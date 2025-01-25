import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True, # Enable auto-reload during development
        reload_dirs=["/home/minecraftjuicer/vencovsky_projekt/backend/app"]
        )