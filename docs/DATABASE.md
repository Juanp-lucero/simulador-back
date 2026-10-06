# PostgreSQL y migraciones

La aplicación obtiene la conexión desde `DATABASE_URL`. La plantilla `.env.example` contiene una URL local de ejemplo, no credenciales reales; configúrala para el entorno donde se ejecute la aplicación. El motor utiliza SQLAlchemy 2 y el driver Psycopg 3, y las sesiones se cierran al terminar cada solicitud.

## Migraciones

Alembic está configurado en `alembic.ini` y usa `Base.metadata` como metadatos de los modelos. El entorno importa el paquete `app.models`; importa allí cualquier módulo de modelo nuevo antes de generar una revisión para que el autogenerador lo detecte.

Desde la raíz del backend:

```bash
alembic revision --autogenerate -m "describir el cambio"
alembic upgrade head
```

La migración `0001_create_users` crea la tabla de usuarios requerida por autenticación. Las migraciones se verificaron en SQLite temporal y en una instancia PostgreSQL 17 temporal; esto no acredita todavía la configuración de la base de producción del usuario.

`0002_aircraft_routes` agrega aeronaves, rutas y waypoints con claves foráneas, índices de propietario y restricciones de unicidad/rango. Al eliminar una aeronave, PostgreSQL desasigna sus rutas mediante `ON DELETE SET NULL`; los waypoints se eliminan con su ruta.
