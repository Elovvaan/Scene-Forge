# OMEGA Film Studio V2 — Desktop MVP

OMEGA is a director-first desktop application that proves one workflow: upload a storyboard and receive a completed MP4 short film.

## MVP Workflow

1. Upload a storyboard PDF, JPG, PNG, or ordered image sequence.
2. OMEGA automatically extracts ordered storyboard panels.
3. OMEGA creates a generated shot list.
4. OMEGA generates `start_frame.png` and `end_frame.png` for every shot.
5. OMEGA applies automatic continuity: the end frame of shot N becomes context for shot N+1.
6. OMEGA sends the shot package through a replaceable video provider interface.
7. OMEGA assembles generated clips into `Final_Film.mp4`.

## Desktop Screens

The V2 UI intentionally contains only the MVP surfaces:

- Project Dashboard
- Director Chat
- Shot Workspace
- Export Screen

Advanced dashboards, graphs, inspectors, accounts, billing, collaboration, audio, and marketplace features are out of scope for V2.

## Project Output Structure

```text
SAIN_OMEGA_CINEMA_ENGINE/project/
  universe_memory.json
  shots/
    shot001/
      start_frame.png
      end_frame.png
      clip.mp4
    shot002/
      start_frame.png
      end_frame.png
      clip.mp4
  Final_Film.mp4
```

## Video Provider Interface

The replaceable contract lives in `SAIN_OMEGA_CINEMA_ENGINE/render/video_provider.py`:

```python
generate_video(start_frame, end_frame, shot_context)
```

The desktop MVP ships with `LocalPreviewVideoProvider`, an offline provider that creates simple MP4 clips from start/end frames. Kling, Runway, or future providers can replace it without hard-coding provider logic into the OMEGA pipeline.

## Install

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```
