# main.py (корневой файл проекта)
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from src.app.main import app  # Импортируем приложение из указанного пути

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)