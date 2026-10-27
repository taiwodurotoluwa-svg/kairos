FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
# bake the embedding model into the image so the first request is fast
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"
COPY backend/app ./app
COPY fixtures ./fixtures
ENV FIXTURES_DIR=/app/fixtures
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
