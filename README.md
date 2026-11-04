# Multimodal Fusion Engine

A Python-based multimodal interaction project for controlling a graphical drawing palette through speech, gestures, and mouse pointing. Built for the final-year Human–Computer Interaction (HCI) practical at **UPSSITECH — University of Toulouse**.

The objective is to design a **multimodal fusion engine** inspired by the *Put That There* interaction paradigm. Instead of relying on a single input channel, the engine will combine information from multiple modalities to create and move graphical objects.

## Current status

The multimodal fusion engine is implemented and validated
through automated tests and simulated Ivy interactions.

| Component | Status |
| --- | --- |
| Python fusion engine | Implemented |
| Dialogue FSM and temporal buffer | Implemented |
| Multimodal shape creation | Implemented |
| Multimodal shape movement | Implemented |
| Named colors (red, green, blue) | Implemented |
| Color lookup via Ivy | Implemented |
| Combined color and position references | Implemented |
| SRA5 speech grammar | Implemented, XML and semantic tests passed |
| OneDollarIvy gesture recognition | Integrated, real recognition pending validation |
| Processing palette | Extended, final graphical validation pending |
| Automated Python tests | 131 tests passed |

Note: Automated tests do not replace end-to-end validation
with the real Processing, SRA5 and OneDollarIvy applications.

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


## Ivy communication protocol

The application uses the Ivy message bus at `127.255.255.255:2010`.

### Input events

| Source | Message |
| --- | --- |
| Speech | `sra5 Parsed=action=create shape=circle Confidence=0.95 NP=0 Num_A=0` |
| Gesture | `OneDollarIvy Template=Cercle Confidence=0.95` |
| Mouse | `Palette Click X=200 Y=180` |

### Fusion engine commands

| Operation | Example |
| --- | --- |
| Create | `Fusion Create=cercle X=200 Y=180` |
| Create with color | `Fusion Create=cercle X=200 Y=180 Color=rouge` |
| Move | `Fusion Move Shape=cercle FromX=200 FromY=180 ToX=400 ToY=300` |
| Query color | `Fusion GetColor X=200 Y=180 RequestId=1` |
| Color response | `Palette ColorAt RequestId=1 Color=rouge` |

Supported shapes: `cercle`, `rectangle`, `triangle`, `losange`.

Supported colors: `rouge`, `vert`, `bleu`.

Color lookup may return `none` or `ambiguous` when no valid source can be identified.

The dialogue controller requires at least two distinct input modalities before executing a user command. The configured runtime fusion window is 8 seconds.

The Python protocol is covered by automated tests. Final validation with the real Processing palette and speech/gesture recognizers is still pending.


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


## Running the application

All applications communicate through the Ivy bus:

`127.255.255.255:2010`

### Clone the current project version

```powershell
git clone -b feature/finalisation-tp https://github.com/TJeanm/multimodal-fusion-engine.git
cd multimodal-fusion-engine


### 1. Install Python dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Start the fusion engine

```powershell
.\.venv\Scripts\python.exe -m fusion_engine.ivy_adapter
```

### 3. Start the Processing palette

Open `tools/Palette/Palette.pde` with Processing 4
and press Run.

The palette starts in Fusion mode.

Press V to switch between Fusion and local Debug modes.

### 4. Start speech recognition

On Windows, run:

```powershell
.\tools\sra5\sra5_on.bat
```

This loads `fusion_sra5_sapi.grxml`.

### 5. Start gesture recognition

Open `tools/OneDollarIvy/OneDollarIvy.pde`
with Processing 4 and press Run.

Import the trained templates and enter recognition mode.

### 6. Run automated tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

### 7. Test without graphical applications

Example: create a red circle at (300, 250).

```powershell
.\.venv\Scripts\python.exe -m simulators.send_test_events speech --shape circle --color red --here
.\.venv\Scripts\python.exe -m simulators.send_test_events click 300 250
```

The engine should output:

`Fusion Create=cercle X=300 Y=250 Color=rouge`

The events must arrive within the configured 8-second
fusion window.