# <ai_context>
# Dockerfile for building and running the Python backend.
# </ai_context>

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["python", "src/main.py"] 