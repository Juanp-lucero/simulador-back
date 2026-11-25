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

## Cómo probarlo

1. Entra a https://simulador-front.vercel.app e inicia sesión con la cuenta de prueba (o crea una cuenta en **Crear cuenta**). Abajo a la izquierda debe decir **API conectada** y **Asistencia IA activa (Groq)**.
2. **Aeronaves → nueva aeronave:** matrícula `HK-5001`, modelo `Cessna 172`, velocidad de crucero `60` m/s, altitud máxima `4200` m.
3. **Planes de ruta → nuevo plan:** nombre `Bogotá — Medellín`, aeronave `HK-5001` y estos waypoints (los valores grises son solo ejemplos; hay que escribirlos):

   | # | Latitud | Longitud | Altitud (m) | Velocidad (m/s) |
   |---|---|---|---|---|
   | 1 | 4.7016 | -74.1469 | 2600 | 60 |
   | 2 | 5.5 | -74.8 | 4100 | 60 |
   | 3 | 6.1714 | -75.4231 | 2100 | 55 |

4. En la ruta, pulsa **Métricas**: distancia, duración estimada, altitudes, velocidades y margen bajo el techo. Esta ruta muestra una alerta porque el waypoint 2 pasa a 100 m del techo de la aeronave.
5. Pulsa **Revisar con IA**: resumen, fortalezas, riesgos y sugerencias. La etiqueta **IA** indica que respondió Groq; **REGLAS** indica que se usó el respaldo automático.
6. **Simulador:** marca la ruta, **Cargar escenario**, reproduce o mueve la línea de tiempo y pulsa **Explicar con IA**. Escribe un nombre y pulsa **Guardar**.
7. **Historial:** abre la simulación guardada. Puedes explicarla con IA (la explicación queda guardada), renombrarla, eliminarla o **Abrir en el simulador** en el mismo segundo.
8. **Resumen:** totales de aeronaves, rutas, simulaciones guardadas, simulaciones explicadas con IA y distancia planificada.

## Cómo funciona

```
Angular + Leaflet + Chart.js (Vercel) ──REST + JWT──▶ FastAPI (Vercel) ──▶ PostgreSQL (Neon)
                                                          │
                                                          └──▶ Groq (IA, opcional)
```

1. **Motor de simulación (determinístico):** calcula la posición, altitud, velocidad, rumbo y progreso de cada aeronave en un instante, con geometría sobre la esfera terrestre. Es un modelo académico: no incluye viento, aceleración ni separación entre aeronaves.
2. **Métricas de ruta:** el backend calcula distancia, duración, rangos de altitud y velocidad, margen bajo el techo y tasa vertical. Genera alertas cuando:
   - la ruta no tiene aeronave;
   - supera el techo o queda a menos de 150 m de él;
   - va a más de 1,2 veces la velocidad de crucero;
   - sube o baja a más de 10 m/s.
3. **IA (Groq, `openai/gpt-oss-120b`):** solo interpreta. Recibe los números ya calculados y nunca los cambia.
   - **Explicar:** lectura en lenguaje natural de un instante de la simulación.
   - **Revisar ruta:** JSON validado con resumen, fortalezas, riesgos y sugerencias. Si la IA falla, responde con una revisión por reglas.
   - Si el modelo configurado deja de existir, el backend prueba otro automáticamente.
4. **Historial:** cada simulación guardada conserva sus rutas, el instante, el resultado calculado y, si se pidió, la explicación de la IA.

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
- `GROQ_MODEL`: modelo de Groq; por defecto `openai/gpt-oss-120b`.

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
| `POST` | `/ai/simulation/runs/{id}/explain` | Explica una simulación guardada y guarda el texto en el historial. |
| `POST` | `/ai/routes/{id}/review` | Revisa un plan de ruta. Usa Groq si está configurado y, si no, una revisión por reglas (`source: "rules"`). |

El endpoint de explicación requiere JWT y rutas pertenecientes al usuario autenticado. La respuesta generada no cambia coordenadas, altitudes, velocidades, duración ni progreso. La falta de API key devuelve `503`; un fallo del proveedor devuelve `502`. El preview determinístico existente sigue funcionando sin Groq.

El sistema no guarda prompts. Solo las explicaciones pedidas sobre una simulación guardada se almacenan junto a esa simulación, y se borran con ella. Evita incluir información sensible en los datos enviados al proveedor externo.

### Historial, métricas y estado

| Método | Ruta | Descripción |
|---|---|---|
| `GET`, `POST` | `/simulation/runs` | Lista (más recientes primero, con `offset` y `limit`) o guarda una simulación. |
| `GET`, `PATCH`, `DELETE` | `/simulation/runs/{id}` | Lee, renombra o elimina una simulación guardada. |
| `GET` | `/routes/{id}/insights` | Distancia, duración, altitudes, velocidades, margen bajo el techo y alertas de un plan. |
| `GET` | `/stats` | Totales del usuario para el dashboard. |
| `GET` | `/health/details` | Estado de la base de datos y de la configuración de IA, sin exponer secretos. |

Todas las rutas, salvo `/health/details`, requieren JWT y solo devuelven datos del usuario autenticado.
