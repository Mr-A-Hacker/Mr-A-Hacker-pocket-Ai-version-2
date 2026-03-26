# 🧠 Viora AI

> **A fully offline, voice-powered personal AI assistant for Raspberry Pi and Linux.**
> Talk to it, show it things, ask it to remember tasks, check the weather, open maps — all without internet.

Viora AI is a complete AI assistant that runs **entirely on your device**. No cloud, no subscriptions, no data leaving your machine. It combines speech recognition, a local LLM, text-to-speech, camera vision, scheduled tasks, weather, offline maps, and a powerful Dev AI coding assistant — all in one modern touch-friendly interface.

---

## ✨ Features

### 💬 Chat
Converse naturally with **Viora AI** using voice or text. Powered by **Qwen 0.6B GGUF**, a fast local language model that runs entirely offline. Responses are streamed in real-time and read aloud by **Piper TTS**. Supports markdown, code blocks, and multi-turn conversations with full history.

### 🎤 Voice Input
Two speech-to-text engines available:
- **Whisper Tiny** — fast, accurate, internet-required for first download
- **Vosk** — fully offline, lightweight, perfect for privacy

Just tap the mic, speak, and Viora responds in her own voice. Supports real-time partial transcription so you can see what you're saying as you speak.

### 🗣 Voice Output
**Piper TTS** reads responses aloud with natural, low-latency synthesis. Viora sounds like a real voice assistant — not a robot.

### 👁 Vision (Camera)
Connect a USB webcam or Raspberry Pi camera and Viora can see. Captures photos, streams live video, and supports **Hailo object detection** — identify objects in real-time. Great for home automation, security, or learning projects.

### 📷 Gallery
All captured photos are saved locally and organized in a gallery view. Tap any photo to view it full-screen, delete it, or send it to the chat for analysis.

### ✅ Agent (Task Scheduler)
Schedule tasks to run automatically at specific times or intervals. Tell Viora *"Remind me to water the plants every day at 9 AM"* and it stays in the background running those jobs — no internet needed.

### 🌦 Weather
Check current weather conditions. Powered by **Open-Meteo** (free, no API key needed). Shows temperature, conditions, humidity, and wind. Works with internet. Displays a friendly "Please connect to the internet" message when offline.

### 🗺️ Maps
Opens **Organic Maps** — a beautiful, fully offline map app. No Google, no internet required. Perfect for hiking, cycling, or any situation where you need navigation without a data connection.

### 🤖 Dev AI (OpenCode)
A built-in coding assistant powered by **OpenCode**. Ask Viora to write code, debug scripts, explain concepts, or refactor existing code. Works completely offline — your code never leaves your machine. Supports Python, JavaScript, Bash, and more.

### ⚙️ Settings
Configure voice input/output, enable/disable features, manage conversation history, and customize your experience.

---

## 📋 What You Need

### Hardware
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Device | Raspberry Pi 4 / any Linux PC | Raspberry Pi 5 |
| RAM | 4 GB | 8 GB |
| Storage | 8 GB SD card/SSD | 32 GB+ SSD |
| Camera | USB webcam (optional) | Raspberry Pi Camera Module 3 |
| Audio | USB mic or 3.5mm jack | ReSpeaker USB Mic |

### Software
| Dependency | Version | Install |
|------------|---------|---------|
| Python | 3.10+ | `sudo apt install python3 python3-venv` |
| Node.js | 18+ | `curl -fsSL https://deb.nodesource.com/setup_18.x | sudo bash -` |
| Git | any | `sudo apt install git` |
| PortAudio | system | `sudo apt install portaudio19-dev` |
| CMake | build tool | `sudo apt install cmake` |

### API Keys (Optional)
- **Hugging Face** — for downloading LLM models (free account needed, huggingface.co)
- **OpenCode** — install separately at opencode.ai for Dev AI

---

## 🚀 Quick Start

### 1. Clone the Repository

git clone https://github.com/Mr-A-Hacker/Mr-A-Hacker-pocket-Ai-version-2
cd Mr-A-Hacker-pocket-Ai-version-2


### 2. Set Up Python Environment

python3 -m venv .venv
source .venv/bin/activate


### 3. Install Backend Dependencies

pip install -r requirements.txt

**System dependencies** (Debian/Ubuntu):

sudo apt-get update
sudo apt-get install -y portaudio19-dev cmake libopenblas-dev liblapack-dev


### 4. Install Frontend Dependencies

cd chat-gui
npm install
cd ..


### 5. Download AI Models

Viora needs several AI models. They download automatically on first run, or you can get them manually:

**LLM — Qwen 0.6B GGUF**
mkdir -p models
# Download from Hugging Face (auto-downloaded on first run)
# Repo: Qwen/Qwen3-0.6B-GGUF
# File: Qwen3-0.6B-Q8_0.gguf

**Tool LLM — Function Gemma**
# Repo: nlouis/functiongemma-pocket-q4_k_m
# File: functiongemma-pocket-q4_k_m.gguf

**Whisper (auto-downloaded)**
# faster-whisper downloads this automatically on first use

