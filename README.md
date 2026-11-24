# AeroMind IA · Backend

API FastAPI para el simulador académico AeroMind IA, integrada con el frontend Angular del repositorio `Juanp-lucero/simulador-front`.

## Despliegue

Desplegado en Vercel:

| | URL | Repositorio |
|---|---|---|
| Aplicación (frontend) | https://simulador-front.vercel.app | [Juanp-lucero/simulador-front](https://github.com/Juanp-lucero/simulador-front) |
| API (backend) | https://simulador-back.vercel.app | [Juanp-lucero/simulador-back](https://github.com/Juanp-lucero/simulador-back) |
| Estado de la API | https://simulador-back.vercel.app/health | |
| Documentación de la API | https://simulador-back.vercel.app/docs | |

El backend implementa autenticación JWT, gestión de aeronaves, rutas y un motor geométrico de simulación determinística. Incluye asistencia narrativa opcional con Groq para explicar resultados ya calculados por el motor.

> **Alcance académico:** el simulador no es un sistema operacional de navegación, despacho, predicción meteorológica ni control de tráfico aéreo. Las respuestas de IA tampoco son instrucciones de vuelo.

## Requisitos

- Python 3.11+
- PostgreSQL
- Una clave de Groq para habilitar explicaciones con IA (opcional)

## Instalación

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

Copia `.env.example` como `.env` y configura los valores para tu entorno. El backend carga automáticamente el archivo `.env` ubicado en la raíz del proyecto. En producción utiliza variables del gestor de secretos.

Variables principales:

- `DATABASE_URL`: conexión PostgreSQL.
- `SECRET_KEY`: clave aleatoria de firma JWT de al menos 32 bytes.
- `CORS_ORIGINS`: orígenes permitidos separados por coma.
- `GROQ_API_KEY`: clave privada de Groq. Déjala vacía para deshabilitar la asistencia IA.
- `GROQ_MODEL`: modelo de Groq; por defecto `llama-3.3-70b-versatile`.

Obtén tu clave en https://console.groq.com/keys. Nunca subas el archivo `.env` ni compartas la clave.

## Ejecutar

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Documentación interactiva: http://localhost:8000/docs

## Verificación

```bash
python -m pytest -q
python -m compileall -q app tests alembic
alembic check
```

La suite ordinaria usa SQLite temporal. La prueba de integración PostgreSQL es opcional y requiere una base desechable, migrada a head:

```bash
RUN_POSTGRES_TESTS=1 python -m pytest -q
```

## API

- [Contrato API](docs/API.md)
- [Base de datos](docs/DATABASE.md)
- [Motor de simulación](docs/SIMULATION.md)
- [Análisis del proyecto](docs/PROJECT_ANALYSIS.md)

### Asistencia IA

La IA está separada del motor matemático. El backend calcula el preview con `preview_simulation`; después, el endpoint autenticado envía la entrada y el resultado del servidor a Groq para obtener una explicación en lenguaje natural.

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/ai/status` | Indica si Groq está configurado, sin exponer secretos. |
| `POST` | `/ai/simulation/explain` | Calcula el preview y devuelve una explicación contextualizada de Groq. |

El endpoint de explicación requiere JWT y rutas pertenecientes al usuario autenticado. La respuesta generada no cambia coordenadas, altitudes, velocidades, duración ni progreso. La falta de API key devuelve `503`; un fallo del proveedor devuelve `502`. El preview determinístico existente sigue funcionando sin Groq.

El sistema no persiste prompts ni respuestas de IA. Evita incluir información sensible en los datos enviados al proveedor externo.
