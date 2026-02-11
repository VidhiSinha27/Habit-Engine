# Habit Engine - React Web Project

This project contains a split-stack application:
1. **Backend**: Python FastAPI (Analytic Engine)
2. **Frontend**: React (User Interface)

## Setup

### 1. Backend
The backend utilizes the existing Python environment.
Ensure you are in the root folder `Habit Engine`.

```powershell
# Start the API Server
& ".\habitEngine\Scripts\python.exe" src/api/main.py
```
*Server runs at http://localhost:8000*

### 2. Frontend
Open a **new terminal**, navigate to the `web-client` folder, and start the development server.

```powershell
cd web-client
npm run dev
```
*Client runs at http://localhost:5173*

## Usage
1. Open the React Client URL (http://localhost:5173).
2. Use "User History Simulation" to generate training data and train the models.
3. Once trained, use "Daily Context" to input today's metrics and get recommendations.
