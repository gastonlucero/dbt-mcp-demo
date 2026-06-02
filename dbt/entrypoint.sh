#!/bin/bash
set -e

# Script de entrada para el contenedor dbt
# Permite ejecutar comandos dbt dentro de Docker

cd /app/dbt-demo-postgres

echo "🔧 dbt Analytics Environment"
echo "=============================="
echo ""
echo "PostgreSQL Host: ${DBT_POSTGRES_HOST}"
echo "PostgreSQL Port: ${DBT_POSTGRES_PORT}"
echo "PostgreSQL Database: ${DBT_POSTGRES_DATABASE}"
echo "MCP Server: ${MCP_SERVER_URL}"
echo ""

# Verify PostgreSQL connection
echo "🔗 Verificando conexión a PostgreSQL..."
max_attempts=10
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if pg_isready -h $DBT_POSTGRES_HOST -p $DBT_POSTGRES_PORT -U $DBT_POSTGRES_USER > /dev/null 2>&1; then
        echo "✅ PostgreSQL está disponible"
        break
    fi
    attempt=$((attempt + 1))
    echo "⏳ Intento $attempt/$max_attempts... esperando PostgreSQL..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ No se pudo conectar a PostgreSQL después de $max_attempts intentos"
    exit 1
fi

# If no arguments provided, start interactive shell
if [ $# -eq 0 ]; then
    echo ""
    echo "📊 Comandos disponibles:"
    echo ""
    echo "  dbt run              # Ejecuta todos los modelos"
    echo "  dbt test             # Ejecuta tests"
    echo "  dbt run && dbt test  # Ejecuta ambos"
    echo "  dbt docs generate    # Genera documentación"
    echo "  dbt debug            # Verifica la conexión"
    echo "  dbt parse            # Parsea modelos sin ejecutar"
    echo ""
    echo "Escribe 'exit' para salir"
    echo ""
    /bin/bash
else
    # Execute provided command
    exec "$@"
fi
