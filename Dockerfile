FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
COPY rank.py sandbox_app.py ./
COPY src ./src
COPY data ./data

EXPOSE 7860
CMD ["python", "sandbox_app.py", "--host", "0.0.0.0", "--port", "7860"]
