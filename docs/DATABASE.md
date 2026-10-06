# PostgreSQL y migraciones

La aplicación obtiene la conexión desde `DATABASE_URL`. La plantilla `.env.example` contiene una URL local de ejemplo, no credenciales reales; configúrala para el entorno donde se ejecute la aplicación. El motor utiliza SQLAlchemy 2 y el driver Psycopg 3, y las sesiones se cierran al terminar cada solicitud.

## Migraciones

Alembic está configurado en `alembic.ini` y usa `Base.metadata` como metadatos de los modelos. Cuando se agreguen entidades, importa sus módulos en el entorno de Alembic antes de generar una revisión para que el autogenerador las detecte.

Desde la raíz del backend:

```bash
alembic revision --autogenerate -m "describir el cambio"
alembic upgrade head
```

Todavía no se crea una migración inicial porque esta fase no define modelos de dominio. No se verificó una conexión a un servidor PostgreSQL real en el entorno de desarrollo de esta etapa.
