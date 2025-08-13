@echo OFF

REM Kill any existing servers
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul

REM Upgrade pip and install Python dependencies, then start the backend server
start "Backend" cmd /k "python -m pip install --upgrade pip && pip install -r requirements.txt && python app.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Install frontend dependencies and start the server with Vite
start "Frontend" cmd /k "cd ../frontend && npm install && npm run dev"
