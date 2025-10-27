CalmSync: Neurofeedback State Detection and Training

CalmSync is an innovative proof-of-concept project designed to demonstrate the real-time detection and manipulation of human mental states using data acquired from the NeuroSky MindWave Mobile 2 EEG sensor. The core idea is to translate complex brainwave data into meaningful biofeedback that users can intuitively learn to control through immersive, state-specific games.

Project Goals

The primary objective of CalmSync is to provide a comprehensive system that can:

Acquire and Parse raw brainwave data (Alpha, Beta, Meditation, Concentration) in real-time.

Detect and Classify distinct mental states (e.g., focused, relaxed, stressed).

Demonstrate Neurofeedback by creating interactive games that respond dynamically to the user's brain activity.

Key Features

Real-Time EEG Data Acquisition: Seamless integration with the NeuroSky MindWave Mobile 2 sensor.

Mental State Detection: Advanced parsing to derive key metrics: Meditation, Concentration, Alpha Waves, and Beta Waves.

Dual Game Modules: Interactive experiences tailored for state manipulation and demonstration.

Historical Logging: Robust session tracking and data storage using SQL.

Professional Reporting: On-demand generation of session reports and analysis using a LaTeX template.

System Components

The CalmSync project is divided into three main operational modules:

1. Data Acquisition and Parser

This module handles the communication with the NeuroSky sensor.

Sensor Interface: Establishes a connection (likely Bluetooth/BLE) to receive continuous brainwave packets.

Parser Logic: Processes the raw data stream to extract the essential metrics (Alpha/Beta power, eSense Meditation, eSense Concentration).

State Detection Engine: Implements algorithms (e.g., threshold analysis, moving averages) to classify the user's current dominant mental state based on the ratio and magnitude of the acquired metrics (e.g., high Alpha/low Beta for relaxation).

2. Neurofeedback Game Modules

Two distinct game environments are implemented to validate the state detection and neurofeedback capabilities.

Game Name

Primary Goal

Mechanism

Neurofeedback

Stress Inducer

Demonstrate inducing a high-stress, high-focus state.

High-pressure, fast-paced challenge requiring intense focus.

None. Used as a baseline and control group activity.

Relaxation Oasis

Induce and train a state of deep relaxation.

Neurofeedback Loop: The game scenery (e.g., lighting, music tempo, visual smoothness) changes directly based on the user's Alpha (relaxation) and Beta (alertness) wave ratio. Higher Alpha relative to Beta leads to a calmer, more expansive virtual environment.

Active. Direct brainwave control.

3. Database and Reporting

This ensures data persistence and provides formal documentation for training sessions.

SQL Session History: Every training session, including timestamps and recorded minute-by-minute metric averages, is logged into a structured SQL database for later analysis.

LaTeX Report Generator: Users can request a formatted report (un informe de la sesion). This component pulls the session data from the SQL database and dynamically generates a clean, professionally typeset PDF document using LaTeX. The report includes performance graphs, average state metrics, and a summary of the session.

Installation and Setup

Prerequisites

Hardware: NeuroSky MindWave Mobile 2 Headset.

Software Dependencies (Example):

Python (for data parsing and backend logic)

A suitable library for serial/Bluetooth communication (e.g., pySerial or a custom NeuroSky SDK wrapper).

A SQL Database (e.g., SQLite, PostgreSQL, or MySQL) and corresponding Python connector (e.g., SQLAlchemy).

A LaTeX distribution (e.g., TeX Live or MiKTeX) for report generation, along with a Python library for calling LaTeX compilation (e.g., pylatex or template rendering).

Quick Start (Conceptual)

Install Dependencies: pip install -r requirements.txt (Hypothetical)

Database Setup: Initialize the SQL schema.

Sensor Pairing: Pair the NeuroSky headset with your computer.

Run Application: python main.py

Usage Workflow

Connect: Start the CalmSync application and ensure the NeuroSky sensor is connected and transmitting data.

Select Activity: Choose either the Stress Inducer or the Relaxation Oasis game module.

Play & Train: Engage with the game. Observe how your brain activity (and therefore your mental state) directly influences the relaxation environment.

End Session: Stop the game. The session data is automatically logged to the SQL database.

Generate Report: Request a formal LaTeX report of the session for detailed review and performance tracking.