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
