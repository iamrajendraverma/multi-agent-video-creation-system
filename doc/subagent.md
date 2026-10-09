## 1. Re-seach Agent 

```text

User Prompt -> Research agent -> 
Claude AI -> with websearch tool ->
Claude AI -> with out websearch tool ->
  
  Structured Reseach -> 
Script Agent
```
## 2.  Script Agent 


```text
(user_Prompt, research result and revious feedback)->input -> build prompt (Load instruction , rearch, word limits and feedback)
-> Genertae the script(calude return structureed output and matching the script model) -> Save and Log -> update state
```
## 3. Visual Agent 

It creates the storyboard, it means what will look. let's have a look on one storyboard how it looks like. 

```json

{
  "color_theme": "forest",
  "scenes": [
    {
      "index": 1,
      "layout": "title",
      "narration": "Your cat and dog can be best friends—but only if you speak their language.",
      "headline": "Your cat and dog can be best friends",
      "stat_value": "",
      "bullets": [],
      "chart_labels": [],
      "chart_values": [],
      "chart_unit": "",
      "source": ""
    }
  ]
}
```
A storyboard is basically a **blueprint for the video**. These are illustrative scenes, not actaul output from your code. 

let's understand the flow 

```text
1. Calude generates storyboard -> 2. Check storyboard.scenes 
if not present agent raise error 
if present Renumber scenes   -> return to co-ordinator agent

```
## 4. Video Agent 
Vieo agent is the **production manage** of your multi-agent video creation system. 
It takes the storyboard created by the visual agent and turns it into a complete video with visuals,voice narration,background music and a thumbnail.

Let's highlight few more points of Video Agent

```python
for scene in storyboard.scenes:
        scene_images.append(
            render_scene(
                scene,
                storyboard.color_theme,
                len(storyboard.scenes),
                scenes_dir / f"scene_{scene.index:02d}.png",
            )
        )
        audio_paths.append(
            generate_voice(scene.narration, audio_dir / f"scene_{scene.index:02d}")
        )
```
The `render_scene` method is responsbile to create the video frame from the storyboard. 

The method `find_background_music`attached the video 

## Interview-ready explanation 

The **Video Agent** consumes the storyboard produced by the Visual Agent. For each scene, it renders an `image` and generates `voice narration`. It then locates optional `background music`, composes the assets into an MP4, creates a JPEG thumbnail from the first scene, and stores the resulting paths and scene durations in the shared state for downstream processing.

## 5. Review Agent 

It review the created video in following terms. if the video does not pass the video get regenerated. 

**A. Check video duration** 

```python 
if info.duration < config.VIDEO_MIN_SECONDS - DURATION_TOLERANCE:
    # Add a major issue: lengthen the script.

if info.duration > config.VIDEO_MAX_SECONDS + DURATION_TOLERANCE:
    # Add a major issue: shorten the script.
```

It generate the video between 25 sec to 65 sec. Below 25 is `too small` and above `65 is too big`

The duration issue targets the "script" agent because changing the **narration length** is one way to correct the video duration.

**B.Check resolution**

```python
if (info.width, info.height) != (
    config.VIDEO_WIDTH, config.VIDEO_HEIGHT
):
    # Add a critical issue.
```
it compare the actual dimensions against the configured dimensions. The message in your original code speciafically says 1080X1929, so that message should be kept consistent with the configuration if you ever change the target resolution. 

**C.Build the technical report**

```python 
report = (
    f"Duration: {info.duration:.1f} s "
    f"(target {config.VIDEO_MIN_SECONDS}-{config.VIDEO_MAX_SECONDS} s)\n"
    f"Resolution: {info.width}x{info.height}\n"
    f"Video stream: {info.has_video}, audio stream: {info.has_audio}\n"
    f"Scenes: {len(state.scene_durations)}"
)

return report, issues
```
Example report:

```text
Duration: 45.0 s (target 30-60 s)
Resolution: 1080x1920
Video stream: True, audio stream: True
Scenes: 6
```
the technical agents save the review to the `state` and the coordinator agent will decide to the next. 

**Feedback** 

This is the `feedback_section()` function, not a separate agent. It helps the Script Agent, Visual Agent, or another targeted agent understand what went wrong in the previous review and what it needs to fix.

**How it works** 
- **state** : Contains the previous review and its issues 
- **target** : Identifies which agent needs feedback,such as "script" or "visual"
- Return a string that can be added to that agent's prompt. 

**1.Check whether feedback is needed** 

```python
if not state.review or state.review.approved:
    return ""
```

If there is no previous review, or the previous video was approved, it returns an empty string.

**Meaning:** On the first attempt, there is no previous review feedback to provide.