**Vosk Model (fully offline STT)**
mkdir -p models/vosk
cd models/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

**Piper TTS**
mkdir -p models/piper
# Download from:
# https://github.com/rhasspy/piper/releases/download/2024.11.14-2/en_US-lessac-medium.onnx
# Place at: models/piper/en_US-lessac-medium.onnx


### 6. Configure Environment

Create a `.env` file:

cp .env.example .env
nano .env

Recommended settings:

# Ports
PORT=8000

# Model paths
LOCAL_DIR=./models

# Speech-to-Text
USE_WHISPER=true
USE_VOSK=true
VOSK_MODEL=models/vosk/vosk-model-small-en-us-0.15

# Text-to-Speech
PIPER_MODEL=en_US-lessac-medium.onnx

# Camera
CAMERA_DEVICE=0

# LLM
MAX_TOKENS=2048
TEMPERATURE=0.7

# Feature toggles
ENABLE_CAMERA=true
ENABLE_TTS=true
ENABLE_STT=true
ENABLE_LLM=true


### 7. Install OpenCode (for Dev AI)

curl -fsSL https://opencode.ai/install.sh | sh


### 8. Run the App

**Option A — One command (backend + frontend):**

./start-viora-ai.sh

**Option B — Manual:**

# Terminal 1: Start backend
source .venv/bin/activate
python app.py

# Terminal 2: Start frontend
cd chat-gui
npm run dev

Then open **http://localhost:5173** in your browser, or run as an Electron app:

cd chat-gui
npm run build
# The built app will be in chat-gui/out/


---

## 🗂️ Project Structure

Viora-AI/
├── app.py                  # FastAPI backend — all HTTP & WebSocket endpoints
├── chat_ai.py              # Core AI pipeline: STT → LLM → TTS
├── stt_whisper.py          # Whisper speech recognition engine
├── stt_vosk.py             # Vosk offline speech recognition
├── tts_piper.py            # Piper text-to-speech engine
├── semantic_router_ai.py    # Routes prompts to the right model
├── tool_ai.py              # Function-calling LLM for tools
├── task_scheduler.py        # Background job scheduler (APScheduler)
├── weather.py              # Open-Meteo weather API endpoint
├── maps.py                 # Maps & Organic Maps launcher
├── devai.py                # OpenCode Dev AI endpoint
├── camera_stream.py         # MJPEG camera stream & capture
├── config.py               # All configuration in one place
├── tools.json              # Tool definitions for function calling
├── requirements.txt        # Python dependencies
│
├── chat-gui/               # Electron + React frontend
│   ├── src/
│   │   ├── App.jsx        # Main app with router
│   │   ├── index.css      # Global styles (Viora theme)
│   │   ├── config.js      # API URLs
│   │   └── components/
│   │       ├── Home.jsx       # Main menu with all feature buttons
│   │       ├── ChatInterface   # Chat with Viora AI
│   │       ├── CameraView      # Live camera + object detection
│   │       ├── Gallery        # Photo gallery
│   │       ├── TaskManager    # Scheduled tasks
│   │       ├── Settings       # App configuration
│   │       ├── Maps           # Organic Maps launcher
│   │       ├── DevAI          # OpenCode coding assistant
│   │       ├── Weather        # Weather display
│   │       ├── Avatar.jsx     # Animated Viora avatar
│   │       └── StatusBar.jsx  # CPU/RAM/Temperature bar
│   └── package.json
│
├── models/                 # AI models (download separately)
│   ├── qwen/              # Qwen LLM GGUF file
│   ├── piper/             # Piper TTS voice file
│   └── vosk/             # Vosk STT model folder
│
├── captures/               # Camera photos saved here
│
├── conversations.json      # Chat history
├── task_jobs.json         # Scheduled task data
│
├── start-viora-ai.sh      # One-click launcher script
├── VioraAI.desktop        # Desktop shortcut file
└── README.md


---

## 🎛 How the App Works

### Architecture Overview

┌─────────────────────────────────────────────────────┐
│                   ELECTRON / BROWSER                 │
│              React Frontend (Viora UI)               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐  │
│  │  CHAT   │ │ CAMERA  │ │ GALLERY │ │  AGENT   │  │
│  │ VISION  │ │  MAPS   │ │ WEATHER │ │  DEV AI  │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬─────┘  │
└───────┼──────────┼──────────┼──────────┼──────────┘
        │          │          │          │
        │   HTTP / WebSocket  │          │
        ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────┐
