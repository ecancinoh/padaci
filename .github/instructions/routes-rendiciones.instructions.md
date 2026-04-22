---
applyTo: "routes/**/*.py,deliveries/**/*.py,planner/**/*.py,rendiciones/**/*.py,templates/routes/**/*.html,templates/rendiciones/**/*.html,templates/planner/**/*.html"
description: "Reglas del dominio en espanol para cambios que toquen entregas, rutas, planificacion semanal y rendiciones."
---

# Reglas del Dominio: Routes y Rendiciones

## Fuente de verdad

- La fuente principal del dominio de entregas y rutas esta en [routes/models.py](../../routes/models.py), especialmente `Entrega`, `EntregaPago`, `RutaDia` y `ParadaRuta`.
- El app `deliveries` funciona principalmente como wrapper de compatibilidad sobre ese modelo y no esta montado en [padaci/urls.py](../../padaci/urls.py).
- Si una regla de negocio cambia para entregas, estados, pagos o rutas, valida primero si la edicion correcta debe hacerse en `routes`.

## Limites entre apps

### routes

- Maneja el dominio operativo diario: entregas, estados, pagos registrados, rutas y paradas.
- Contiene logica de ejecucion real de ruta y parte de la integracion IA en vistas como [routes/views.py](../../routes/views.py).

### planner

- Maneja planificacion semanal y recomendaciones previas al reparto.
- La logica fuerte vive en [planner/services.py](../../planner/services.py).
- No mover a `planner` logica de cierre contable, pagos reales de entrega ni ejecucion diaria de ruta.

### rendiciones

- Maneja el cierre contable posterior a la ruta.
- [rendiciones/models.py](../../rendiciones/models.py) depende de `RutaDia` mediante una relacion `OneToOne`.
- [rendiciones/views.py](../../rendiciones/views.py) autocompleta items contables desde paradas, estados y pagos de entregas. Esa logica debe mantenerse idempotente y respetar ediciones manuales existentes.

## Reglas concretas para editar

1. Si tocas estados o metodos de pago en `Entrega` o `EntregaPago`, revisa el impacto directo en rendiciones.
2. Si tocas autocompletado o resumenes contables, valida los mapeos A/B/C/D/E en [rendiciones/views.py](../../rendiciones/views.py).
3. Si tocas filtros o listados en `routes` o `deliveries`, revisa referencias legacy como `numero_guia`; hay codigo historico que aun lo usa aunque no sea parte del modelo actual.
4. Si cambias la estructura de `RutaDia`, revisa `planner`, `rendiciones` y cualquier flujo que lea conductor, peoneta, total consolidado o fecha.
5. No dupliques reglas entre `routes` y `deliveries` salvo que sea estrictamente necesario por compatibilidad.

## Acceso y UI

- Antes de cambiar vistas o navegacion, revisa [accounts/mixins.py](../../accounts/mixins.py), [padaci/middleware.py](../../padaci/middleware.py) y [templates/base.html](../../templates/base.html).
- Mantener copy en espanol y patrones Bootstrap 4 ya existentes.

## Verificacion recomendada

- Para cambios de rendiciones o pagos, prioriza [rendiciones/tests.py](../../rendiciones/tests.py).
- Para cambios de planner, verifica [planner/services.py](../../planner/services.py) y el flujo en [planner/views.py](../../planner/views.py).
- Si un cambio cruza `routes` y `rendiciones`, valida ambos lados antes de cerrar la tarea.