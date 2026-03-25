"""
PADACI - URL Configuration principal
"""
import traceback
from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import include, path


def _log_url_import_error(section: str) -> None:
    base_dir = Path(__file__).resolve().parent.parent
    log_paths = [
        base_dir / "tmp" / "urlconf_import_errors.log",
        base_dir / "urlconf_import_errors.log",
        Path("/tmp/padaci_urlconf_import_errors.log"),
    ]
    payload = (
        "\n=== URL import error: " + section + " ===\n" + traceback.format_exc() + "\n"
    )
    for log_path in log_paths:
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as handler:
                handler.write(payload)
            break
        except Exception:
            continue


def _safe_include(route: str, module: str, namespace: str):
    try:
        return path(route, include(module, namespace=namespace))
    except Exception:
        _log_url_import_error(f"{route} -> {module}")
        return None


def _home(request):
    return redirect("dashboard:index")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", _home, name="home"),
]

for route, module, namespace in [
    ("accounts/", "accounts.urls", "accounts"),
    ("dashboard/", "dashboard.urls", "dashboard"),
    ("clientes/", "clients.urls", "clients"),
    ("empresas/", "companies.urls", "companies"),
    ("historial/", "history.urls", "history"),
    ("mapa/", "maps.urls", "maps"),
    ("planificacion/", "planner.urls", "planner"),
    ("rutas/", "routes.urls", "routes"),
    ("rendiciones/", "rendiciones.urls", "rendiciones"),
]:
    included = _safe_include(route, module, namespace)
    if included is not None:
        urlpatterns.append(included)


if not any(p.pattern.describe() == "'dashboard/'" for p in urlpatterns):
    def _fallback(request):
        return HttpResponse(
            "PADACI operativo parcialmente. Revisa tmp/urlconf_import_errors.log para detalle.",
            status=200,
            content_type="text/plain; charset=utf-8",
        )

    urlpatterns.append(path("", _fallback, name="home_fallback"))


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
