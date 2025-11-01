CalmSync
CalmSync is a neurofeedback platform that connects to the NeuroSky MindWave Mobile 2 to measure and interpret brainwave activity — specifically meditation, attention, alpha, and beta signals.
Its goal is to detect different mental states and demonstrate how these states can be influenced through interactive neurofeedback games.
Overview
CalmSync enables users to visualize and modulate their cognitive states in real time. The system processes EEG data, stores session information, and offers both relaxing and stress-inducing environments to showcase neurofeedback’s potential.
Features
EEG Data Parser: Captures and processes meditation, attention, alpha, and beta wave data from the MindWave sensor.
State Detection: Classifies user mental states (e.g., relaxed, focused, stressed) based on EEG metrics.
Game Modules:
Stress Game: Designed to induce stress (no neurofeedback control).
Relax Game: Reacts dynamically to alpha/beta wave changes, adjusting the environment in real time.
Session Reporting: Generates a complete session report in LaTeX.
SQL History: Logs each session with timestamps, EEG metrics, and classification results.
System Architecture
Data Acquisition – Stream EEG data via Bluetooth from the MindWave Mobile 2.
Data Parser – Convert raw signals into structured metrics (alpha, beta, meditation, concentration).
State Classification – Identify cognitive states through defined thresholds or ML models.
Game Interaction – Send feedback values to the game modules to manipulate visuals or difficulty.
Report Generator – Export session summaries as LaTeX-based PDFs.
SQL Database – Store and retrieve user session data for analysis and history tracking.
Technologies
Python (data parsing, state detection, reporting)
NeuroSky MindWave SDK
SQL (SQLite/MySQL) for session history
LaTeX for automatic report generation
Game Engine (Unity/Pygame) for neurofeedback environments
Project Structure
calmSync/
│
├── parser/              # EEG data parser and communication with MindWave
├── states/              # Mental state detection logic
├── games/
│   ├── stress_game/     # Game without neurofeedback
│   └── relax_game/      # Neurofeedback-based environment
├── reports/             # LaTeX report generation
├── database/            # SQL schema and session storage
└── main.py              # Entry point for running CalmSync
Demo Workflow
Connect the MindWave Mobile 2 via Bluetooth.
Run the parser to start streaming EEG data.
Choose a game mode (stress or relax).
Play and observe neurofeedback in action.
After the session, generate a LaTeX report and store session data in SQL.
Future Directions
Advanced classification using deep learning.
Cross-session adaptation models.
Real-time dashboards for EEG visualization.
