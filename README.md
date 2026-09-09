# UGC Video Generator — Chat App

A minimal, production-quality ChatGPT-style web application that turns product websites and URLs into short-form, vertical (9:16) UGC-style social media videos.

The system uses **AI-directed deterministic video assembly** (not slow, hallucinating generative video models). Groq AI acts as the Creative Director—analyzing the product, selecting the ideal marketing angle, and picking curated assets—while FFmpeg deterministically renders the final 4-layer MP4 video, which is stored directly inside PostgreSQL as binary data (`BYTEA`) and returned directly in the chat thread.

---

## Architecture Flow

```text
User Message / URL
       ↓
Next.js Chat UI (TypeScript + Tailwind CSS)
       ↓  POST /api/v1/chat
FastAPI Backend
       ↓
Deterministic Intent & URL Detection
       ├── [Normal Chat: "hi", "what can you do?"] ──→ Conversational Response
       └── [Product / Video Request]
               ↓
       Background Video Pipeline
               ↓
       1. Product Extraction (Jina Reader → httpx + BeautifulSoup fallback)
               ↓
       2. Product Understanding (Groq AI JSON → heuristic fallback)
               ↓
       3. Asset Selection (Deterministic Tag Filtering → Groq Selection → Fallback Plan)
               ↓
       4. FFmpeg Video Assembly (1080x1920 9:16 Video, Bold Hook Text, Reaction GIF, Music)
               ↓
       5. PostgreSQL Binary Storage (BYTEA via PostgresVideoStorage)
               ↓
       6. Temporary Disk Files Cleaned Up Immediately
               ↓
Chat UI Polls GET /api/v1/videos/{video_id}
       ↓ (extracting → planning → rendering → completed)
Playable 9:16 Video Player in Chat (GET /api/v1/videos/{video_id}/file)
```

---

## Tech Stack

