import os
import re
import time
import asyncio
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from stt_whisper import STTEngine
from stt_vosk import STTEngine as VoskEngine
from tts_piper import PocketAudio

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model Configuration ---
REPO_ID = "Qwen/Qwen3-0.6B-GGUF"
FILENAME = "Qwen3-0.6B-Q8_0.gguf"
LOCAL_DIR = "./models"
MODEL_PATH = os.path.join(LOCAL_DIR, FILENAME)

# --- Singleton Engines ---
class AIState:
    def __init__(self):
        self.llm = None
        self.stt = STTEngine()
        self.vosk = VoskEngine()
        self.tts = PocketAudio()
        self.messages = [
            {"role": "system", "content": "You are a helpful assistant. Keep your responses concise for text-to-speech."}
        ]
        self.is_recording = False
        self.is_vosk_recording = False

    def load_models(self):
        if not os.path.exists(MODEL_PATH):
            print("Downloading model...")
            os.makedirs(LOCAL_DIR, exist_ok=True)
            hf_hub_download(repo_id=REPO_ID, filename=FILENAME, local_dir=LOCAL_DIR)
        
        print("Loading LLM...")
        self.llm = Llama(model_path=MODEL_PATH, n_ctx=4096, n_threads=4, verbose=False)
        print("Loading STT (Whisper)...")
        self.stt.load_model()
        print("Loading STT (Vosk)...")
        self.vosk.load_model()
        print("AI Ready.")

ai = AIState()

@app.on_event("startup")
async def startup_event():
    ai.load_models()

# --- Endpoints ---

@app.get("/system/stats")
async def get_stats():
    return {
        "time": time.strftime("%H:%M:%S"),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "temperature": 0 # Placeholder if no sensor access
    }

def clean_for_tts(text: str) -> str:
    # Filter out <think> tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Remove emojis and special symbols
    text = re.sub(r'[^\w\s\?\!\.\,\'\"\-]', '', text)
    return text.strip()

async def process_chat(websocket: WebSocket, user_text: str):
    ai.messages.append({"role": "user", "content": user_text + " /no_think"})
    
    await websocket.send_json({"type": "voice_status", "status": "thinking"})
    await websocket.send_json({"type": "stream_start"})
    
    full_reply = ""
    # Run LLM in thread to avoid blocking event loop
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: ai.llm.create_chat_completion(
        messages=ai.messages,
        max_tokens=512,
        temperature=0.7,
        stream=True
    ))

    for chunk in response:
        delta = chunk['choices'][0]['delta']
        if 'content' in delta:
            content = delta['content']
            full_reply += content
            await websocket.send_json({"type": "stream_delta", "text": full_reply})
    
    await websocket.send_json({"type": "stream_final", "text": full_reply})
    ai.messages.append({"role": "assistant", "content": full_reply})
    
    # Maintain history limit (last 10 messages + system prompt)
    if len(ai.messages) > 11:
        ai.messages = [ai.messages[0]] + ai.messages[-10:]
    
    # Speak the response
    clean_text = clean_for_tts(full_reply)
    if clean_text:
        await websocket.send_json({"type": "voice_status", "status": "speaking"})
        await loop.run_in_executor(None, ai.tts.speak, clean_text)
    
    await websocket.send_json({"type": "voice_status", "status": "idle"})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Send history on connect
    history = [{"role": m["role"], "text": m["content"]} for m in ai.messages if m["role"] != "system"]
    await websocket.send_json({"type": "history", "messages": history})
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "send":
                user_text = data.get("message", "")
                if user_text:
                    await process_chat(websocket, user_text)
            
            elif msg_type == "toggle_voice":
                if not ai.is_recording:
                    print("Starting Voice Capture...")
                    ai.stt.start_capture()
                    ai.is_recording = True
                    await websocket.send_json({"type": "voice_status", "status": "listening"})
                else:
                    print("Stopping Voice Capture...")
                    ai.is_recording = False
                    await websocket.send_json({"type": "voice_status", "status": "processing"})
                    transcription = ai.stt.stop_and_transcribe()
                    if transcription:
                        await websocket.send_json({"type": "voice_transcription", "text": transcription})
                        # Automatically process chat
                        await process_chat(websocket, transcription)
                    else:
                        await websocket.send_json({"type": "voice_status", "status": "idle"})
            
            elif msg_type == "vosk_start":
                if not ai.is_vosk_recording and not ai.is_recording:
                    print("Starting Vosk Capture...")
                    ai.is_vosk_recording = True
                    
                    loop = asyncio.get_running_loop()
                    def vosk_callback(text):
                        asyncio.run_coroutine_threadsafe(
                            websocket.send_json({"type": "vosk_partial", "text": text}),
                            loop
                        )
                    
                    ai.vosk.start_listening(callback=vosk_callback)
                    await websocket.send_json({"type": "voice_status", "status": "listening"})

            elif msg_type == "vosk_stop":
                if ai.is_vosk_recording:
                    print("Stopping Vosk Capture...")
                    ai.is_vosk_recording = False
                    await websocket.send_json({"type": "voice_status", "status": "processing"})
                    transcription = ai.vosk.stop_listening()
                    if transcription:
                        await websocket.send_json({"type": "voice_transcription", "text": transcription})
                        await process_chat(websocket, transcription)
                    else:
                        await websocket.send_json({"type": "voice_status", "status": "idle"})

            elif msg_type == "reset":
                ai.messages = [ai.messages[0]] # Keep system prompt
                await websocket.send_json({"type": "session_reset"})
                
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
