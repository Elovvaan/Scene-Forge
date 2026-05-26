# S.A.I.N OMEGA CINEMA ENGINE

A modular cinematic intelligence system for turning storyboard sheets into continuity-aware cinematic frame sequences and local MP4 renders.

## Milestone 1 Capabilities

- Clean startup entrypoint (`python main.py`)
- Storyboard sheet upload through a futuristic minimal desktop UI
- Automatic storyboard panel extraction
- Frame candidate generation per panel
- Sequential cinematic frame generation
- MP4 assembly locally
- Continuity chain persistence
- Organized outputs and references

## Project Structure

```
/SAIN_OMEGA_CINEMA_ENGINE
    main.py
    ui/
    engine/
    render/
    packets/
    continuity/
    references/
    outputs/
    storage/
```

## Run

```bash
python main.py
```

## Output Locations

- Storyboard planning refs: `SAIN_OMEGA_CINEMA_ENGINE/references/storyboard/`
- Rendered sequence frames: `SAIN_OMEGA_CINEMA_ENGINE/outputs/frames/sequence/`
- Final video: `SAIN_OMEGA_CINEMA_ENGINE/outputs/videos/`
- Continuity chain file: `SAIN_OMEGA_CINEMA_ENGINE/continuity/continuity_chain.json`
