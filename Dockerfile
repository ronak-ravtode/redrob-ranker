FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY rank.py sandbox_app.py ./
COPY src ./src
COPY data ./data
COPY models ./models

EXPOSE 7860
CMD ["python", "sandbox_app.py", "--host", "0.0.0.0", "--port", "7860"]
