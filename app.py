import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
import sys
import uuid
import time
from typing import Dict, List, Optional
from pydantic import BaseModel

# Import OpenClawClient from the existing file
try:
    from openclaw_client import OpenClawClient, load_openclaw_config, DEFAULT_SESSION_KEY
except ImportError:
    print("Error: Could not import openclaw_client. Make sure it is in the same directory.")
    sys.exit(1)

# Import Computer Vision module
try:
    import computer_vision
except ImportError:
    print("Error: Could not import computer_vision. Make sure it is in the same directory.")
    # We won't exit here, just warn, in case CV is optional or on dev machine without hailo
    computer_vision = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi_bridge")

# ─── Load Global Configuration ───────────────────────────────────────────────

OC_CONFIG, OC_URL, OC_TOKEN = load_openclaw_config()
OC_URL = OC_URL or "ws://127.0.0.1:18789"

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Connection Management ────────────────────────────────────────────────────

class OpenClawBridge:
    """Manages a single WebSocket bridge between a client and OpenClaw."""
    
    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.client: Optional[OpenClawClient] = None
        self.active = True
        self.oc_connected = False

    async def safe_send(self, data: dict):
        """Sends data through the frontend WebSocket safely."""
        if not self.active:
            return
        try:
            await self.websocket.send_json(data)
        except (WebSocketDisconnect, RuntimeError) as e:
            logger.warning(f"[{self.connection_id}] Frontend send failed: {e}")
            self.active = False
        except Exception as e:
            logger.error(f"[{self.connection_id}] Unexpected frontend send error: {e}")

    def on_chat_event(self, payload: dict):
        """Handles incoming 'chat' events from OpenClaw."""
        if not self.active or not self.client:
            return

        # Filter by session key and run ID
        if payload.get("sessionKey") != self.client.session_key:
            return
        
        run_id = payload.get("runId")
        if run_id and self.client._current_run_id and run_id != self.client._current_run_id:
            return

        state = payload.get("state")
        
        # Helper to send message in a separate task to avoid blocking the receiver
        def queue_msg(msg_data):
            if self.active:
                asyncio.create_task(self.safe_send(msg_data))

        if state == "delta":
            content = payload.get("message", {}).get("content", [])
            text = next((block.get("text", "") for block in content if block.get("type") == "text"), "")
            queue_msg({"type": "stream_delta", "text": text})

        elif state == "final":
            content = payload.get("message", {}).get("content", [])
            text = next((block.get("text", "") for block in content if block.get("type") == "text"), "")
            queue_msg({"type": "stream_final", "text": text})

        elif state == "aborted":
            queue_msg({"type": "stream_aborted"})

        elif state == "error":
            error_msg = payload.get("errorMessage", "unknown error")
            queue_msg({"type": "stream_error", "error": error_msg})

    async def connect_openclaw(self):
        """Initializes and connects the OpenClaw client."""
        try:
            self.client = OpenClawClient(url=OC_URL, token=OC_TOKEN, session_key=DEFAULT_SESSION_KEY)
            await self.client.connect()
            self.client.on_event("chat", self.on_chat_event)
            self.oc_connected = True
            logger.info(f"[{self.connection_id}] Connected to OpenClaw")
            return True
        except Exception as e:
            logger.error(f"[{self.connection_id}] OpenClaw connection failed: {e}")
            self.oc_connected = False
            return False

    async def send_history(self):
        """Fetches and sends chat history to the frontend."""
        if not self.oc_connected:
            return

        try:
            history = await self.client.chat_history()
            hist_messages = []
            for msg in history.get("messages", []):
                role = msg.get("role", "")
                content = msg.get("content", [])
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        text_parts.append(block)
                
                text = "\n".join(text_parts).strip()
                if text and role in ("user", "assistant"):
                    hist_messages.append({"role": role, "text": text})

            await self.safe_send({"type": "history", "messages": hist_messages})
        except Exception as e:
            logger.error(f"[{self.connection_id}] Error sending history: {e}")

    async def run(self):
        """Main loop for handling frontend messages."""
        try:
            # 1. Connect to OpenClaw
            if await self.connect_openclaw():
                # 2. Send history immediately
                await self.send_history()

            # 3. Handle messages
            while self.active:
                try:
                    data = await self.websocket.receive_json()
                except (WebSocketDisconnect, RuntimeError):
                    break

                msg_type = data.get("type")

                # Reconnect OpenClaw if it dropped
                if not self.oc_connected:
                    if await self.connect_openclaw():
                        logger.info(f"[{self.connection_id}] Reconnected to OpenClaw")

                if msg_type == "send":
                    message = data.get("message", "").strip()
                    logger.info(f"[{self.connection_id}] Received send request")
                    if message and self.oc_connected:
                        await self.safe_send({"type": "stream_start"})
                        try:
                            await self.client.chat_send(message)
                        except Exception as e:
                            logger.error(f"[{self.connection_id}] chat_send error: {e}")
                            await self.safe_send({"type": "stream_error", "error": str(e)})

                elif msg_type == "abort":
                    if self.oc_connected and self.client and self.client._current_run_id:
                        await self.client.chat_abort(self.client._current_run_id)

                elif msg_type == "reset":
                    if self.oc_connected:
                        try:
                            await self.client.session_reset()
                            await self.safe_send({"type": "session_reset"})
                        except Exception as e:
                            await self.safe_send({"type": "stream_error", "error": str(e)})

        except Exception as e:
            logger.error(f"[{self.connection_id}] Bridge loop error: {e}")
        finally:
            self.active = False
            if self.client:
                logger.info(f"[{self.connection_id}] Disconnecting OpenClaw client")
                await self.client.disconnect()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = str(uuid.uuid4())[:8]
    logger.info(f"[{connection_id}] New connection request")
    
    await websocket.accept()
    logger.info(f"[{connection_id}] Connection accepted")

    bridge = OpenClawBridge(websocket, connection_id)
    await bridge.run()

