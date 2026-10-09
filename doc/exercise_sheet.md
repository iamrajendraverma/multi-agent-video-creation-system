# Exercise Sheet: Understanding the Multi-Agent Video Creation System

Two hands-on exercises to learn how the project works, from the outside in.

**Before you start**

```bash
source .venv/bin/activate          # project virtualenv
pip install -r requirements.txt    # if the venv is missing packages
claude login                       # Claude auth (CLAUDE_AUTH=login is the default)
```

Reference files you will use:

| File | What it tells you |
|---|---|
| `main.py` | CLI flags and the exit path |
| `coordinator/coordinator.py` | The LangGraph state machine and routing rules |
| `models/state.py` | Every data shape that flows between agents |
| `config.py` | All settings and their defaults |
| `doc/introduction.md` | The pipeline as a diagram |

---

## Exercise 1: Follow One Video Run Through the Pipeline

**Goal:** Learn what each agent produces, and where it is saved, by running the pipeline once and reading the output.

### Background

The pipeline has five creation stages, then publish:

```
research → script → visual → video → review → (approved?) → publish
```

Each stage saves its result into a new run folder, `output/<timestamp>-<slug>/`. After every stage the full state is written to `state.json`, so a run can be resumed.

### Steps

1. **Run the pipeline without uploading to YouTube.**

   ```bash
   python main.py --prompt "Five facts about honey bees" --no-publish
   ```

   Wait for the `========== RESULT ==========` block at the end. Note the output folder it prints.

2. **List the run folder.** Replace `<RUN_DIR>` with the folder from step 1.

   ```bash
   ls -la output/<RUN_DIR>
   ```

3. **Match each file to the agent that created it.** Fill in the table below. Use `coordinator/coordinator.py` (`_save_artifact`) to check your answers.

   | File | Created by agent | What it contains |
   |---|---|---|
   | `research.json` | | |
   | `script.json` | | |
   | `storyboard.json` | | |
   | `review_v1.json` | | |
   | `output.mp4` | | |
   | `state.json` | | |
   | `run.log` | | |

4. **Read the script.** Open `script.json`. Count the `body` items and check how `Script.full_text` (in `models/state.py`) joins the hook, body and ending. Explain in one sentence why the narration is read as one text.

5. **Read the storyboard.** Open `storyboard.json`. Answer:
   - Which `layout` values appear in the scenes?
   - Which fields are empty for a `title` scene, and why? (Hint: the `Scene` model says "empty when the layout doesn't use it".)

6. **Read the review.** Open `review_v1.json`. Answer:
   - Was the video `approved`? What is the `score`?
   - Look at each `issues[].target_agent`. Which stage would the coordinator re-run next if the review had rejected the video?

7. **Read the log.** Open `run.log`. Find the lines that start with `▶` (in the console) or the agent names. Write down the order of the agents and how long each one took.

### Checkpoint

You can answer these without looking at the code again:

- What is the difference between `state.json` and `review_v1.json`?
- Which file would you open first if the final video looked wrong, and why?

---

## Exercise 2: Trace the Review Loop and Resume a Failed Run

**Goal:** Understand how a rejected video sends work back to an earlier agent, then use `--resume` to continue a run without repeating finished work.

### Background

After review, `route_after_review` in `coordinator/coordinator.py` decides what happens next:

1. If the video was approved, go to `publish`.
2. If `iteration` has reached `VIDEO_MAX_ITERATIONS` (default `3`), stop and ask for a human.
3. Otherwise, look at the **blocking** issues (`major` or `critical`). If there are none, use all issues. Take the targets, and pick the **earliest** one in `FIX_ORDER = ["script", "visual", "video"]`.

Because of `FIX_ORDER`, a script problem also re-runs visual and video.

### Part A: Predict the routing (no code run)

For each case below, write the stage the graph goes to next. Use only `route_after_review` and `FIX_ORDER`. Check your answers afterwards in `tests/test_coordinator.py` (`test_route_after_review`).

| # | Review result | `iteration` | Expected next stage |
|---|---|---|---|
| a | approved | 1 | |
| b | rejected, one `major` issue targeting `visual` | 1 | |
| c | rejected, `major` on `video` and `minor` on `script` | 1 | |
| d | rejected, only a `minor` issue targeting `script` | 1 | |
| e | rejected, `major` on `visual` | 3 | |

Hints: for case (c), the `minor` issue is ignored because a blocking issue exists. For case (e), the limit is reached, so the run ends.

### Part B: Run the tests

```bash
pytest tests/ -v
```

1. Record how many tests passed and how many failed.
2. Open `tests/test_coordinator.py` and find `test_route_start_skips_finished_stages`. Explain in your own words what `route_start` checks, in order.
3. Compare your answers from Part A with the assertions in `test_route_after_review`. Did any prediction differ? If so, re-read the function and find out why.

### Part C: Resume a run

Simulate a failure, then recover from it.

1. Start a run with no YouTube upload:

   ```bash
   python main.py --prompt "Why the sky is blue" --no-publish
   ```

2. Stop it partway through (press `Ctrl+C` after the `visual` stage starts). Note the run folder path.

3. Check what was saved so far:

   ```bash
   cat output/<RUN_DIR>/state.json | python -m json.tool | grep -E '"(research|script|storyboard|video_path)"'
   ```

4. Resume the run:

   ```bash
   python main.py --resume output/<RUN_DIR> --no-publish
   ```

5. Watch the console. Confirm that `research` and `script` are **not** run again. Explain which function decides this (`route_start`).

### Checkpoint

- Why does `route_after_review` pick the *earliest* stage in `FIX_ORDER` and not the stage with the most issues?
- What is stored in `state.json` that lets `--resume` know which stages are finished?
- Where does `run_pipeline` reset errors before resuming, and why does that matter? (Hint: `state.errors = []`.)

---

## Answer Key (check after you try)

**Exercise 1, step 3:** `research.json` (research agent), `script.json` (script agent), `storyboard.json` (visual agent), `review_v1.json` (review agent), `output.mp4` (video agent), `state.json` (saved by every node), `run.log` (logging for the whole run).

**Exercise 2, Part A:**

| # | Expected next stage | Reason |
|---|---|---|
| a | `publish` | Approved |
| b | `visual` | Only blocking issue targets visual |
| c | `video` | Blocking issue targets video; the minor script issue is ignored |
| d | `script` | No blocking issues, so all issues are used; the earliest target is script |
| e | `END` | `iteration >= VIDEO_MAX_ITERATIONS`; the run needs human review |

Case (e) ends at `END`, not at a stage, because the routing function returns `END` before it looks at the issues.
