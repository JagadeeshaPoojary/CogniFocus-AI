# CogniFocus-AI: AI-Powered Classroom & Behavior Monitoring Platform

**CogniFocus-AI** is a production-style full-stack web application designed to help educators and administrators monitor classroom environments in real time, identify potential mobile phone usage through computer vision and pose/behavior analysis, track student duration, map students to visual seat layouts, and generate actionable alerts and historical analytics.

---

## Key Features

- **Real-Time Camera Stream & Telemetry**: Live MJPEG video feed with real-time FPS overlay, camera controls, and automatic fallback mode.
- **YOLOv8 Pose & Behavior Analysis Engine**: Computer vision logic utilizing `yolov8n-pose.pt` keypoint geometry (wrist-to-face distance ratio, head tilt inclination angle) combined with object detection (`yolov8n.pt`) for mobile phone usage detection.
- **Visual Classroom Seat Layout**: Interactive 2D bench seating grid (Smart Board + Benches B1 to B12) displaying status badges (Normal, Monitoring, Suspicious, Alert) and usage duration.
- **Role-Based Access Control**:
  - **Admin** (`admin@classroom.com` / `admin123`): Full administrative access, classroom configuration, camera hardware management, system settings.
  - **Teacher** (`teacher@classroom.com` / `teacher123`): Classroom verification access code (`CSE301-8291`), live monitoring, visual seat map, alerts management, reporting.
- **Alert System & Cooldown Control**: Real-time alert generation when suspicious posture exceeds threshold (e.g. 5 seconds) with a 30-second cooldown per seat to prevent duplicate alerts. Actions to acknowledge and resolve alerts.
- **Analytics & Historical Reports**: Recharts line charts (alerts over time), donut charts (alert type breakdown), classroom seat heatmaps, date range filters, and CSV export.
- **System Configuration**: Real-time management of `config.json` parameters (confidence thresholds, alert timers, cooldown periods, model types, demo simulation toggle).
- **Demo / Simulation Mode**: Built-in fallback simulator generating annotated classroom frames with moving student pose skeletons and simulated phone usage when physical webcams are offline or disconnected.

---

## Tech Stack

### Frontend
- **Framework**: React.js 18 + Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router DOM v6
- **Icons & Charts**: Lucide React + Recharts
- **HTTP Client**: Axios

### Backend
- **Framework**: Python Flask + Flask-CORS
- **AI & Vision Engine**: OpenCV + Ultralytics YOLOv8 (PyTorch)
- **Database**: SQLite (`classroom_monitoring.db`)
- **Authentication**: JWT & Werkzeug Password Hashing

---

## Quick Setup Instructions

### 1. Prerequisites
- **Python**: 3.10+ (Tested on Python 3.12)
- **Node.js**: v18+ or v22+ (npm 10+)

### 2. Backend Setup
```bash
# Navigate to project root
cd CogniFocus-AI

# Create and activate virtual environment (Windows)
python -m venv venv
.\venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Seed SQLite database and start Flask server
python backend/app.py
```
*The Flask server will initialize `classroom_monitoring.db` and run on `http://127.0.0.1:5000`.*

### 3. Frontend Setup
Open a new terminal window:
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
*The frontend application will open on `http://localhost:5173`.*

---

## Demo Accounts & Verification Code

### Admin Login
- **Email**: `admin@classroom.com`
- **Password**: `admin123`

### Teacher Login
- **Email**: `teacher@classroom.com`
- **Password**: `teacher123`

### Classroom Verification Code
- **Code**: `CSE301-8291`

---

## Application Structure

```text
CogniFocus-AI/
├── frontend/
│   ├── src/
│   │   ├── components/      # SeatMapGrid, StatusIndicator, StatCard, AlertBadge, Modals
│   │   ├── pages/           # Login, Dashboard, LiveMonitoring, SeatMap, Alerts, Students, Classrooms, Cameras, Reports, Config
│   │   ├── layouts/         # MainLayout with Sidebar and Navbar
│   │   ├── services/        # Axios API client
│   │   ├── hooks/           # useAuth Context hook
│   │   ├── App.jsx          # React Router setup
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app.py               # Flask app entry point
│   ├── routes/              # Auth, Monitor, Alerts, Classrooms, Cameras, Students, Reports, Config
│   ├── ai/                  # AI Detector (YOLO pose) & Simulation Engine
│   ├── database/            # SQLite schema (db.py) & Seeder (seed.py)
│   └── config.json          # Live system configuration settings
│
├── models/
│   ├── yolov8n.pt           # YOLO object detection model
│   └── yolov8n-pose.pt      # YOLO pose estimation model
│
├── classroom_monitoring.db  # SQLite Database
├── config.json              # System configuration
├── requirements.txt         # Python dependencies
└── README.md
```

---

## API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate Admin / Teacher |
| `GET` | `/api/auth/me` | Fetch active user session |
| `GET` | `/api/monitor/status` | Real-time monitoring telemetry |
| `GET` | `/api/monitor/feed` | MJPEG real-time video stream |
| `GET` | `/api/monitor/seats` | Visual seat states & live detection status |
| `POST` | `/api/monitor/verify-code` | Validate classroom access code |
| `GET` | `/api/alerts` | List monitoring alerts with status filter |
| `POST` | `/api/alerts/:id/acknowledge` | Acknowledge active alert |
| `POST` | `/api/alerts/:id/resolve` | Resolve active alert |
| `GET` | `/api/classrooms` | Manage classrooms & seat layouts |
| `GET` | `/api/cameras` | Manage camera hardware & test connections |
| `GET` | `/api/students` | View student roster & posture history |
| `GET` | `/api/reports/analytics` | Aggregated analytics & time-series data |
| `GET` | `/api/reports/export` | Download CSV monitoring report |
| `GET / PUT` | `/api/config` | View and modify system configuration |

---

## Troubleshooting

- **Webcam Access Issues**: If a physical webcam is not attached or in use by another app, CogniFocus-AI automatically activates **Demo / Simulation Mode** to ensure uninterrupted visual monitoring demonstration.
- **CORS Issues**: Ensure the backend Flask server is running on `http://127.0.0.1:5000` and `VITE_API_URL` points to it.
