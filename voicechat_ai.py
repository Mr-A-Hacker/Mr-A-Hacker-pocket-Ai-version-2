import os
import re
import sys
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from stt_whisper import STTEngine
from tts_piper import PocketAudio

# 1. Model Configuration
REPO_ID = "Qwen/Qwen/Qwen3-0.6B-GGUF"
FILENAME = "Qwen3-0.6B-Q8_0.gguf"
LOCAL_DIR = "./models"
MODEL_PATH = os.path.join(LOCAL_DIR, FILENAME)

# 2. Auto-Download Logic
if not os.path.exists(MODEL_PATH):
    print(f"Model not found at {MODEL_PATH}. Downloading from Hugging Face...")
    os.makedirs(LOCAL_DIR, exist_ok=True)
    MODEL_PATH = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=LOCAL_DIR
    )
    print("Download complete!")

# 3. Initialize Model 
print("Loading Qwen3-0.6B into Pi RAM...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=4096,   
    n_threads=4,  
    verbose=False 
)

# 4. Initialize STT and TTS
stt = STTEngine()
stt.load_model()
tts = PocketAudio()

# 5. Initialize Chat History
messages = [
    {"role": "system", "content": "You are a helpful assistant. Keep your responses concise for text-to-speech."}
]

thinking_mode = False 

print("\n--- Qwen3-0.6B Chat Ready ---")
print("Type 'exit' to quit.")
print("Type '/think' to enable thinking mode.")
print("Type '/no_think' to disable thinking mode.")
print("-----------------------------\n")

# 5. Interactive Chat Loop
while True:
    print("\n[Press Enter to start voice recording, or type your message]")
    user_input = input("You: ").strip()
    
    if user_input.lower() in ['exit', 'quit']:
        print("Goodbye!")
        break
        
    if user_input == "":
        # Voice input mode
        print("[Recording... Press Enter again to stop]")
        stt.start_capture()
        input() # Wait for Enter
        user_input = stt.stop_and_transcribe()
        if not user_input:
            print("[System: No voice detected]")
            continue
        print(f"You (Voice): {user_input}")

    if user_input == "/think":
        thinking_mode = True
        print("[System: Thinking mode ENABLED]")
        continue
    elif user_input == "/no_think":
        thinking_mode = False
        print("[System: Thinking mode DISABLED]")
        continue
        
    # Append the mode flag so the model knows how to behave
    mode_flag = " /think" if thinking_mode else " /no_think"
    prompt_with_toggle = user_input + mode_flag
    
    messages.append({"role": "user", "content": prompt_with_toggle})
    
    print("AI:\n", end="", flush=True)
    
    # 6. Dynamic Sampling Parameters
    if thinking_mode:
        current_temp = 0.6
        current_top_p = 0.95
    else:
        current_temp = 0.7
        current_top_p = 0.8
        
    # Generate the response
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=2048,
        temperature=current_temp,
        top_p=current_top_p,
        top_k=20,
        min_p=0.0,
        presence_penalty=1.5,
        stream=True
    )
    
    full_reply = ""
    for chunk in response:
        delta = chunk['choices'][0]['delta']
        if 'content' in delta:
            text = delta['content']
            print(text, end="", flush=True)
            full_reply += text
            
    messages.append({"role": "assistant", "content": full_reply})
    
    # 7. Maintain history limit (last 10 messages + system prompt)
    if len(messages) > 11:
        messages = [messages[0]] + messages[-10:]
    
    print("\n")
    
    # Voice output - filter out <think> tags and everything in between
    clean_reply = re.sub(r'<think>.*?</think>', '', full_reply, flags=re.DOTALL).strip()
    
    if clean_reply:
        tts.speak(clean_reply)