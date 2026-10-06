# AeroMind IA · Backend

API FastAPI independiente del frontend Angular (`Juanp-lucero/simulador-front`). Implementa autenticación JWT, aeronaves, rutas y preview determinístico. Es un simulador académico, no un sistema operacional de navegación/ATC.

## Ejecutar

Requiere Python 3.11+ y PostgreSQL. Desde la raíz:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configura `DATABASE_URL`, `SECRET_KEY` (aleatoria, al menos 32 bytes) y `CORS_ORIGINS` mediante el gestor de secretos/variables del entorno. `.env.example` es solo una plantilla; la aplicación lee variables del proceso y no carga automáticamente un archivo `.env`. No guardes credenciales en Git.

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Documentación interactiva: `http://localhost:8000/docs`. El frontend local usa el puerto 4200. En un despliegue utiliza HTTPS y configura orígenes explícitos.

## Verificar

```bash
python -m pytest -q
python -m compileall -q app tests alembic
alembic check
```

Las pruebas habituales usan SQLite efímero y una clave de firma solo de test. La prueba opcional de PostgreSQL necesita una **base desechable**, migrada a head, y `SECRET_KEY` de test:

```bash
RUN_POSTGRES_TESTS=1 python -m pytest -q
```

Nunca hagas downgrade de una base con datos importantes para probar migraciones. La verificación de downgrade debe ejecutarse en una base temporal.

## Contratos y alcance

- [API](docs/API.md): autenticación, CRUD protegido y preview.
- [Base de datos](docs/DATABASE.md): migraciones y claves foráneas.
- [Simulación](docs/SIMULATION.md): unidades, modelo matemático y límites.
- [Análisis inicial](docs/PROJECT_ANALYSIS.md): diagnóstico histórico y roadmap.

La reproducción HTTP es stateless. WebSockets, persistencia de sesiones, conflictos, predicción, optimización e IA son etapas pendientes; no se simulan como funciones existentes.
