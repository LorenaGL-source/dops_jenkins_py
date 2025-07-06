# Usar una imagen base de Python
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ✅ Instalar cliente de PostgreSQL para usar `pg_isready`
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*


COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/proyecto_bd_etl.py .
COPY app/wait-for-postgres.sh .

RUN chmod +x wait-for-postgres.sh

CMD ["./wait-for-postgres.sh"]