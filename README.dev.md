# Новостное веб-приложение на FastAPI с UV

[![uv](https://img.shields.io/badge/powered_by-uv-FFD43B)](https://github.com/astral-sh/uv)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)

Минималистичное веб-приложение для управления лентой новостей с фильтрацией и авторизацией, построенное на современном стеке:

- **FastAPI** для веб-интерфейса и API
- **UV** для управления зависимостями и окружением
- **PostgreSQL** в качестве СУБД

## 🚀 Быстрый старт

### Предварительные требования
- Менеджер пакетов UV ≥0.7.0 ([установка](https://docs.astral.sh/uv/getting-started/))
- Python 3.13


## Запуск
1. `uv sync`
2. `uv run uvicorn src.app.main:app --reload --port 8000`

## Dev Запуск в Docker
1. `uv sync`
2. `uv pip freeze > requirements.txt`
3. `docker-compose -f compose.dev.yaml up --build`