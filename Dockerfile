FROM python:3.12-slim
WORKDIR /app
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt
COPY src ./src
RUN useradd --create-home attendance
USER attendance
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.server.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
