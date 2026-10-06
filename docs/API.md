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
