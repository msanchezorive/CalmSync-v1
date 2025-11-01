# CalmSync

CalmSync is a neurofeedback-based system that collects and analyzes EEG data from the **NeuroSky Mindwave Mobile 2** sensor to detect and interact with different mental states. The project demonstrates how **alpha, beta, meditation, and concentration** signals can be used to influence real-time game environments.

---

## Overview

CalmSync consists of three main components:

1. **Data Parser**  
   - Acquires and preprocesses EEG data from the Mindwave Mobile 2.  
   - Extracts key metrics: meditation, concentration, alpha, and beta waves.  
   - Stores session data in an SQL database for historical tracking.

2. **Game Modules**  
   - **Stress Game:** Designed to induce stress; does *not* use neurofeedback.  
   - **Relaxation Game:** Uses real-time alpha/beta wave feedback to dynamically modify scenery and promote relaxation.

3. **Session Reporting**  
   - Generates a detailed session report in **LaTeX** format.  
   - Includes metrics, trends, and user-specific session summaries.

---

## Objectives

- Demonstrate the feasibility of detecting distinct mental states from EEG signals.  
- Showcase how neurofeedback can influence and stabilize these states through interactive experiences.  
- Provide a foundation for future neuroadaptive gaming and mindfulness research.

---

## Features

- Real-time EEG signal acquisition and parsing  
- SQL-based session history and data persistence  
- Neurofeedback-controlled relaxation environment  
- Automated LaTeX report generation for each session  
- Modular architecture for easy extension of new game types

---

## Tech Stack

- **Hardware:** NeuroSky Mindwave Mobile 2  
- **Languages:** Python (for data parsing, SQL handling, LaTeX report generation)  
- **Database:** SQLite or MySQL  
- **Game Engine:** Unity / Pygame (depending on implementation)  
- **Visualization:** Matplotlib / PyQt (optional)

---

## Repository Structure

