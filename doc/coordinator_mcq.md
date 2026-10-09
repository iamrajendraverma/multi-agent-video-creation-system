# Coordinator Code - 10 MCQ Questions

---

## Question 1
**What is the primary role of the Coordinator in the video creation system?**

A) Generate video content directly  
B) Orchestrate 6 AI agents through a structured pipeline using LangGraph state machine  
C) Store all video files in the database  
D) Manage user authentication  

**Answer: B**  
**Explanation:** The Coordinator uses LangGraph to manage workflow order, routing, and state persistence across the 6 agents (research, script, visual, video, review, publish).

---

## Question 2
**After the review agent rejects a video, which agent is called next?**

A) Always returns to research agent  
B) Determined by `route_after_review()` based on blocking issues in `FIX_ORDER`  
C) Always goes directly to publish  
D) Terminates the pipeline (END)  

**Answer: B**  
**Explanation:** The `route_after_review()` function checks for blocking issues and returns to the earliest agent in `FIX_ORDER` = ["script", "visual", "video"] that needs to be fixed.

---

## Question 3
**What is the maximum number of times the review agent can reject and request fixes?**

A) Unlimited (infinite retries)  
B) 1 (only one chance)  
C) 3 (checked via `config.VIDEO_MAX_ITERATIONS`)  
D) 5 (hardcoded limit)  

**Answer: C**  
**Explanation:** The code has `if state.iteration >= config.VIDEO_MAX_ITERATIONS:` which prevents infinite loops. After reaching max iterations, the pipeline returns to END.

---

## Question 4
**Which of the following is saved to disk after EVERY agent runs?**

A) Only the video file  
B) Complete VideoState to `/run_dir/state.json` + specific artifacts  
C) Only error logs  
D) Nothing (state kept in memory)  

**Answer: B**  
**Explanation:** The `save_state(working)` function saves full state to `/run_dir/state.json` after each agent. Additionally, specific artifacts like research.json, script.json, etc. are saved via `_save_artifact()`.

---

## Question 5
**The `--resume` flag works by:**

A) Re-running all stages from the beginning  
B) Loading state.json, clearing errors, and skipping completed stages  
C) Re-downloading all artifacts  
D) Restarting only the last failed agent  

**Answer: B**  
**Explanation:** In `run_pipeline()`, when `resume_dir` is provided:
```python
state = load_state(Path(resume_dir))
state.errors = []  # Clear old errors
```
The `route_start()` checks what's missing and starts from there.

---

## Question 6
**What happens if the research agent encounters an exception?**

A) The pipeline crashes immediately  
B) Error is caught, appended to `state.errors`, state is saved, and routing sends to END  
C) The error is silently ignored and pipeline continues  
D) Auto-retries 3 times  

**Answer: B**  
**Explanation:** The `_node()` function has try/except:
```python
except Exception as error:
    working.errors.append(f"{name}: {type(error).__name__}: {error}")
```
Then `route_next()` checks `if state.errors: return END`.

---

## Question 7
**In the pipeline, if the visual agent rejects its output and needs to be re-run, which stages must ALSO be re-run automatically (due to FIX_ORDER)?**

A) Only visual  
B) Visual and video  
C) Visual, video, and publish  
D) All stages from research onwards  

**Answer: B**  
**Explanation:** `FIX_ORDER = ["script", "visual", "video"]`. If visual needs fixing, the route returns "visual", but after visual completes, the next stage (video) must also re-run to ensure consistency.

---

## Question 8
**What is the purpose of the `NEXT_STAGE` dictionary?**

A) Stores agent error messages  
B) Maps each agent to the next sequential agent in the pipeline  
C) Saves video metadata  
D) Controls user permissions  

**Answer: B**  
**Explanation:**
```python
NEXT_STAGE = {
    "research": "script",
    "script": "visual",
    "visual": "video",
    "video": "review",
}
```
Used by `route_next()` to determine the next agent.

---

## Question 9
**Which file contains the execution timeline and logs of all agent runs?**

A) state.json  
B) review_v1.json  
C) run.log  
D) youtube.json  

**Answer: C**  
**Explanation:** The `setup_logging()` function creates a file handler:
```python
file_handler = logging.FileHandler(run_dir / "run.log", encoding="utf-8")
```
This log contains timestamps, log levels, and messages from all agents.

---

## Question 10
**What does the `route_start()` function determine?**

A) Which agent rejected the video  
B) The first agent to run based on what's missing or incomplete  
C) Whether to publish to YouTube  
D) The error severity level  

**Answer: B**  
**Explanation:** `route_start()` checks sequentially:
- If research is None → return "research"
- If script is None → return "script"
- If video missing → return "video"
- ... etc.

This enables `--resume` to skip already completed stages.

---

## Answer Key Summary

| Q | Answer | Key Concept |
|---|--------|------------|
| 1 | B | Coordinator role = LangGraph orchestration |
| 2 | B | route_after_review uses FIX_ORDER |
| 3 | C | Max iterations = config.VIDEO_MAX_ITERATIONS |
| 4 | B | State saved to JSON after every agent |
| 5 | B | Resume loads state.json, skips completed stages |
| 6 | B | Errors caught, appended, then route to END |
| 7 | B | FIX_ORDER cascade: visual → video |
| 8 | B | NEXT_STAGE maps agent sequences |
| 9 | C | run.log stores execution timeline |
| 10 | B | route_start finds first incomplete stage |

---

## Study Tips

**Common Pitfalls in These Questions:**

1. **Q2 Trap:** Students think "always go back to research" but it's based on FIX_ORDER
2. **Q3 Trap:** Thinking iterations are unlimited (they're not—max 3)
3. **Q5 Trap:** Resume re-runs all stages (it skips completed ones)
4. **Q7 Trap:** Only visual is re-run (but video cascades too per FIX_ORDER)
5. **Q6 Trap:** Errors crash the system (they don't—they're collected)

---

## Harder Variants (Bonus)

### Bonus Q1
**If the script agent completes successfully but the visual agent needs to re-run, what happens to the script?**

A) Script is re-run as well  
B) Script remains unchanged; only visual re-runs  
C) Script is deleted and regenerated  
D) Visual goes directly to video  

**Answer: B** - Script is upstream; only downstream agents re-run

### Bonus Q2
**How many artifacts are saved after the script agent completes?**

A) 1 (only script.json)  
B) 2 (script.json + run.log)  
C) 3 (script.json + state.json + run.log)  
D) 5 (all previous + current artifacts)  

**Answer: A** - Only agent-specific artifact + state.json is saved via save_state() separately

---

**Good Luck! 🎯**
