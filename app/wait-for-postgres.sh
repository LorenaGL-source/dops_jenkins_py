#!/bin/sh

echo "⏳ Esperando a que PostgreSQL esté disponible..."

# Reintenta conexión hasta que PostgreSQL esté listo
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  sleep 1
done

echo "✅ PostgreSQL disponible. Ejecutando ETL..."

# Ejecuta el script Python
exec python proyecto_bd_etl.py
