# DataOps - Pagila ✕ Python ✕ Docker ✕ Jenkins  
Pipeline automatizado de análisis de rentabilidad y churn de clientes para un negocio de alquiler de películas.

---

## 1. Descripción

Este proyecto ejecuta, de forma **100 % automatizada**, un proceso de extracción, análisis y visualización de datos desde una base de datos PostgreSQL (`pagila`):

1. **Ingesta**  
   - Se conecta a PostgreSQL (`pagila`) para consultar datos históricos de alquiler, pago, películas, categorías y clientes.

2. **Transformación**  
   - Calcula el puntaje de abandono de clientes.
   - Detecta películas poco rentables.
   - Resume la rentabilidad por categoría.
   - Ranking de sucursales por ingresos.

3. **Salida**  
   - Genera un archivo PDF (`reporte_pagila.pdf`) con gráficos y tablas.
   - Publica automáticamente el informe como artefacto en Jenkins.

4. **Orquestación**  
   - Todo el código corre dentro de un contenedor **Docker** reproducible.
   - Un pipeline en **Jenkins** compila la imagen, ejecuta el ETL y publica resultados.


---

## 2. Arquitectura

```
┌──────────────┐ docker compose ┌────────────────────┐
│ Jenkins Job │ ────────────────────▶│ Contenedor Python │
│ (pipeline) │ │ Script ETL Pagila │
└──────────────┘ │ │
▲ │ - Conecta a PG │
│ │ - Procesa métricas │
│ PDF como artefacto │ - Genera PDF │
└────────────────────────────│ - Output en /app │
└────────────────────┘
                     ▲
                     │
         ┌──────────────────────┐
         │ PostgreSQL (Pagila)  │
         │ init con pagila.sql  │
         └──────────────────────┘


```

---

## 3. Tecnologías

| Componente | Versión | Propósito |
|------------|---------|-----------|
| Python     | 3.10+   | Transformaciones y lógica ETL       |
| Pandas     | 2.x     | Procesamiento de datos              |
| psycopg2-binary | 2.9 | Conexión PostgreSQL               |
| matplotlib | 3.7+    | Visualizaciones y PDF               |
| Docker     | 24+     | Contenerización y aislamiento       |
| Jenkins    | 2.452+  | Automatización del pipeline         |
| Azure VM   | Ubuntu  | Infraestructura de despliegue       |
---

## 4. Estructura de carpetas

```

.
├─ app/
│ ├─ proyecto_bd_etl.py # Script principal ETL
│ ├─ config.py # Conexión PostgreSQL
│ ├─ requirements.txt # Dependencias Python
│ ├─ Dockerfile # Imagen para contenedor ETL
│ ├─ pagila.sql # Script para crear la base Pagila
│ └─ output/ # Carpeta del informe generado
├─ docker-compose.yml # Orquesta PostgreSQL + ETL + Jenkins
├─ Jenkinsfile # Define el pipeline de CI/CD
└─ README.md # Documentación del proyecto
````

---

## 5. Prerequisitos

| Requisito        | Notas                                         |
|------------------|-----------------------------------------------|
| Docker Engine    | Instalado en la Azure VM                      |
| Jenkins Agent    | Con acceso a Docker (`/var/run/docker.sock`)  |
| PostgreSQL       | Se inicializa automáticamente desde pagila.sql|
| Azure VM         | Con puertos 8080 (Jenkins) y 5432 habilitados |
| Git              | Clonado automático del repositorio            |

---


## 6. Ejecución local o en VM

```bash
# clonar repositorio
git clone https://github.com/tu-org/pagila-etl.git
cd pagila-etl

# levantar los servicios
docker compose up --build

# el PDF se genera en:
app/output/reporte_pagila.pdf

7. Pipeline Jenkins (Jenkinsfile)

pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps {
        git 'https://github.com/tu-org/pagila-etl.git'
      }
    }

    stage('Build ETL') {
      steps {
        sh 'docker compose build etl'
      }
    }

    stage('Run ETL') {
      steps {
        sh 'docker compose run --rm etl'
      }
    }

    stage('Publicar PDF') {
      steps {
        archiveArtifacts artifacts: 'app/output/*.pdf', fingerprint: true
      }
    }
  }

  post {
    always {
      sh 'docker compose down'
    }
  }
}


---


## 8. Extensiones sugeridas

| Idea                                     | Valor agregado                        |
| ---------------------------------------- | ------------------------------------- |
| Subir el PDF a Azure Blob Storage        | Distribución centralizada             |
| Agregar dashboard en Power BI o Superset | Visualización interactiva             |
| Agendar pipeline con triggers horarios   | Automatización real                   |
| Integrar Slack o Teams para alertas      | Notificación inmediata a stakeholders |
| Añadir ML para predicción de churn       | Análisis predictivo del negocio       |


---

## 10. Licencia

MIT License – Puedes modificar, usar y redistribuir libremente.

Desarrollado por [Tu Nombre]
🔗 GitHub: https://github.com/LorenaGL-source

