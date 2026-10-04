# MULTI-AGENT VIDEO CREATION SYSTEM

An automated AI system that takes a text prompt and creates, reviews, and publishes an animated video to YouTube.

## 🚀 Quick Start Guide

### Prerequisites
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Authenticate with Claude
claude login

# 3. (Optional) Set up Google Cloud for TTS and YouTube
export GOOGLE_APPLICATION_CREDENTIALS=./gcp-service-account.json
```

## 📖 Working Guide & Commands

### ✅ Option 1: Create Video WITHOUT YouTube Upload (Testing)
**Use this when you just want to test if video creation works**

```bash
python main.py --prompt "Your video topic here" --no-publish
```

**Examples:**
```bash
# Simple topic
python main.py --prompt "A cat and dog playing together" --no-publish

# Detailed topic
python main.py --prompt "Create an educational video about climate change and renewable energy" --no-publish

# Interactive (no prompt flag)
python main.py --no-publish
# Then type your prompt when prompted
```

**Output:**
- ✅ Full video creation pipeline runs (research → script → visual → video → review)
- ✅ YouTube upload is **skipped**
- ✅ Final video saved at `output/<timestamp>/output.mp4`
- ✅ All metadata and logs saved for analysis

---

### 🎥 Option 2: Create Video WITH YouTube Upload
**Use this when you want the final video published to YouTube**

```bash
python main.py --prompt "Your video topic here"
```

**Examples:**
```bash
# Will ask for confirmation before uploading
python main.py --prompt "A guide to healthy eating"

# Auto-confirm upload (no confirmation prompt)
python main.py --prompt "A guide to healthy eating" --yes

# With custom privacy level
python main.py --prompt "A guide to healthy eating" --privacy public
python main.py --prompt "A guide to healthy eating" --privacy unlisted
```

**Privacy Options:**
- `private` (default) - Only you can see it
- `unlisted` - Anyone with link can see it
- `public` - Everyone can find and see it

**Output:**
- ✅ Full video creation pipeline runs (including YouTube upload)
- ✅ Video published to your YouTube channel
- ✅ YouTube URL returned: `https://youtu.be/xxx`

---

### ⏸️ Option 3: Resume Failed Run
**Use this if a run failed halfway and you want to continue**

```bash
python main.py --resume output/20261004-154158-hi --no-publish
```

**Examples:**
```bash
# Resume and skip YouTube upload
python main.py --resume output/20261004-144717-i-want-to-create-a-story-of-two-vegitabl --no-publish

# Resume and upload to YouTube
python main.py --resume output/20261004-144717-i-want-to-create-a-story-of-two-vegitabl --yes

# Resume with different privacy level
python main.py --resume output/20261004-144717-i-want-to-create-a-story-of-two-vegitabl --privacy public
```

**What happens:**
- ✅ Previous progress is loaded from `state.json`
- ✅ Skipped completed stages (research, script, visual, video already done)
- ✅ Only re-runs failed stage or next stage
- ✅ No duplicate work

---

## 🧪 Testing Guide

### Test 1: Quick Test (No API Cost if Web Search Disabled)
```bash
# This is fast and uses minimal API
python main.py --prompt "Hello world" --no-publish
```

Expected output:
- Runs all 5 creation stages
- Takes ~30-60 seconds
- Video saved in `output/` folder

---

### Test 2: Full Pipeline Test (With Web Search)
```bash
# This uses more API quota (web search enabled)
python main.py --prompt "Latest breakthroughs in artificial intelligence" --no-publish
```

Expected output:
- Research agent searches the web
- Script written with current information
- Full video created
- Takes ~2-5 minutes
- Video quality is higher

---

### Test 3: Test YouTube Upload (Publishing)
```bash
# Test complete pipeline including YouTube
python main.py --prompt "My First AI Generated Video" --yes
```

Expected output:
- ✅ All stages complete
- ✅ Video uploaded to YouTube
- ✅ YouTube URL displayed
- ✅ Takes 5-10 minutes total

---

### Test 4: Test with Interactive Prompt
```bash
# No --prompt flag, you'll be asked to type it
python main.py --no-publish
```

When prompted:
```
What video do you want to create?
> Your topic here
```

---

### Test 5: Check Existing Outputs
```bash
# List all previous runs
ls -la output/

# Check latest run details
cat output/20261004-154158-hi/state.json

# Watch run logs
cat output/20261004-154158-hi/run.log

# Check generated script
cat output/20261004-154158-hi/script.json

# Check visual plan
cat output/20261004-154158-hi/storyboard.json

# View final video
open output/20261004-154158-hi/output.mp4  # macOS
# or
vlc output/20261004-154158-hi/output.mp4   # Linux/Windows
```

---

## 📊 Understanding Output Files

After each run, check `output/<timestamp>/`:

