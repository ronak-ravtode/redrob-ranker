FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('all-MiniLM-L6-v2').save('models/all-MiniLM-L6-v2')"

COPY rank.py sandbox_app.py ./
COPY src ./src
COPY data ./data

EXPOSE 7860
CMD ["python", "sandbox_app.py", "--host", "0.0.0.0", "--port", "7860"]
