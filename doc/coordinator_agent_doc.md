## 1. Multi-Agent Video System: Coordinator Code Breakdown

#### 🎯 Overview

The Coordinator is a **LangGraph state machine** that orchestrates 6 AI agents through a structured video creation pipeline.
- It manages workflow,
- state persistence,
- error handling,
- conditional routing.

#### 📊 Pipeline Flow

```
START
↓
research → script → visual → video → review ⟵⟶ (rejected, max 3 iterations)
↓
publish
↓
END
```

#### Key Points:

- Linear progression through stages
- Review can reject and route back to earlier stages for fixes
- Any agent error stops the entire run
- Full state saved after each step for resumability

#### 🤖 The 6 Agents

Agent	Task

| Agent | Task |
|-------|------|
| Research | Gathers facts from web search |
| Script | Writes video narrative/voiceover |
| Visual | Plans storyboard & scene layout |
| Video | Renders the animated video |
| Review | Quality check (approve/reject) |
| Publish | Uploads to YouTube |

#### 🔄 Core Components

**1. State Management** 

- All data stored in VideoState model (Pydantic)
- State file: `/run_dir/state.json`
- After each agent: state saved to disk
- Allows `--resume` to restart from failure point  python

####  Save state after every step

```python 
save_state(working)  # Writes to state.json
```

#### Load state for resume
```python
state = load_state(resume_dir)
```
**2. Routing Logic**

**Route Start** - Determines first agent based on `what's missing:`

```python 
if research is None → start at research
elif script is None → skip research, start at script
elif video missing → skip to video stage
else if approved → go to publish
else → review feedback routing
```

**Route After Review** - Decides next stage based on issues:

```python 

If approved → publish
If iteration < 3 → fix the blocking issue
 Else → END (human review needed)
```
**Fix Order (for re-runs)** :

```python 
["script", "visual", "video"]
```

- Fixes script = must re-run visual + video
- Fixes visual = must re-run video
- Ensures downstream consistency

**3.Artifact Storage**

After each agent runs, specific outputs saved:

| File | Description |
|------|-------------|
| research.json | Research findings |
| script.json | Generated script |
| storyboard.json | Visual plan |
| review_v1.json | First review |
| review_v2.json | Second review (if retry) |
| youtube.json | YouTube metadata |
| run.log | Execution timeline |


**3. ⚙️ Node Structure** 

Each agent runs as a node with:

```python
def _node(name):
    def run(state):
        # 1. Call agent function
        # 2. Catch errors (append to state.errors)
        # 3. Save state to JSON
        # 4. Save artifacts (research.json, script.json, etc)
        # 5. Return updated state fields
    return run
```
#### Error Handling:

- Catches exceptions, logs them
- Appends error string to `state.errors`
- Continues to save partial state
- Routing sends to END if errors detected

#### 📝 State Machine Edges

```text
START ──→ route_start() ──→ {research, script, visual, video, review, END}

research ──route_next──→ script (or END if error)
script ──route_next──→ visual (or END if error)
visual ──route_next──→ video (or END if error)
video ──route_next──→ review (or END if error)

review ──route_after_review──→ {script, visual, video, publish, END}
  ├─ Approved? → publish
  ├─ Max iterations? → END
  ├─ Has issues? → route to blocking agent
  └─ Else → retry script

publish ──→ END
```

**4. 🚀 Resume Capability**

Key Feature: Resumable runs via `--resume /path/to/run`

```python
if resume_dir:
    state = load_state(Path(resume_dir))  # Load from state.json
    state.errors = []  # Clear old errors
    state.publish = publish  # Override publish setting
    state.auto_confirm = auto_confirm
    state.privacy = privacy
```

- Skips completed stages (research, script, etc.)
- Re-runs failed stage + any downstream changes
- No duplicate work

**5. 📋 Logging Setup**

- Console: Rich formatting for readability
- File: /run_dir/run.log with timestamps
- Level: INFO (third-party libs set to WARNING to reduce noise)

```python
2024-10-06 10:30:45,123 INFO coordinator: Run folder: output/...
2024-10-06 10:30:46,456 INFO coordinator: ▶ research agent
2024-10-06 10:30:52,789 INFO coordinator: research agent finished in 6.3 s
```
**6. 🎛️ Entry Point: run_pipeline()**

```python
run_pipeline(
    user_prompt="Create a video about AI",
    publish=True,           # Upload to YouTube?
    auto_confirm=False,     # Ask before uploading?
    privacy="private",      # private, unlisted, public
    resume_dir=None         # Or: "output/20261006-154158-..."
)
```
**Flow:**

1. Load or create state
2. Setup logging
3. Create graph
4. Invoke app (runs agents in order)
5. Return final VideoState

**7.💡 Key Design Patterns** 

| Pattern                 | Purpose |
|-------------------------|---------|
| **State Machine**       | Enforce workflow order |
| **Conditional Routing** | Adapt based on outputs |
| **Artifact Saving**     | Inspection & debugging |
| **State Checkpointing** | Enable resume |
| **Error Collection**    | Don't crash, accumulate errors |
| **Iteration Limits**    | Prevent infinite loops |

**8.🔍 Example Flow (Happy Path)**

```text
1. START
2. route_start() → research (nothing done yet)
3. research_agent runs, finds facts, returns state
4. save_state() → state.json, research.json
5. route_next("research") → script (no errors)
6. script_agent runs, writes script
7. save_state() → state.json, script.json
8. ... (visual, video follow same pattern)
9. review_agent checks video quality
10. if approved: route_after_review() → publish
11. publish_agent uploads to YouTube
12. return final state with youtube_url
```

**9.⚠️ Example Flow (Rejection)**

```text

1-8. (same as above)
9. review_agent finds issues in script quality
10. state.approved = False, state.review.issues = [...]
11. route_after_review() checks blocking issues
12. Finds target_agent = "script" → return "script"
13. Increment state.iteration = 1
14. script_agent re-runs with feedback
15. visual_agent re-runs (fix_order cascade)
16. video_agent re-runs
17. review_agent runs again
18. If still not approved & iteration < 3: repeat
19. Else: return END (needs human review)
```
**10. 📌 Summary**

**Coordinator = Orchestrator**

1. Manages 6 agents in a state machine
2. Routes based on workflow logic
3. Saves state for resilience
4. Handles errors gracefully
5. Enables resume from failure
6. Limits iteration to prevent loops
7. Logs everything for debugging


