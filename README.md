# MULTI-AGENT VIDEO CREATION SYSTEM – PROJECT PLAN

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