│               FASTAPI BACKEND (Python)               │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐       │
│  │ /ws/chat │  │ /ws/voice│  │ /camera/*   │       │
│  └────┬─────┘  └────┬─────┘  └──────┬──────┘       │
│       │             │               │               │
│  ┌────▼─────────────────────────────▼─────┐        │
│  │            chat_ai.py (Core)            │        │
│  │  STT → Semantic Router → LLM → TTS     │        │
│  └────┬─────────────────────────────┬──────┘        │
│       │                             │               │
│  ┌────▼────┐  ┌──────▼──────┐  ┌───▼──────┐       │
│  │ Whisper │  │ Qwen 0.6B   │  │  Piper   │       │
│  │  / Vosk │  │   GGUF      │  │   TTS    │       │
│  └─────────┘  └─────────────┘  └──────────┘       │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ OpenCode     │  │ Open-Meteo   │                │
│  │ (Dev AI)     │  │ (Weather)    │                │
│  └──────────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────┘

### Chat Flow
1. User types or speaks a message
2. If voice → **Whisper** or **Vosk** converts speech to text
3. Text is sent via **WebSocket** to the backend
4. **Semantic Router** decides: basic chat, thinking mode, or tool use
5. **Qwen LLM** generates a response
6. Response is streamed to the frontend in real-time
7. **Piper TTS** reads the response aloud
8. Conversation is saved to `conversations.json`

### Voice Flow
1. User holds the mic button (or taps)
2. **Whisper/Vosk** captures and transcribes in real-time
3. Transcription appears as you speak
4. On release, text is sent to the LLM
5. Response streams back + TTS plays simultaneously


---

## 📱 The Viora Interface

The home screen features a **modern, clean UI** with a glowing animated avatar. Six main buttons lead to all features:

| Button     | Color   | Feature                    |
|------------|---------|----------------------------|
| 💬 CHAT    | Purple  | Talk to Viora AI           |
| 📷 VISION  | Cyan    | Camera + object detection   |
| 📝 AGENT   | Pink    | Scheduled tasks             |
| 🖼 GALLERY | Gray    | Photo gallery              |
| 🗺️ MAPS    | Green   | Organic Maps launcher       |
| 🤖 DEV AI  | Orange  | OpenCode coding assistant   |

Plus quick-access to **Weather** and **Settings** from the header.


---

## 🛠 Troubleshooting

### "Missing X server or $DISPLAY"
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority


### Vosk model not found
Make sure `VOSK_MODEL` in `.env` points to the extracted folder:
VOSK_MODEL=models/vosk/vosk-model-small-en-us-0.15


### Whisper download failing
Manually download:
huggingface-cli download NVIDIA/StableDiffusion-quality
# Or use the auto-downloader on first run


### Camera not working
# List available cameras
ls /dev/video*

# Test with ffmpeg
ffmpeg -i /dev/video0 -frames 1 test.jpg


### Backend won't start
# Check port is free
lsof -i :8000

# Kill existing processes
pkill -f "python app.py"


### OpenCode not launching
# Verify installation
opencode --version

# Check path in devai.py matches your install location
cat devai.py | grep OPENCODE_PATH


### TTS not playing audio
# Check your audio output
speaker-test -c 2

# Set correct output
# For HDMI: sudo raspi-config → Advanced → Audio
# For headphone jack: amixer cset numid=3 1


---

## 🔧 Customization

### Change the Voice
Replace the Piper model in `models/piper/` with any voice from piper-voice-models. Update `.env`:
PIPER_MODEL=your_voice.onnx


### Use a Different LLM
Change in `config.py`:
CHAT_REPO_ID = "your/model-name"
CHAT_FILENAME = "your-model-q8_0.gguf"
GGUF models from TheBloke on Hugging Face work out of the box.


### Add New Tools
Edit `tools.json` to define new functions that Viora can call. The Function Gemma model will automatically learn to use them.


### Customize the UI
All styles are in `chat-gui/src/index.css`. The theme uses CSS variables — change them once and the whole app updates:
:root {
  --ai-color: #7c3aed;      /* Primary purple */
  --bg: #faf8ff;             /* Background */
  --surface: #fff;           /* Card background */
  --border: #ede9f8;        /* Borders */
  --text: #1e1030;           /* Text color */
  --text-mid: #6b5b8e;      /* Secondary text */
}


---

## 🌐 Offline Capabilities

| Feature                  | Online | Offline         |
|--------------------------|--------|-----------------|
| Chat with Viora          | ✅     | ✅              |
| Voice input (Whisper)    | ✅     | ⚠️ First run   |
| Voice input (Vosk)       | ✅     | ✅              |
| Voice output (TTS)       | ✅     | ✅              |
| Camera + capture         | ✅     | ✅              |
| Object detection         | ✅     | ✅              |
| Scheduled tasks          | ✅     | ✅              |
| Gallery                  | ✅     | ✅              |
| Organic Maps             | ✅     | ✅              |
| Weather                  | ✅     | ❌              |
| Dev AI (OpenCode)        | ✅     | ✅              |


---

## 🧪 Testing

# Run backend tests
source .venv/bin/activate
pytest tests/

# Test a specific component
python test_pocket_ai.py


---

## 📜 License

MIT License — free to use, modify, and distribute.


---

## 🙏 Credits

Built by **Mr-A-Hacker**. Engineered for Raspberry Pi and offline AI experimentation.

Powered by:
- Qwen by Alibaba
- Whisper by OpenAI
- Vosk by AlphaCEP
- Piper by Rhasspy
- Function Gemma by nlouis
- Organic Maps by Organic Maps
- OpenCode by OpenCode
- Open-Meteo by Open-Meteo
