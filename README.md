<<<<<<< HEAD
# Team_O-DB_Chatbot

A web-based chat application with Python backend and HTML/JavaScript frontend.

## Project Structure

```
Team_O-DB_Chatbot/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── auth_database.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   └── chat_service.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── sql/
│   │   └── auth_db_init.sql
│   ├── .env              # Environment configuration
│   ├── prompt.txt
│   └── run.py
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
└── requirements.txt      # Python dependencies
```

## Setup & Installation

1. **Quick Setup (Linux/Unix)**

   ```bash
   # Make the setup script executable
   chmod +x setup.sh

   # Run the setup script
   ./setup.sh
   ```
2. **Manual Setup**

   ```bash
   # Create a virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate

   # Install dependencies using requirements.txt
   pip install -r requirements.txt
   ```
3. **Environment Configuration**

   - Copy `.env.example` to `.env` in the backend directory:
     ```bash
     cp backend/.env.example backend/.env
     ```
   - Update the following variables in `.env`:
     - `DB_*`: Configure your PostgreSQL database connection
     - `SECRET_KEY`: Set a secure random string for JWT encryption
     - `OPENAI_API_KEY`: Your OpenAI API key
     - Other settings as needed

## Running the Application

1. **Start the Backend**

   ```bash
   cd backend
   python run.py
   ```

   The API will be available at `http://localhost:8000`
2. **Start the Frontend**

   ```bash
   cd frontend
   python -m http.server 5500
   ```

   Access the application at `http://localhost:5500`

## Features

- User authentication and registration
- Real-time chat functionality
- Secure API endpoints
- Simple and intuitive UI

## Development

- Backend is built with FastAPI
- Frontend uses vanilla JavaScript
- PostgreSQL database for data persistence
- JWT-based authentication

## Notes

- Make sure to properly configure CORS settings in production
- Default frontend server is for development only
- Refer to API documentation at `/docs` endpoint for available API routes
=======
# Team_O-DB_Chatbot
>>>>>>> 9a36e3a52125e8daabfc6ef82d8693d7062f87b7
