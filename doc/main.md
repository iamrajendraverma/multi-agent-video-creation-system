# Multi-Agent Video Creation System - Complete Guide

## 📌 Project Overview

This is an **automated video creation system** that takes a simple text prompt from a user and automatically creates, reviews, and publishes an animated video to YouTube.

**In simple terms:** You type "Create a video about climate change" → The system makes a complete video and uploads it to YouTube automatically.

---

## 🎯 What Problem Does It Solve?

Creating videos manually takes a lot of time:
1. Write a script
2. Create storyboard/visuals
3. Generate audio/video
4. Review and edit
5. Upload to YouTube

This system **automates all these steps** using AI agents.

---

## 🏗️ System Architecture

```
User Input (Text Prompt)
       ↓
┌─────────────────────────────────────┐
│     COORDINATOR (LangGraph)         │  - Orchestrates the workflow
│     State Machine & Router          │  - Handles iteration loops
└─────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│              PIPELINE STAGES (Sequential)                   │
├─────────────────────────────────────────────────────────────┤
│ 1️⃣  RESEARCH AGENT    → Gathers facts & context             │
│ 2️⃣  SCRIPT AGENT      → Writes video script                 │
│ 3️⃣  VISUAL AGENT      → Creates storyboard (scene details)  │
│ 4️⃣  VIDEO AGENT       → Renders scenes & generates audio    │
│ 5️⃣  REVIEW AGENT      → AI reviews video quality            │
│ 6️⃣  PUBLISH AGENT     → Uploads to YouTube                  │
└─────────────────────────────────────────────────────────────┘
       ↓
   Final Output
   - Video file (MP4)
   - YouTube URL
   - Metadata (title, description, tags)
```

---

## 🤖 What Each Agent Does (Simple Explanation)

### 1️⃣ **RESEARCH AGENT** (`agents/research_agent.py`)
**Job:** Understand what the user is asking about

**How it works:**
- Takes the user's prompt
- Can search the web for real information (if enabled)
- Collects facts, statistics, and context
- Outputs: A research document with key points

**Example:**
- Input: "Create a video about renewable energy"
- Output: Key facts about solar, wind, hydro power + statistics

---

### 2️⃣ **SCRIPT AGENT** (`agents/script_agent.py`)
**Job:** Write the actual video script (voiceover text)

**How it works:**
- Uses research from previous step
- Writes engaging narration for a 30-60 second video
- Breaks script into scenes with timing
- Makes sure it flows naturally
- Outputs: A structured script with scene timings

**Example:**
```
Scene 1 (0-5 sec):
  "Welcome! Did you know that solar energy..."
  
Scene 2 (5-15 sec):
  "In just 5 years, renewables have grown by..."
```

---

### 3️⃣ **VISUAL AGENT** (`agents/visual_agent.py`)
**Job:** Create a visual plan (storyboard)

**How it works:**
- Takes the script
- Imagines what each scene should look like
- Describes visual elements (characters, backgrounds, animations)
- Specifies duration for each scene
- Outputs: Scene-by-scene visual descriptions

**Example:**
```
Scene 1: Green landscape with solar panels
         Animation: Sun rays coming down
         Duration: 5 seconds
         
Scene 2: Wind turbines spinning
         Animation: Rotation effect
         Duration: 10 seconds
```

---

### 4️⃣ **VIDEO AGENT** (`agents/video_agent.py`)
**Job:** Create the actual video file

**How it works:**
- Renders all the scenes (images + animations)
- Generates voiceover audio from the script
- Combines everything into a single video
- Adds music and effects
- Outputs: Final video file (MP4)

**Technologies used:**
- Scene Rendering: Custom image generation
- Voice: Google Cloud Text-to-Speech (or macOS `say` for local testing)
- Video Editing: FFmpeg
- Music: Royalty-free library

---

### 5️⃣ **REVIEW AGENT** (`agents/review_agent.py`)
**Job:** Quality check - Is this video good enough?

**How it works:**
- Watches the generated video
- Checks:
  - ✅ Is it 30-60 seconds long?
  - ✅ Is audio/video synchronized?
  - ✅ Does it match the script?
  - ✅ Is visual quality good?
- Gives score out of 10
- If score < threshold: Sends feedback to fix issues
- Outputs: Approval/rejection + feedback

**Feedback Loop:**
- If rejected, feedback goes back to Script/Visual/Video agent
- They fix issues and try again (up to 3 iterations)
- If still rejected after 3 tries: Flags for human review

---

### 6️⃣ **PUBLISH AGENT** (`agents/publisher_agent.py`)
**Job:** Upload the approved video to YouTube

**How it works:**
- Takes the approved video
- Creates YouTube metadata (title, description, tags)
- Uploads to user's YouTube channel
- Sets privacy level (private/unlisted/public)
- Outputs: YouTube URL + confirmation

---

## 📊 Data Flow & State Management

The system uses **LangGraph** for state management:

