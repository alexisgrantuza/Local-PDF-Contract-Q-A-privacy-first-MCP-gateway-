FROM python:3.10-slim


ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
&& apt-get install -y --no-install-recommends build-essential git curl gcc libsndfile1 \
&& rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt


# Pre-download the embedding model at build time to speed runtime
RUN python - <<PY
from sentence_transformers import SentenceTransformer
SentenceTransformer('all-MiniLM-L6-v2')
print('model cached')
PY


COPY ./app /app/app


EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]