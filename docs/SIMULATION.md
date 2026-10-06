# Motor determinístico

Este módulo es un simulador geométrico académico, **no un sistema de control de tráfico aéreo ni un modelo operacional de vuelo**.

## Convenciones

- Latitud/longitud: grados geográficos, con longitud en `[-180, 180]`.
- Altitud: metros. Velocidad sobre el suelo: metros por segundo. Tiempo: segundos simulados.
- Rumbo: grados desde el norte verdadero, en sentido horario.
- Tierra esférica con radio medio de 6 371 008,8 m; no se modela el elipsoide WGS84.
- Cada tramo sigue el arco de círculo máximo más corto y usa la velocidad del waypoint de salida.
- La altitud cambia linealmente a lo largo del tramo. No se modelan viento, aceleración, rendimiento, virajes, límites de ascenso ni separación operacional.
- Al terminar una ruta, el estado queda en su último waypoint con velocidad cero.

El motor puro está en `app/simulation/engine.py`. `sample_path` depende solo de los waypoints y el tiempo recibido; no usa reloj, base de datos, aleatoriedad ni ML. Rechaza coordenadas no finitas, tramos de longitud cero y puntos antipodales.

## Preview

`POST /simulation/preview` requiere JWT y recibe:

```json
{"route_ids": [1, 2], "elapsed_s": 120}
```

Devuelve los estados de las rutas propias seleccionadas. Se permiten hasta 25 rutas y 86400 segundos por solicitud. Todas deben tener aeronave asignada; una aeronave no puede ocupar dos rutas simultáneas en el mismo escenario. La altitud del plan no debe exceder el límite almacenado de la aeronave.

Este endpoint es **stateless**: permite buscar un instante o repetir una evaluación con el mismo resultado. Todavía no mantiene sesiones compartidas, no persiste posiciones y no ejecuta un bucle autónomo.