```python
VideoState = {
  user_prompt: str          # Original request from user
  research: ResearchResult  # Facts & context
  script: Script            # Video script
  storyboard: Storyboard    # Visual plan
  video_path: str           # Path to generated video
  review: Review            # Quality check results
  youtube_url: str          # Published video URL
  errors: List[str]         # Any errors that occurred
  iteration: int            # How many review loops we've done
}
```

**Key feature:** After every step, the entire state is saved to `state.json`
- Allows resuming interrupted runs
- Useful for debugging

---

## 🔧 Technologies Used

### Core Framework
- **LangGraph**: State machine for workflow orchestration
- **Pydantic**: Data validation & structured outputs
- **Anthropic Claude**: AI for all agent logic

### Video Generation
- **FFmpeg**: Video encoding & combining scenes
- **Google Cloud Text-to-Speech**: Voice generation
- **Custom Scene Renderer**: Image generation from descriptions

### Authentication & APIs
- **Claude Code SDK**: For Claude authentication
- **Anthropic SDK**: For Claude API calls (if using API key)
- **Google Cloud APIs**: For TTS and YouTube
- **YouTube Data API**: For publishing videos

### Configuration
- **.env file**: Environment variables for API keys, settings
- **config.py**: Centralized configuration management

---

## 🚀 How to Run It

### Setup (One-time)
```bash
# Install dependencies
pip install -r requirements.txt

# Authenticate with Claude
claude login

# (Optional) Set up Google Cloud for TTS and YouTube
export GOOGLE_APPLICATION_CREDENTIALS=./gcp-service-account.json
```

### Create a Video

**Option 1: With YouTube Upload**
```bash
python main.py --prompt "Create a video about AI"
```

**Option 2: Without YouTube Upload (Just test video creation)**
```bash
python main.py --prompt "Create a video about AI" --no-publish
```

**Option 3: Auto-approve and upload (skip confirmation)**
```bash
python main.py --prompt "Create a video about AI" --yes
```

**Option 4: Resume a previous run (if it failed)**
```bash
python main.py --resume output/20261004-154158-hi --no-publish
```

### Output
Results are saved in `output/<timestamp>-<topic>/` folder:
```
output/20261004-154158-hi/
├── state.json              # Complete pipeline state
├── run.log                 # Execution logs
├── research.json           # Research output
├── script.json             # Video script
├── storyboard.json         # Visual plan
├── output.mp4              # Final video file
├── youtube.json            # YouTube metadata
└── review_v*.json          # Review results
```

---

## 📋 Project File Structure

```
multi-agent-video-creation-system/
├── main.py                 # Entry point - Run this to start
├── config.py               # Configuration & settings
├── coordinator/            # Main orchestrator
│   └── coordinator.py      # LangGraph workflow definition
├── agents/                 # Individual agents
│   ├── research_agent.py
│   ├── script_agent.py
│   ├── visual_agent.py
│   ├── video_agent.py
│   ├── review_agent.py
│   └── publisher_agent.py
├── models/                 # Data structures (Pydantic)
│   └── state.py           # VideoState definition
├── services/               # Utilities & external services
│   ├── llm.py             # Claude API communication
│   ├── video_generator.py # FFmpeg video creation
│   ├── scene_renderer.py  # Image rendering
│   ├── voice_generator.py # TTS voice creation
│   ├── youtube.py         # YouTube upload
│   └── media_probe.py     # Video file analysis
├── prompts/               # AI instruction templates
│   └── *.txt files        # System prompts for each agent
├── tests/                 # Unit tests
├── output/                # Generated videos & logs
├── assets/                # Music & fonts
├── .env                   # Configuration (API keys, settings)
└── README.md              # Initial project plan
```

---

## 🔄 Pipeline Flow with Error Handling

```
START
  ↓
Check if research exists → If not, run Research Agent
  ↓
Check if script exists → If not, run Script Agent
  ↓
Check if storyboard exists → If not, run Visual Agent
  ↓
Check if video exists → If not, run Video Agent
  ↓
Run Review Agent
  ↓
Is video approved? ─NO→ Any errors?
  │                      ├─ YES → END with error
  │                      └─ NO → Iteration < 3?
  │                             ├─ YES → Fix & go back to Script/Visual/Video
  │                             └─ NO → Flag for human review
  ↓ YES
Run Publish Agent (if publish=true, else skip)
  ↓
END with YouTube URL
```

---

## ⚙️ Key Configuration Options

From `.env`:

```
# Authentication
CLAUDE_AUTH=login              # Use "login" or "api_key"
CLAUDE_MODEL=claude-haiku-4-5-20251001

# Video settings
VIDEO_MIN_SECONDS=30
VIDEO_MAX_SECONDS=60
VIDEO_MAX_ITERATIONS=3         # Max review loops before human review

# Voice
VOICE_PROVIDER=google          # "google" or "macos"
GOOGLE_TTS_VOICE=en-US-Neural2-D

# YouTube
YOUTUBE_PRIVACY=private        # "private", "unlisted", or "public"

# Research
RESEARCH_WEB_SEARCH=true       # Enable web search during research
```