# ─── Computer Vision Endpoints ────────────────────────────────────────────────

def generate_frames():
    """Generator for MJPEG stream."""
    if computer_vision is None:
        return
        
    while True:
        frame, _ = computer_vision.get_latest_frame()
        if frame is not None:
             # Encode to JPEG
             # Ensure frame is valid (it should be if get_latest_frame returned cleanly)
             try:
                 # Convert RGB to BGR for OpenCV encoding if needed, 
                 # BUT computer_vision.py says it forces RGB. 
                 # OpenCV expects BGR. So we convert RGB -> BGR.
                 frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                 ret, buffer = cv2.imencode('.jpg', frame_bgr)
                 if ret:
                     yield (b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
             except Exception as e:
                 logger.error(f"Error encoding frame: {e}")
        
        # Cap at ~30 FPS to save CPU
        time.sleep(0.033)

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

class CVControl(BaseModel):
    action: str # "start", "stop"
    mode: str = "raw" # "raw", "detection", "pose"

@app.post("/cv/control")
def cv_control(data: CVControl):
    if computer_vision is None:
        return {"status": "error", "message": "Computer vision module not loaded"}

    logger.info(f"CV Control: {data.action} {data.mode}")

    if data.action == "stop":
         computer_vision.stop_task()
         return {"status": "stopped"}
         
    elif data.action == "start":
         # Stop any running task first
         computer_vision.stop_task()
         
         target = None
         if data.mode == "raw":
             target = computer_vision.run_raw_camera_app
         elif data.mode == "detection":
             target = computer_vision.run_detection_app
         elif data.mode == "pose":
             target = computer_vision.run_pose_app
             
         if target:
             computer_vision.start_task(target)
             return {"status": "started", "mode": data.mode}
         else:
             return {"status": "error", "message": "Invalid mode"}
             
    return {"status": "ignored"}


@app.on_event("shutdown")
def shutdown_event():
    """Release camera and GStreamer resources on server shutdown."""
    if computer_vision is not None:
        logger.info("Shutting down computer vision...")
        computer_vision.stop_task()
        logger.info("Computer vision stopped.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