- **Frontend**: Next.js (App Router), React, TypeScript, Tailwind CSS, Lucide Icons
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL (Neon/Local), Pydantic v2
- **Video Assembly**: FFmpeg (`libx264`, `aac`, 9:16 1080x1920, 30fps) & Pillow
- **AI Creative Director**: Groq API (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`)
- **Product Extraction**: Jina Reader (`https://r.jina.ai/{url}`) with fallback to `httpx` + `BeautifulSoup`
- **Storage**: Direct PostgreSQL `BYTEA` binary persistence (no cloud S3/R2/Blob dependencies)
- **Containerization**: Docker & Docker Compose

---

## Video Specifications (4 Layers)

Every assembled video is strictly formatted for short-form social video (TikTok, Reels, Shorts):
- **Aspect Ratio**: Vertical 9:16 (1080x1920)
- **Duration**: 7 seconds (configurable 5–10s)
- **Format**: MP4 (`libx264` video, `aac` audio, `yuv420p` pixel format for universal mobile/browser compatibility)
- **Layer 1 — Background**: Thematic motion video scaled and center-cropped to 1080x1920.
- **Layer 2 — Reaction GIF**: Emotion-driven looping GIF overlay (scaled to ~0.55 and positioned prominently).
- **Layer 3 — Bold Text Overlay**: Punchy social media hook text with drop-shadow and translucent backdrop pill.
- **Layer 4 — Royalty-Free Audio**: High-tempo upbeat background audio track trimmed and volume-balanced.

---

## Curated Asset Library

The repository includes a curated offline asset library covering 10+ product categories (Food, Fitness, Productivity, Finance, Technology, AI, Beauty, Shopping, Lifestyle):
- **13 Backgrounds**: `food_01.mp4`, `fitness_01.mp4`, `productivity_01.mp4`, `tech_01.mp4`, etc.
- **15 Reaction GIFs**: `gif_excited_01.gif`, `gif_celebration_01.gif`, `gif_mindblown_01.gif`, `gif_shocked_01.gif`, etc.
- **5 Audio Tracks**: `energy_01.mp3`, `chill_01.mp3`, `tech_01.mp3`, `quirky_01.mp3`, etc.

Assets are indexed with stable IDs and tags in the PostgreSQL `assets` table.

---

## Local Development Setup

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+** and `npm`
- **FFmpeg** (`brew install ffmpeg` on macOS, `apt-get install ffmpeg` on Linux)
- **PostgreSQL** database (Local or Neon/Supabase)

### 2. Clone & Setup Environment

```bash
git clone <repo-url>
cd ugc-generator-8x

# Copy environment variables
cp .env.example .env
```

Edit `.env` and fill in your database and API credentials:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/ugc_generator
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
JINA_API_KEY=your_jina_api_key_optional
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> **Note on Groq API**: If `GROQ_API_KEY` is not provided or fails, the application automatically uses deterministic creative fallbacks (for food, fitness, productivity, finance, tech, etc.). It never crashes.

### 3. Backend Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Seed curated assets and initialize database tables
cd backend
python seed_assets.py

# Start FastAPI backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend API will be live at `http://localhost:8000` (Docs: `http://localhost:8000/docs`).

### 4. Frontend Setup

In a new terminal window:
```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## Running with Docker Compose

To run the complete stack (PostgreSQL, FastAPI with FFmpeg, and Next.js) in containers:

```bash
docker compose up --build
```

- Web Chat UI: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

## Running Automated Tests

A comprehensive test suite covers URL extraction, intent detection, product extraction fallbacks, candidate asset filtering, creative planning, video state transitions, and FFmpeg command generation:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run test suite from backend directory
cd backend
pytest tests/ -v
```

---

## Example Requests & Usage

### 1. The Core Demo Acceptance Test
Send this prompt in the chat:
```text
I'm building CalAI, a calorie-tracking app. Here's the site: calai.app
```

The system will:
1. Detect `https://calai.app` and identify video request intent.
2. Reply: *"Got it — I'll create a short UGC-style video for CalAI."*
3. Extract CalAI's website via Jina Reader.
4. Groq understands: Calorie tracking app for fitness & nutrition.
5. Filter candidate assets (food backgrounds, excited/mindblown reaction GIFs, upbeat audio).
6. Plan creative: Hook *"POV: you finally know what you're eating"*.
7. FFmpeg renders 7-second 1080x1920 MP4 with background, bold text, looping reaction GIF, and music.
8. Store MP4 bytes in PostgreSQL `BYTEA` and delete temporary files.
9. Display the video player directly inside the chat thread.

### 2. Conversational Chat
Send normal conversational queries:
- `"hi"` → Greets normally without generating a video.
- `"what can you do?"` → Explains its UGC video generation capabilities.
- `"Tell me about this website https://example.com"` → Treated conversationally unless video generation is requested.

---

## Project Structure

```text
ugc-generator-8x/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app & lifespan
│   │   ├── core/
│   │   │   ├── config.py            # Settings & env loading
│   │   │   └── database.py          # SQLAlchemy engine & session
│   │   ├── models/                  # Conversation, Message, Product, Asset, Video
│   │   ├── schemas/                 # Pydantic v2 validation models
│   │   ├── services/
│   │   │   ├── chat_service.py      # Conversation management & routing
│   │   │   ├── product_extractor.py # Jina Reader + BeautifulSoup fallback
│   │   │   ├── groq_service.py      # Groq AI creative director
│   │   │   ├── asset_service.py     # Deterministic candidate asset filtering
│   │   │   ├── creative_service.py  # Creative plan orchestrator & category fallbacks
│   │   │   ├── ffmpeg_service.py    # 4-layer 9:16 FFmpeg video renderer
│   │   │   ├── video_storage.py     # PostgresVideoStorage (BYTEA adapter)
│   │   │   └── video_service.py     # Pipeline background orchestration
│   │   ├── utils/                   # URL extraction & file helpers
│   │   └── api/routes/              # Health, Chat, Videos, Products
│   ├── assets/                      # Curated 9:16 MP4s, reaction GIFs, MP3 audio
│   ├── tests/                       # Pytest automated test suite
│   ├── seed_assets.py               # Local asset synthesizer & DB seed
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js App Router (layout, page, globals.css)
│   │   ├── components/              # ChatInterface, MessageItem, VideoPlayer, ChatInput
│   │   ├── lib/api.ts               # Backend API client
│   │   └── types/chat.ts            # TypeScript interfaces
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Known Limitations & MVP Scope

- **Video Storage**: In strict accordance with the assignment requirements, video files are stored directly in PostgreSQL `BYTEA` columns. For high-scale production systems beyond an MVP, an object storage service (S3/R2/GCS) with a CDN would be used.
- **Background Jobs**: Uses async background tasks and polling for simplicity rather than Celery/Redis.