---

## 🎓 Interview Tips - Key Concepts to Explain

### 1. **How is this different from manual video creation?**
- Manual: Days to create one video
- This system: Minutes (fully automated)
- Scalable: Can create 100+ videos with no human effort

### 2. **Why use multiple agents instead of one big AI?**
- Separation of concerns: Each agent is specialized
- Easy to debug: Know which stage failed
- Easy to improve: Update one agent without affecting others
- Reusable: Agents can be used in other systems

### 3. **Why use LangGraph?**
- State management: Keeps track of data between steps
- Resumable: Can continue from where it stopped
- Routing: Can loop back (review → fix → review)
- Observable: Can track what's happening

### 4. **What about AI failures/bad outputs?**
- Review agent catches quality issues
- Feedback loop: Automatically retries up to 3 times
- Human fallback: If AI can't fix it, humans review
- Error logging: Every error is logged for analysis

### 5. **Scalability considerations:**
- **Per-user quotas:** API usage limits (can reset monthly)
- **Concurrent runs:** Currently sequential, could parallelize research
- **Cost:** Depends on Claude API usage per video
- **Video quality:** Trade-off between rendering quality and generation time

---

## 🐛 Troubleshooting Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "API usage limits reached" | Quota exceeded | Wait for reset or use new account |
| "Claude login not found" | Not authenticated | Run `claude login` |
| "YouTube upload failed" | Missing credentials | Set up Google OAuth tokens |
| "Video is too short/long" | Script doesn't fit | Adjust VIDEO_MIN/MAX_SECONDS |
| "Poor audio quality" | TTS settings | Change GOOGLE_TTS_VOICE in .env |

---

## 📚 Important Files to Know

- **main.py**: How users interact with the system
- **coordinator/coordinator.py**: How workflow is orchestrated
- **config.py**: All settings and configuration
- **models/state.py**: Data structures passed between agents
- **services/llm.py**: How Claude is called (authentication, structured outputs)
- **prompts/**: System instructions for each agent

---

## 💡 Example Interview Questions You Might Face

1. **"How does the system handle if the AI generates a bad script?"**
   - Review agent detects it
   - Sends feedback to script agent
   - Script agent tries again with feedback
   - Repeats up to 3 times

2. **"What happens if an agent fails?"**
   - Error is caught and logged
   - Pipeline stops
   - User can resume with `--resume` after fixing the issue
   - Full state is saved, so no progress is lost

3. **"How is the system scalable?"**
   - Agents are independent: Easy to add new ones
   - State machine design: Can handle complex workflows
   - Resumable: Can handle long-running tasks
   - Future: Could parallelize some stages

4. **"Why use Pydantic for data models?"**
   - Type safety: Catch data errors early
   - Validation: Ensures data from AI is correct
   - Structured outputs: Claude returns valid JSON
   - Documentation: Models serve as API documentation

5. **"How do you ensure YouTube upload is successful?"**
   - YouTube API handles authentication
   - Metadata is structured and validated
   - Errors are caught and logged
   - User gets confirmation with video URL

---

## 🎬 Sample Run Output

When you run the system, you'll see:

```
Run folder: /Users/.../output/20261004-154158-hi
Request: Create a video about renewable energy

▶ research agent        ← Gathering facts
  research agent finished in 2.5 s

▶ script agent          ← Writing script
  script agent finished in 3.2 s

▶ visual agent          ← Creating storyboard
  visual agent finished in 2.8 s

▶ video agent           ← Rendering video
  video agent finished in 15.3 s

▶ review agent          ← Checking quality
  review agent finished in 4.1 s

Review:        approved (score 8.5/10)

▶ publish agent         ← Uploading to YouTube
  publish agent finished in 3.4 s

========== RESULT ==========
Output folder: /Users/.../output/20261004-154158-hi
Video:         /Users/.../output/20261004-154158-hi/output.mp4
Iterations:    1
Review:        approved (score 8.5/10)
Title:         Renewable Energy Revolution
YouTube:       https://youtu.be/abc123def456
```

---

## 🚀 What's Next / Potential Improvements

1. **Parallel execution:** Run research + script agent in parallel
2. **Custom scenes:** Let users upload custom images/videos
3. **Multiple voices:** Dialogue between characters
4. **Real-time streaming:** Upload as video is being created
5. **Analytics:** Track performance metrics for each agent
6. **A/B testing:** Generate multiple versions and pick the best

---

## 📞 Getting Help

- Check `output/<run_id>/run.log` for detailed error messages
- Look at `state.json` to see what data each agent had
- Review saved artifacts (script.json, storyboard.json) to understand outputs
- Use `--resume` to retry after fixing issues

---

**Good luck with your interview! 🎉**
