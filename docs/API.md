# API de AeroMind IA

## Estado inicial

La documentación interactiva está disponible en `/docs` cuando se ejecuta la aplicación. La API mantiene separados los routers, schemas, services y models.

## Autenticación

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| `POST` | `/auth/register` | Público | Crea una cuenta con correo y contraseña; `username` es opcional y, si se omite, se deriva de la parte local del correo. |
| `POST` | `/auth/login` | Público | Recibe un formulario OAuth2 (`username` contiene el correo y `password` la contraseña); devuelve un JWT bearer. |
| `GET` | `/auth/me` | Bearer JWT | Devuelve el perfil del usuario autenticado. |

Las contraseñas se almacenan con Argon2 y nunca aparecen en las respuestas ni en los claims del JWT. Los tokens incluyen `sub`, `email`, `role`, `iat` y `exp`; la duración y la clave de firma se configuran con variables de entorno. `SECRET_KEY` debe tener al menos 32 bytes y solo se permiten algoritmos HMAC (`HS256`, `HS384` o `HS512`); si falta o no es válida, las operaciones con tokens fallan de forma cerrada. Define una clave aleatoria por medio del gestor de secretos del entorno; `CHANGE_ME` en `.env.example` es un marcador que no sirve para iniciar sesión.

El rol se limita a `admin` y `user`. La autorización por rol queda preparada para fases posteriores y no se usa todavía para restringir módulos.

## Aeronaves y rutas

Todos estos endpoints requieren Bearer JWT. Cada usuario solo puede leer y modificar sus recursos; un identificador ajeno devuelve `404`. Los listados aceptan `offset` y `limit` (máximo 100).

| Método | Ruta | Descripción |
|---|---|---|
| `GET`, `POST` | `/aircraft` | Lista o crea aeronaves. |
| `GET`, `PUT`, `DELETE` | `/aircraft/{id}` | Lee, reemplaza o elimina una aeronave. |
| `GET`, `POST` | `/routes` | Lista o crea rutas con entre 2 y 100 waypoints ordenados. |
| `GET`, `PUT`, `DELETE` | `/routes/{id}` | Lee, reemplaza o elimina una ruta y sus waypoints. |

Una aeronave contiene `registration`, `model_name`, `cruise_speed_mps` y `max_altitude_m`. La matrícula se normaliza a mayúsculas y es única. Una ruta contiene `name`, `aircraft_id` opcional y `waypoints`; el nombre es único por usuario. Solo se puede asignar una aeronave propia. Eliminar una aeronave deja sus rutas sin asignación, no elimina los planes.

Cada waypoint contiene `latitude_deg`, `longitude_deg`, `altitude_m` y `speed_mps`. La posición se expresa en grados geográficos; la altitud en metros y la velocidad en metros por segundo. El orden del array define la secuencia. `PUT` reemplaza el recurso completo. Las colisiones de matrícula/nombre devuelven `409`; los valores fuera de rango devuelven `422`.

## Simulación

`POST /simulation/preview` evalúa rutas propias en un tiempo simulado. Recibe `route_ids` y `elapsed_s`; devuelve posiciones, rumbo, velocidad, progreso y duración. Requiere aeronaves asignadas y no permite la misma aeronave en dos rutas del escenario. Los supuestos y límites están en [SIMULATION.md](SIMULATION.md).

### Historial de simulaciones

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/simulation/runs` | Calcula el preview y guarda `name`, `route_ids`, `elapsed_s` y el resultado. |
| `GET` | `/simulation/runs?offset=0&limit=20` | Lista las simulaciones propias, más recientes primero. Cada elemento indica `has_explanation`. |
| `GET` | `/simulation/runs/{id}` | Devuelve el resultado guardado y la explicación IA, si existe. |
| `PATCH` | `/simulation/runs/{id}` | Renombra la simulación (`{"name": "..."}`). |
| `DELETE` | `/simulation/runs/{id}` | Elimina la simulación y su explicación. |

Las simulaciones de otro usuario responden `404`.

## Métricas de rutas y dashboard

- `GET /routes/{id}/insights`: distancia total, tramos, duración estimada, rango de altitudes y velocidades, techo de la aeronave, margen bajo el techo, tasa vertical máxima y `warnings` (sin aeronave, techo superado o con margen menor a 150 m, velocidad mayor a 1,2 veces la de crucero, tasa vertical mayor a 10 m/s).
- `GET /stats`: conteo de aeronaves, rutas, waypoints y simulaciones guardadas, y distancia total planificada.
- `GET /health/details` (público): `{"status", "database", "ai_configured"}`.

## Asistencia IA con Groq

Los endpoints de IA requieren autenticación Bearer JWT y no sustituyen los cálculos del motor geométrico.

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/ai/status` | Devuelve proveedor, modelo y si existe configuración de Groq. No expone la clave. |
| `POST` | `/ai/simulation/explain` | Ejecuta el preview de rutas del usuario y solicita a Groq una explicación del resultado. |
| `POST` | `/ai/simulation/runs/{id}/explain` | Explica una simulación guardada y almacena la explicación. |
| `POST` | `/ai/routes/{id}/review` | Devuelve `{source, summary, strengths, risks, suggestions, insights}`. Con Groq, `source` es `"ai"`; sin clave o si el proveedor falla, `"rules"`. Nunca responde `502`/`503`. |

Ejemplo de cuerpo para `POST /ai/simulation/explain`:

```json
{
  "route_ids": [1],
  "elapsed_s": 120,
  "simulation_result": {}
}
```

El resultado enviado por el cliente no reemplaza los valores calculados por el servidor. Las posiciones y duraciones se vuelven a calcular a partir de las rutas propias y se entregan al proveedor solo para redactar una explicación. La respuesta incluye un aviso de alcance académico.

Respuestas de error:

- `401`: falta un token válido.
- `404`: ruta o aeronave no encontrada para el usuario.
- `422`: entrada inválida.
- `503`: `GROQ_API_KEY` no configurada.
- `502`: error al comunicarse con Groq.