```
output/20261004-154158-hi/
├── output.mp4              ← Final video file (MOST IMPORTANT)
├── state.json              ← Complete pipeline state
├── run.log                 ← Execution timeline & logs
├── research.json           ← Research findings
├── script.json             ← Generated script
├── storyboard.json         ← Visual plan
├── review_v1.json          ← Quality review scores
└── youtube.json            ← YouTube metadata (if published)
```

**Key files to inspect:**
- `output.mp4` - Watch this to see the final video
- `run.log` - Check for errors or performance info
- `script.json` - See what text was generated
- `storyboard.json` - See visual descriptions

---

## ⚙️ Configuration Options

Edit `.env` to customize behavior:

```env
# CLAUDE AUTHENTICATION
CLAUDE_AUTH=login                    # Use "login" or "api_key"
CLAUDE_MODEL=claude-haiku-4-5-20251001

# VIDEO SETTINGS
VIDEO_MIN_SECONDS=30                 # Minimum video length
VIDEO_MAX_SECONDS=60                 # Maximum video length
VIDEO_MAX_ITERATIONS=3               # Max review loops before human review
VIDEO_FPS=30                         # Frames per second

# VOICE & AUDIO
VOICE_PROVIDER=google                # "google" or "macos"
GOOGLE_TTS_LANGUAGE=en-US
GOOGLE_TTS_VOICE=en-US-Neural2-D     # Different voices available
GOOGLE_TTS_SPEAKING_RATE=1.05        # Speed (1.0 = normal)

# RESEARCH
RESEARCH_WEB_SEARCH=true             # Enable web search for facts
RESEARCH_MAX_SEARCHES=5              # Max searches per run

# YOUTUBE
YOUTUBE_PRIVACY=private              # private, unlisted, or public
YOUTUBE_CLIENT_SECRET_FILE=client_secret.json
YOUTUBE_TOKEN_FILE=youtube_token.json

# OUTPUT
OUTPUT_DIR=output                    # Where to save videos
```

---

## 🔐 Authentication Methods

### Method 1: Claude Code Login (Recommended)
```bash
# One-time setup
claude login

# Then just run normally
python main.py --prompt "Your topic" --no-publish
```

### Method 2: API Key (For CI/Headless)
```bash
# Set in .env
CLAUDE_AUTH=api_key
ANTHROPIC_API_KEY=sk-ant-v1-xxxxx

# Or set as environment variable
export ANTHROPIC_API_KEY=sk-ant-v1-xxxxx
python main.py --prompt "Your topic" --no-publish
```

### Method 3: Claude Code Token (For CI/Scripts)
```bash
# Get token
claude setup-token

# Set in .env
CLAUDE_CODE_OAUTH_TOKEN=your-token-here

# Then run
python main.py --prompt "Your topic" --no-publish
```

---

## 🐛 Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "API usage limits reached" | Monthly quota exceeded | Wait for reset or use new account |
| "Claude login not found" | Not authenticated | Run `claude login` |
| "YouTube upload failed" | Missing Google OAuth | Set up YouTube credentials |
| "Research failed" | Web search disabled/API issue | Check `RESEARCH_WEB_SEARCH` in .env |
| "Video file not created" | FFmpeg not installed | `brew install ffmpeg` |
| "Audio quality is poor" | TTS voice not ideal | Try different `GOOGLE_TTS_VOICE` |

---

## 📋 Common Workflows

### Workflow 1: Just Test If It Works
```bash
python main.py --prompt "Test topic" --no-publish
# Runs ~1 minute, checks all stages work
```

### Workflow 2: Create Video Portfolio
```bash
# Create multiple videos for testing
python main.py --prompt "Topic 1" --no-publish
python main.py --prompt "Topic 2" --no-publish
python main.py --prompt "Topic 3" --no-publish

# Check which one is best
ls -lh output/*/output.mp4
```

### Workflow 3: Publish Best One
```bash
# Publish the best video
python main.py --resume output/20261004-154158-hi --privacy public --yes
```

### Workflow 4: Debug Failed Run
```bash
# First check what went wrong
cat output/20261004-154158-hi/run.log

# Check the state
cat output/20261004-154158-hi/state.json | grep -A 2 "errors"

# Fix the issue, then resume
python main.py --resume output/20261004-154158-hi --no-publish
```

---

## 📝 All Command-Line Flags

```
--prompt TEXT              What the video should be about
--no-publish              Create video but skip YouTube upload
--yes                     Auto-approve upload (skip confirmation)
--privacy {private,unlisted,public}  YouTube privacy level (default: private)
--resume RUN_DIR          Continue a previous run from its output folder
--help                    Show all options
```

**Complete examples:**

```bash
# Basic: Create video without publishing
python main.py --prompt "Hello world" --no-publish

# With all options
python main.py \
  --prompt "Climate change solutions" \
  --privacy public \
  --yes

# Resume after fixing issues
python main.py \
  --resume output/20261004-154158-hi \
  --privacy unlisted \
  --no-publish
```

---

## 📊 System Architecture (Brief)

