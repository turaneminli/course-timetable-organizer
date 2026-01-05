# Course Timetable Organizer

## Project Overview

This is a course timetable optimization system using genetic algorithms. The backend is a FastAPI application that loads problem instances (JSON format), runs GA optimization to assign sessions to timeslot-room combinations, and exports results as CSV files. A separate React UI consumes the API.

## Architecture

- **Backend**: FastAPI app in `app/main.py` with REST API endpoints
- **Core Logic**: `timetable/` module containing GA, fitness evaluation, repair, and data models
- **Data Flow**: Instance loading → GA optimization → Fitness evaluation → Constraint repair → Result export
- **UI**: Separate React/Vite application (not in this repo) that calls the API

## Key Components

- `timetable/models.py`: Data classes for Instance, Session, Room, Timeslot, etc.
- `timetable/ga.py`: Genetic algorithm implementation with multiprocessing support
- `timetable/fitness.py`: Constraint evaluation (hard penalties ×1000 + soft penalties)
- `timetable/repair.py`: Local search repair for hard constraint violations
- `timetable/loader.py`: JSON instance parsing (supports both "courses" and "sessions" formats)
- `timetable/export.py`: CSV export functions for schedule and group views

## Features

- Upload timetable problem instances (JSON format)
- Run genetic algorithm optimization
- View results with validation and statistics
- Export timetables as CSV

## Tech Stack

- **Backend**: Python FastAPI with genetic algorithm optimization
- **Frontend**: React with Vite, Recharts for visualization

## Quick Start

### Backend

```bash
cd course_timetable_organizer
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd ui
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Usage

1. Upload a JSON instance file via the web interface
2. Configure GA parameters (population size, generations, etc.)
3. Start optimization and monitor progress
4. Download results as CSV files

## Instance Format

JSON files with timeslots, rooms, courses/sessions, teacher availability, and preferences. See `test_files/` for examples.
