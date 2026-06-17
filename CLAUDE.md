# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Local development (Windows — preferred, handles venv + migrations + superuser)
start.bat

# Manual
python manage.py runserver
python manage.py migrate
python manage.py createsuperuser

# Run tests for a specific app
python manage.py test rendiciones
python manage.py test routes
python manage.py test accounts
```

There is no linter config, Makefile, or test runner beyond Django's built-in framework.

## Stack & Setup Requirements

- **Django 4.2 / Python 3.11 / MySQL 8+** — no SQLite fallback; `padaci_db` must exist before first migration.
- **Required env vars** (copy `.env.example` → `.env`): `SECRET_KEY`, `DB_*`, `GEMINI_API_KEY`.
- **`USE_L10N = True` + `USE_THOUSAND_SEPARATOR = True` with `LANGUAGE_CODE = es-cl`** — Django formats integers ≥ 1000 with a period separator (`1.234`). Always use `{{ value|unlocalize }}` when outputting PKs or numeric IDs into HTML attributes (`id=`, `data-*`) or JavaScript. Failing to do so causes `getElementById` mismatches for records with large PKs.
- Deployment target is cPanel shared hosting. Entry points are `passenger_wsgi.py` / `wsgi_app.py`. Avoid assuming container or VPS access.

## App Architecture

```
padaci/               — settings, URLs, middleware, WSGI
accounts/             — CustomUser with role field (admin, supervisor, conductor, peoneta, operador)
clients/              — Cliente model (coordinates, Waze/Maps URLs, visit time, delivery weight)
companies/            — Empresa model
routes/               — Core domain: Entrega, RutaDia, ParadaRuta + OCR + Falabella workflow
planner/              — Weekly planning; heavy logic in planner/services.py (TSP + Nearest Neighbor)
rendiciones/          — Post-route accounting (OneToOne on RutaDia); has the most tests
delivery_optimizer/   — Experimental Gemini-based optimization (separate from planner)
maps/                 — No models; GeoJSON endpoint + Leaflet.js client map
dashboard/            — No models; KPI view over existing data
asistencia/           — Attendance tracking
informe_servicio/     — Service reports
deliveries/           — Compatibility wrapper; not mounted in urls.py; real source is routes/
```

URL mounts (all under `padaci/urls.py`): `/rutas/` → routes, `/rendiciones/` → rendiciones, `/planificacion/` → planner, `/clientes/` → clients, `/mapa/` → maps, `/dashboard/` → dashboard, `/asistencia/` → asistencia.

## Domain Rules

The authoritative delivery domain lives in **`routes/models.py`**. Key models:

| Model | Role |
|---|---|
| `Entrega` | One delivery; FK to `Cliente`, `Empresa`, `conductor` |
| `RutaDia` | Daily route; has `modalidad` (estandar / falabella), `foto_hoja_ruta`, OCR fields |
| `ParadaRuta` | Ordered stop inside a route; FK to `Entrega`; `unique_together (ruta, orden)` |
| `EntregaPago` | Payment line(s) on a delivery (multiple methods per delivery) |
| `ParadaFalabellaMeta` | OneToOne on `ParadaRuta`; holds `direccion_importada` (Excel original, immutable), `direccion_original` (last searched), `estado_direccion`, geocoding state |
| `ParadaUbicacionCandidata` | FK to `ParadaRuta` (`related_name='ubicaciones_candidatas'`); one row per Nominatim result |
| `ClienteOCRAlias` | Persistent name→Client mapping learned from OCR to avoid re-matching |
| `RendicionReparto` | OneToOne on `RutaDia`; 5 deduction categories (A–E) |

**Cross-app rules:**
- If you change `Entrega` states or payment methods, check the impact on `rendiciones/views.py` (accounting autocomplete maps states to categories A–E).
- If you change `RutaDia` structure, verify `planner`, `rendiciones`, and any view that reads `conductor`, `peoneta`, `total_consolidado`, or `fecha`.
- The `deliveries` app duplicates some CRUD; the real source is always `routes`. Do not duplicate business rules between them.

## Falabella Workflow

Routes with `modalidad='falabella'` use a dedicated flow:

1. **Import** (`ruta_falabella_import`): reads an `.xlsx`, geocodes each address with `_geocode_free_address()`, creates `ParadaFalabellaMeta` (sets both `direccion_importada` and `direccion_original` from the Excel), runs TSP optimization.
2. **Detail view** (`ruta_falabella_detail`): must use `select_related('falabella_meta').prefetch_related('ubicaciones_candidatas')` to avoid N+1.
3. **Address search** (`falabella_actualizar_direccion`): updates `cliente.direccion` + `meta.direccion_original` (NOT `direccion_importada`).
4. **Re-optimize** (`falabella_reoptimizar`): runs `_falabella_optimizar_con_anclas()` — Nearest Neighbor TSP anchored to Rengo (origin) and Rancagua (end).
5. **Manual reorder** (`falabella_reordenar_paradas`): accepts `{orden: [parada_id, ...]}`, uses two-phase update to avoid `unique_together` collisions.
6. **Candidate selection** (`falabella_seleccionar_candidato`): picks a `ParadaUbicacionCandidata`, saves coords to `Cliente`, triggers re-optimization.

## Geocoding

`_geocode_nominatim()` in `routes/views.py` supports two modes:
- **Structured** (preferred): `street=`, `city=`, `state=` params — better precision for Chilean addresses.
- **Free-text** (`q=`): fallback when structured returns no results.

`_geocode_free_address(direccion, localidad)` tries structured first, then falls back. `_falabella_regenerar_candidatos()` follows the same pattern for generating candidate rows.

## Access Control

- Per-view mixins: `accounts/mixins.py` (`RolRestringidoMixin`, `AdminSupervisorMixin`).
- Global enforcement: `padaci/middleware.py` (`RoleAccessMiddleware`) — supervisors are read-only; conductors/peonetas are restricted to their section.
- Navigation visibility: `templates/base.html`.
- Check all three before adding or moving views.

## Frontend Conventions

- Templates extend `templates/base.html` and set the matching `{% block active_* %}` sidebar block.
- UI framework: Bootstrap 4 + SB Admin 2. Keep existing component patterns.
- Maps: Leaflet.js 1.9.4 + OpenStreetMap tiles (CDN). No Google Maps SDK.
- Drag-to-reorder: Sortable.js 1.15.2 (CDN), used in `falabella_detail.html`.
- All user-facing copy is in Spanish. Keep it that way.
- Business logic belongs in views/services, not templates.

## Pitfalls

- **OCR docs in README are outdated.** Current code uses Gemini (`google-genai` SDK) in `routes/views.py` and `delivery_optimizer/services.py`. EasyOCR is no longer used.
- **`numero_guia` is a removed field.** Legacy filter/list code may still reference it; inspect before refactoring.
- **Two-phase order updates.** `ParadaRuta` has `unique_together (ruta, orden)`. Any reordering must first assign temporary out-of-range ordinals, then apply final values inside `transaction.atomic()`.
- **`start.bat` auto-creates a superuser** (`admin` / `admin123`) on first run. Do not rely on this in tests or production.
