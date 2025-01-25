#!/bin/bash

echo "Setting up Team_O-DB_Chatbot..."

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Check if .env exists, if not copy from example
if [ ! -f backend/.env ]; then
    if [ -f backend/.env.example ]; then
        cp backend/.env.example backend/.env
        echo "Created .env file. Please configure it with your settings."
    fi
fi

# Start backend and frontend in separate terminals
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd backend && python run.py; exec bash"
    gnome-terminal -- bash -c "cd frontend && python -m http.server 5500; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -e "cd backend && python run.py" &
    xterm -e "cd frontend && python -m http.server 5500" &
else
    echo "Please open two terminals and run:"
    echo "Terminal 1: cd backend && python run.py"
    echo "Terminal 2: cd frontend && python -m http.server 5500"
fi
