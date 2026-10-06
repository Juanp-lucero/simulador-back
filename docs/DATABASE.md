# PostgreSQL y migraciones

La aplicación obtiene la conexión desde `DATABASE_URL`. La plantilla `.env.example` contiene una URL local de ejemplo, no credenciales reales; configúrala para el entorno donde se ejecute la aplicación. El motor utiliza SQLAlchemy 2 y el driver Psycopg 3, y las sesiones se cierran al terminar cada solicitud.

## Migraciones

Alembic está configurado en `alembic.ini` y usa `Base.metadata` como metadatos de los modelos. El entorno importa el paquete `app.models`; importa allí cualquier módulo de modelo nuevo antes de generar una revisión para que el autogenerador lo detecte.

Desde la raíz del backend:

```bash
alembic revision --autogenerate -m "describir el cambio"
alembic upgrade head
```

La migración `0001_create_users` crea la tabla de usuarios requerida por autenticación. Se verificó el upgrade y downgrade de esa migración en SQLite temporal; no se verificó una conexión a un servidor PostgreSQL real en este entorno.
