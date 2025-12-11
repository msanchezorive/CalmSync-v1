# CalmSync 🧠

CalmSync is a **low-cost neurofeedback platform** built around a **MindWave Mobile EEG headset**, a **Raspberry Pi**, and a **touchscreen interface**.

Instead of stimulating the brain, CalmSync simply **listens**: it reads brain activity, extracts **alpha** and **beta** bands and simple vendor features (attention, meditation, signal quality), and transforms them into **real-time visual feedback** that the user can learn to modulate.

> ⚠️ **Disclaimer**  
> CalmSync is a **student research prototype**, intended for **education, exploration and experimentation**, **not** for clinical use or diagnosis. It is not a medical device.


---

## Project Overview

Modern life is full of **cognitive overload, stress and distraction**. Most tools that try to deal with this are either:

- **Subjective** – based on self-report or questionnaires  
- **Pharmacological** – relying on medication with side effects  
- **Expensive** – requiring clinical-grade equipment

CalmSync explores a different direction:  
using **low-cost EEG** and **visual feedback** to let people **see** and **train** their mental state in a gentle, non-invasive way.

The system:

- Uses a **MindWave Mobile** EEG headset to record brain activity from the forehead  
- Processes the signal on a **Raspberry Pi**  
- Extracts:
  - **Alpha power**
  - **Beta power**
  - **Attention**
  - **Meditation**
  - **Signal quality / noise**
- Computes a simple **mental state index**:
  
  \[
  IR = \frac{\text{Alpha}}{\text{Beta}}
  \]

- Feeds this index into a set of interactive modules:
  - Sensor **calibration**
  - **Alpha/Beta bars** visualizer
  - **Neurofeedback game** (weather changes with mental state)
  - **Stroop test** (attention / interference task)

---

## Main Features

- **Non-invasive neurofeedback** – no stimulation, only EEG readout and visual feedback  
- **Standalone** – runs entirely on a Raspberry Pi with touchscreen  
- **Shared EEG backend** – a single server (`udp.py`) provides data to all modules  
- **Real-time visualisation** – alpha/beta bars and an IR gauge  
- **Gamified feedback** – a landscape that turns stormy or sunny depending on the EEG-derived index  
- **Attention task** – tactile Stroop test before/after training  

---

## System Architecture

High-level data flow:

1. **MindWave Mobile EEG headset**  
2. Bluetooth → Raspberry Pi (`/dev/rfcomm0`)  
3. `udp.py`:
   - Connects to the MindWave via serial
   - Uses `generic_parser.py` to parse vendor packets
   - Extracts alpha, beta, attention, meditation, signal quality
   - Keeps the latest values in a shared dictionary
   - Serves them over **TCP** on `127.0.0.1:12345`
4. **Front-end modules** (Python scripts):
   - `initial_calibration.py`
   - `bars_visualizer.py`
   - `neurofeedback_game.py`
   - `test_stroop_tactil.py`
   - main GUI (CalmSync menu)
5. Each module creates an `EEGClient` (from `udp.py`) that:
   - Connects to the TCP server
   - Receives JSON lines with the latest EEG metrics
   - Locally smooths and uses them for its own UI

This design allows **all modules to share the same EEG stream** without reconnecting or resyncing the headset.

---

## Repository Structure

(Names may be adapted to your actual layout; this is the intended structure.)

```text
CalmSync-v1/
├── assets/
│   └── neurofeedback_scenery/
│       ├── paisaje.jpg
│       ├── sol_png.png
│       ├── rayo_png.png
│       └── nube_png.png
├── raspberry/
│   ├── udp.py
│   ├── generic_parser.py
│   ├── initial_calibration.py
│   ├── bars_visualizer.py
│   ├── neurofeedback_game.py
│   ├── test_stroop_tactil.py
│   └── main_interface.py   # customtkinter menu (name may vary)
├── requirements.txt
└── README.md