```
User Prompt
    ↓
RESEARCH AGENT (Gather facts)
    ↓
SCRIPT AGENT (Write script)
    ↓
VISUAL AGENT (Plan visuals)
    ↓
VIDEO AGENT (Render video)
    ↓
REVIEW AGENT (Check quality) ─→ Loop back if needed
    ↓
PUBLISH AGENT (YouTube upload) ─→ Only if --no-publish not set
    ↓
DONE! Video URL
```

---

## 📚 For More Details

See `doc/main.md` for complete project documentation including:
- How each agent works
- Technologies used
- Interview preparation guide
- Architecture deep-dive

## Authentication

Claude calls use your Claude login. You don't need an API key.

1. Install Claude Code and run `claude login` once.
2. Or, for headless/CI runs, run `claude setup-token` and set `CLAUDE_CODE_OAUTH_TOKEN` in `.env`.

Usage counts against your Claude plan. To use an Anthropic API key instead, set `CLAUDE_AUTH=api_key` and `ANTHROPIC_API_KEY` in `.env`. With `CLAUDE_AUTH=login`, any `ANTHROPIC_API_KEY` in `.env` is ignored.

## Phase 1: SYSTEM OVERVIEW

Objective: Build a multi-agent system that takes a user prompt and automatically produces, reviews, and publishes an animated video to YouTube.

Input: User provides a single prompt/instruction (e.g., "Create a reel about labor market trends in India")

Output: Published video on YouTube channel

Architecture: Coordinator Agent + 5 Sub-Agents

## Phase 2: COORDINATOR AGENT

Role: Central orchestrator that manages the workflow

Responsibilities:

Receives user prompt
Routes tasks to appropriate sub-agents
Monitors sub-agent outputs
Tracks pipeline status
Handles error management

Tech Stack: LangChain / AutoGen or custom agent framework

## Phase 3: SUB-AGENT 1 – SCRIPT WRITER

Role: Converts prompt into a video script

Input: User prompt

Output: Structured video script (intro, body, outro, timing notes)

Tasks:

Understand prompt intent
Generate engaging narrative
Add dialogue/voiceover text
Include scene timing suggestions
Ensure 30-60 second format for reels

Tools: Claude API / GPT

## Phase 4: SUB-AGENT 2 – STORYBOARD PLANNER

Role: Creates visual plan for the video

Input: Script from Agent 1

Output: Scene-by-scene breakdown with visual descriptions

Tasks:

Break script into scenes
Describe visuals for each scene
Define transitions
Suggest animations/effects
Create shot list

Tools: Claude API / vision models

## Phase 5: SUB-AGENT 3 – VIDEO GENERATION

Role: Creates the actual animated video

Input: Script + Storyboard

Output: Raw animated video file

Tasks:

Call external video generation API (Synthesia, Runway, D-ID, etc.)
Pass script and visual specs
Generate video in correct format/duration
Return video file URL/path

Tools: Synthesia API / Runway API / D-ID API

## Phase 6: SUB-AGENT 4 – REVIEW & QA

Role: Checks video quality before publishing

Input: Generated video

Output: Approval/rejection with feedback

Tasks:

Check video length (30-60 seconds)
Verify audio/video sync
Review script accuracy in video
Check visual quality
Suggest edits if needed
Flag issues for human review

Tools: Video analysis / Claude vision

## Phase 7: SUB-AGENT 5 – YOUTUBE PUBLISHER

Role: Uploads and publishes video to YouTube

Input: Approved video file

Output: Published video URL + channel confirmation

Tasks:

Authenticate YouTube account
Upload video file
Add title/description/tags
Set thumbnail
Configure privacy settings
Publish to channel

Tools: YouTube API / pytube / google-auth

## Phase 8: WORKFLOW & DEPENDENCIES
User Prompt
    ↓
Coordinator (routing)
    ↓
Script Writer Agent → Script Output
    ↓
Storyboard Agent → Storyboard Output
    ↓
Video Generation Agent → Video File
    ↓
Review & QA Agent → Approval Decision
    ↓ (if approved)
YouTube Publisher Agent → Published Video
    ↓
Completion & URL to User
## Phase 9: TECHNOLOGY STACK
Component	Tech Options
Coordinator	LangChain, AutoGen, CrewAI
LLMs	Claude, GPT-4, Llama
Video Generation	Synthesia, Runway, D-ID, HeyGen
YouTube Integration	YouTube API v3, google-auth
Language	Python (recommended)
Framework	FastAPI for API endpoints
## Phase 10: IMPLEMENTATION TIMELINE

Phase 1 (Week 1-2): Set up coordinator + Script Writer agent
Phase 2 (Week 3): Build Storyboard agent
Phase 3 (Week 4-5): Integrate video generation API
Phase 4 (Week 6): Build Review agent
Phase 5 (Week 7): YouTube publisher integration
Phase 6 (Week 8): Testing & refinement
