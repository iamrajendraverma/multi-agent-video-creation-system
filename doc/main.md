## System Overview 


```
                    USER PROMPT
                         │
                         ▼
               ┌──────────────────┐
               │ COORDINATOR AGENT │
               │  Orchestrator     │
               └────────┬─────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
 ┌────────────┐  ┌────────────┐  ┌──────────────┐
 │ Research   │  │ Script     │  │ Visual/Asset  │
 │ Agent      │  │ Agent      │  │ Agent         │
 └─────┬──────┘  └─────┬──────┘  └──────┬───────┘
       │               │                  │
       └───────────────┼──────────────────┘
                       ▼
                ┌──────────────┐
                │ Video Agent  │
                │ Animation    │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │ Review Agent │
                │ QA + Fixes   │
                └──────┬───────┘
                       │
                 approved?
                  /        \
                NO          YES
                │            │
                └───fix──────┘
                             ▼
                    YouTube Publisher
```

For Python, I would use Claude + LangGraph + Pydantic + FFmpeg/MoviePy + YouTube Data API.

## 1. Define the responsibilities

I would make your five sub-agents:

| Agent          | Responsibility                        | Output           |
| -------------- | ------------------------------------- | ---------------- |
| Research Agent | Research topic/facts                  | `ResearchResult` |
| Script Agent   | Convert research into narration/story | `Script`         |
| Visual Agent   | Decide scenes, images, animations     | `Storyboard`     |
| Video Agent    | Generate actual video                 | `VideoArtifact`  |
| Review Agent   | Check factual/content/video quality   | `ReviewResult`   |






This agent converts the script into a **structured storyboard**.


```
{
  "scenes": [
    {
      "scene": 1,
      "duration": 5,
      "narration": "India's job market is changing...",
      "visual": "Animated India map with employment icons",
      "animation": "Zoom into major cities"
    },
    {
      "scene": 2,
      "duration": 7,
      "narration": "...",
      "visual": "Office workers and AI robots",
      "animation": "Icons moving toward AI"
    }
  ]
}
```

## Review Agent 

This is extremely important 

Don't make 

```
Generate → Publish
```
Make : 

```
Generate
   ↓
Review
   ↓
Approved?
 ┌─┴─┐
No  Yes
│    │
Fix  Publish
│
└──→ Generate
```
