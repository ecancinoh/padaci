# AGENTS

## Project Snapshot
- PADACI is a Django 4.2 logistics application for parcel delivery operations.
- Primary stack: Python 3.11, Django, MySQL, Bootstrap 4, Crispy Forms.
- Main workspace docs: [README.md](README.md). Treat it as a starting point, not the source of truth for OCR or deployment details.

## Start Here
- Configure the existing virtual environment and install dependencies from [requirements.txt](requirements.txt).
- Copy [.env.example](.env.example) to `.env` and provide MySQL plus `GEMINI_API_KEY` values.
- The app requires MySQL. There is no SQLite fallback in [padaci/settings.py](padaci/settings.py).
- When asked to start the app locally, prefer [start.bat](start.bat) on Windows because it activates `.venv`, runs migrations, ensures a superuser exists, and starts Django.

## Verified Commands
- Install dependencies: `pip install -r requirements.txt`
- Apply migrations: `python manage.py migrate`
- Run server: `python manage.py runserver`
- Create admin manually if needed: `python manage.py createsuperuser`
- Run targeted tests: `python manage.py test <app_label>`

## Architecture
- Global settings and app registration live in [padaci/settings.py](padaci/settings.py).
- URL mounting lives in [padaci/urls.py](padaci/urls.py).
- Core delivery domain models are in [routes/models.py](routes/models.py), especially `Entrega`, `RutaDia`, `ParadaRuta`, and payment records.
- `planner` contains planning logic and service-layer code: [planner/services.py](planner/services.py).
- `rendiciones` is the post-route accounting layer and has the most substantial existing tests: [rendiciones/tests.py](rendiciones/tests.py).
- `delivery_optimizer` is a separate AI-assisted optimization module.
- `deliveries` is mostly a compatibility wrapper around models and CRUD patterns already defined in `routes`; it is not mounted from [padaci/urls.py](padaci/urls.py).

## Coding Conventions
- Prefer Django class-based views for standard CRUD. Use function views only for workflow-heavy actions when the existing module already follows that pattern.
- Forms are mostly `ModelForm` classes with Bootstrap widget classes assigned in the form definition.
- Templates typically extend [templates/base.html](templates/base.html) and set the corresponding `active_*` sidebar block.
- Keep business logic out of templates. Follow the existing split between views, forms, and services when a service module already exists.
- Preserve Spanish user-facing copy and route names unless the change explicitly requires otherwise.

## Access Control
- Review role restrictions before changing views or navigation.
- Per-view access helpers are in [accounts/mixins.py](accounts/mixins.py).
- Global role-based request filtering is in [padaci/middleware.py](padaci/middleware.py).
- Navigation visibility is controlled in [templates/base.html](templates/base.html).

## Pitfalls
- README documentation for OCR is outdated. The current code uses Gemini, not EasyOCR. Verify behavior in [delivery_optimizer/services.py](delivery_optimizer/services.py) and route-related view code before changing AI flows.
- Fresh local setups depend on MySQL availability. If migrations fail, check the DB connection and whether `padaci_db` exists.
- [start.bat](start.bat) auto-creates a local superuser with default credentials if none exists. Avoid relying on that behavior in tests or production guidance.
- Deployment is shared-hosting oriented. Review [.cpanel.yml](.cpanel.yml), [passenger_wsgi.py](passenger_wsgi.py), and [wsgi_app.py](wsgi_app.py) before changing startup or static/media behavior.
- Some legacy code still references removed fields such as `numero_guia`; inspect related models and migrations before refactoring list/filter logic.

## Change Guidance
- Prefer targeted changes inside the relevant app instead of introducing new cross-app abstractions.
- If a change touches deliveries, confirm whether the real source of truth is `routes` before editing duplicated compatibility code.
- When modifying UI, preserve the Bootstrap 4 and SB Admin 2 patterns already used across templates.
- When changing deployment behavior, keep shared-hosting compatibility intact and avoid assuming container or VPS access.

## Useful References
- Local setup and project overview: [README.md](README.md)
- Environment variables: [.env.example](.env.example)
- Local startup helper: [start.bat](start.bat)
- Main template shell: [templates/base.html](templates/base.html)
- Planning workflow example: [planner/views.py](planner/views.py)
- Route domain models: [routes/models.py](routes/models.py)

## Instrucciones Especializadas
- Pruebas Django focalizadas: [.github/skills/pruebas-django-padaci/SKILL.md](.github/skills/pruebas-django-padaci/SKILL.md)
- Despliegue en hosting compartido: [.github/skills/deploy-hosting-compartido/SKILL.md](.github/skills/deploy-hosting-compartido/SKILL.md)
- Reglas del dominio para rutas y rendiciones: [.github/instructions/routes-rendiciones.instructions.md](.github/instructions/routes-rendiciones.instructions.md)