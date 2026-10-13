# Multimodal Fusion Engine

A Python-based multimodal interaction project for controlling a graphical drawing palette through speech, gestures, and mouse pointing. Built for the final-year Human–Computer Interaction (HCI) practical at **UPSSITECH — University of Toulouse**.

The objective is to design a **multimodal fusion engine** inspired by the *Put That There* interaction paradigm. Instead of relying on a single input channel, the engine will combine information from multiple modalities to create and move graphical objects.

## Current status

**Initial integration validated.** The supplied Processing palette has been extended with an Ivy message listener. A manually sent Ivy message successfully created a circle in the running palette.

| Component | Status |
| --- | --- |
| Python environment and Ivy dependency | Set up locally |
| Processing drawing palette | Running locally |
| Ivy-to-Processing command interface | Implemented and manually tested for circle creation |
| Multimodal dialogue controller and fusion logic | Planned |
| Speech-recognition integration (`sra5`) | Planned |
| Gesture-recognition integration (`OneDollarIvy` / $N) | Planned |
| Automated test suite | Planned |

**Important:** The successful Ivy-to-Processing test is an integration smoke test, **not** a completed multimodal interaction. Real speech, gesture recognition, and temporal fusion have not yet been validated.

## Architecture

```text
Speech recognition / simulator ─┐
Gesture recognizer ─────────────┼──► Ivy message bus
Mouse pointing / palette ───────┘          │
                                          ▼
                              Python multimodal fusion engine
                              (events, temporal context, FSM)
                                          │
                                          ▼
                                    Ivy commands
                                          │
                                          ▼
                                   Processing palette
```

The applications communicate using the **Ivy software bus**, with a shared rendezvous address of `127.255.255.255:2010` for local development.

The provided Processing palette handles rendering and object manipulation; the Python application is intended to handle event interpretation, dialogue state, and multimodal fusion.

## Requirements

- **Windows** (recommended for the course-provided `sra5` and `ppilot5` tools)
- **Python 3.12** (tested environment: Python 3.12.10)
- **Processing 4** (tested environment: Processing 4.5.7, portable edition)
- **Git**
- Python packages listed in [`requirements.txt`](requirements.txt)
- Ivy Java library (`ivy-java-1.2.18.jar`) for the Processing sketch, located in `tools/Palette/code/`

Downloads: [Python](https://www.python.org/downloads/) · [Processing](https://processing.org/download) · [Git](https://git-scm.com/downloads) · [Ivy Java](https://github.com/truillet/ivy/blob/master/lib/ivy-java-1.2.18.jar)

## Getting started

### 1. Clone the repository

```powershell
git clone https://github.com/TJeanm/multimodal-fusion-engine.git
cd multimodal-fusion-engine
```

### 2. Create the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell prevents activating the environment, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then retry activation. Alternatively, use `.\.venv\Scripts\python.exe` directly without activation.

If `python` is not on `PATH`, call the installed Python 3.12 executable by its full path when creating the environment.

### 3. Launch the Processing palette

1. Open `tools/Palette/Palette.pde` in Processing 4.
2. Check that the Ivy Java JAR is present in `tools/Palette/code/`.
3. Click **Run**.
4. Check the Processing console for the Ivy connection confirmation.

The original keyboard controls remain available for local testing: `c` (circle), `r` (rectangle), `t` (triangle), `l` (diamond), and `m` (move).

### 4. Send an Ivy test command

Start the Ivy probe in another terminal, using the same bus address:

```powershell
ivyprobe.py -b 127.255.255.255:2010 "^(.*)"
```

Then send:

```text
Fusion Create=cercle X=200 Y=180
```

**Expected result:** a circle appears in the Processing palette at the requested coordinates.

This is a manual smoke test of the Ivy connection and the palette's command handler. It does not depend on the Python fusion logic.

## Ivy command protocol

The following command format was added to the course palette for this project:

```text
Fusion Create=<shape> X=<x> Y=<y>
```

Supported shapes: `cercle`, `rectangle`, `triangle`, `losange`. Coordinates are non-negative integer values in the palette's coordinate system.

Example:

```text
Fusion Create=rectangle X=350 Y=240
```

This is a **project-specific protocol**. It is not part of the unmodified course-provided palette. Additional messages for selection, movement, color, and pointing will be defined as the fusion engine evolves.

## Repository structure

```text
multimodal-fusion-engine/
├── fusion_engine/       # Python fusion engine (under development)
├── tools/
│   └── Palette/         # Processing palette and Ivy integration
├── requirements.txt     # Python dependencies
├── README.md
└── .gitignore
```

Planned directories include `simulators/`, `tests/`, `docs/`, and `report/` for input simulation, validation scenarios, design diagrams, and the final report. Empty directories may not appear in Git until files are added.

## Project scope and roadmap

The course requires multimodal creation and movement of circles, rectangles, triangles, and diamonds. The design must support flexible ordering of voice, gesture, and pointing inputs, optional color and position information, and disambiguation when necessary. **User-facing operations must combine modalities; a voice-only or gesture-only shortcut is not sufficient.**

Planned milestones:

1. Define voice and gesture grammars, event formats, and temporal interaction diagrams.
2. Specify the dialogue controller as a finite-state machine (FSM) and define the fusion context data model.
3. Implement the Python event adapters and temporal fusion logic.
4. Integrate speech recognition, gesture recognition, pointing, and optional spoken feedback.
5. Validate representative scenarios and document the design and results.

## Working as a team

Both contributors should work from their **own local clone** and their **own `.venv`**. Never commit `.venv` or machine-specific configuration.

For each change, create a dedicated branch, commit the files, push the branch, and open a pull request:

```powershell
git switch main
git pull origin main
git switch -c feature/short-description
# Make your changes
git add .
git commit -m "feat: describe the change"
git push -u origin feature/short-description
```

Keep the Ivy message protocol and shared event structures documented before developing independent modules.

## References and attribution

- [UPSSITECH — Multimodal Fusion practical](https://github.com/truillet/upssitech/blob/master/SRI/5A/IHM/TP/lab3-5_fusion.md)
- [Ivy middleware and course-provided tools](https://github.com/truillet/ivy)
- [OneDollarIvy gesture recognizer](https://github.com/truillet/OneDollarIvy)
- Richard A. Bolt, [*“Put-That-There”: Voice and Gesture at the Graphics Interface*](https://dl.acm.org/doi/10.1145/965105.807503) (1980)
- Denis Lalanne et al., [*Fusion Engines for Multimodal Input: A Survey*](https://iihm.imag.fr/publs/2009/FinalSurvey.pdf) (2009)

The initial Processing palette is supplied by the course instructors. This repository contains its adaptation for communication with the Python-based multimodal fusion engine.
