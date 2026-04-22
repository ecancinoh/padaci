---
name: pruebas-django-padaci
description: "Guia en espanol para ejecutar pruebas Django utiles en PADACI, priorizando validaciones focalizadas por app y evitando corridas amplias innecesarias."
argument-hint: "Opcionalmente indica el app o flujo que cambiaste, por ejemplo rendiciones, routes o planner"
---

# Pruebas Django en PADACI

Usa esta skill cuando el usuario pida validar cambios, agregar tests o ejecutar pruebas en este repositorio Django.

## Objetivo

- Ejecutar la menor cantidad de pruebas necesaria para validar el cambio.
- Favorecer `python manage.py test <app_label>` o una clase de prueba concreta antes que correr toda la suite.
- Recordar que este proyecto depende de MySQL y no tiene configuracion de `pytest`, `tox`, `ruff` o `mypy` en el repo.

## Reglas de trabajo

1. Antes de correr pruebas, confirma que el entorno Python del workspace este configurado y que la base MySQL este disponible.
2. Empieza por pruebas focalizadas del app afectado.
3. Evita `python manage.py test` global salvo que el usuario lo pida o el cambio afecte varias apps fuertemente acopladas.
4. Si no existe cobertura util en el area tocada, agrega una prueba pequeña en el `tests.py` del app correspondiente en vez de proponer una suite nueva.
5. Si una prueba falla por infraestructura ajena al cambio, reportalo con claridad y no encadenes arreglos no solicitados.

## Cobertura util verificada

- [rendiciones/tests.py](../../../rendiciones/tests.py): hoy es la cobertura mas sustantiva del proyecto y sirve como referencia para flujos contables, autocompletado desde rutas y exportaciones.
- Otros `tests.py` existen por app, pero varios son basicos o placeholders. No asumas cobertura profunda en `routes`, `deliveries`, `maps`, `dashboard` o `history` sin revisar primero.

## Comandos recomendados

- App completa: `python manage.py test rendiciones`
- Clase puntual: `python manage.py test rendiciones.tests.RendicionCreateTests`
- Otro app puntual: `python manage.py test planner`

## Estrategia por tipo de cambio

### Cambios en rendiciones

- Prioriza pruebas en [rendiciones/tests.py](../../../rendiciones/tests.py).
- Verifica calculos, autocompletado de items A/B/C/D/E, exportaciones y relaciones con `RutaDia`.

### Cambios en routes o pagos de entrega

- Revisa primero [routes/models.py](../../../routes/models.py) y [rendiciones/views.py](../../../rendiciones/views.py), porque rendiciones deriva datos desde pagos y estados de entrega.
- Si el cambio altera estados, pagos o flujo de ruta, agrega una prueba que cubra el impacto en rendiciones aunque el cambio principal este en `routes`.

### Cambios en planner

- Usa pruebas focalizadas sobre reglas de asignacion o capacidad, preferentemente cerca de [planner/services.py](../../../planner/services.py).
- No mezcles validaciones de planificacion semanal con ejecucion real de rutas o cierres contables.

## No hacer

- No introducir `pytest` o nuevas herramientas de calidad sin que el usuario lo pida.
- No asumir SQLite para pruebas locales.
- No usar [start.bat](../../../start.bat) como sustituto de las pruebas; ese script es para levantar la app, no para validar cambios.

## Salida esperada al usuario

- Indica exactamente que prueba corriste.
- Resume si el resultado valida el cambio o si hay un bloqueo de entorno.
- Si no corriste pruebas, dilo explicitamente y explica por que.