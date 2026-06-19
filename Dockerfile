FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt README.md rank.py validate_submission.py sandbox_app.py ./
COPY src ./src
COPY data ./data
COPY scripts ./scripts

EXPOSE 7860
CMD ["python", "sandbox_app.py", "--host", "0.0.0.0", "--port", "7860"]
