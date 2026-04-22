---
name: deploy-hosting-compartido
description: "Guia en espanol para cambios y recomendaciones de despliegue en el hosting compartido de PADACI, evitando suposiciones de VPS o contenedores."
argument-hint: "Opcionalmente indica si el cambio toca WSGI, archivos estaticos, migraciones o despliegue en cPanel"
---

# Despliegue en Hosting Compartido

Usa esta skill cuando el usuario pida preparar despliegue, revisar archivos de hosting, subir cambios para produccion o modificar el arranque de la aplicacion.

## Contexto obligatorio

- Este proyecto esta pensado para hosting compartido, no para VPS.
- Antes de sugerir cambios de despliegue, revisa [\.cpanel.yml](../../../.cpanel.yml), [passenger_wsgi.py](../../../passenger_wsgi.py), [wsgi_app.py](../../../wsgi_app.py) y [padaci/wsgi.py](../../../padaci/wsgi.py).
- No recomiendes por defecto `gunicorn`, `systemd`, `docker`, `nginx` administrado por el usuario o pipelines tipicos de VPS.

## Flujo verificado de despliegue

- [\.cpanel.yml](../../../.cpanel.yml) instala dependencias con `pip`, ejecuta migraciones, corre `collectstatic`, asegura la carpeta `media`, crea o actualiza el enlace simbolico de media y toca `tmp/restart.txt`.
- [passenger_wsgi.py](../../../passenger_wsgi.py), [wsgi_app.py](../../../wsgi_app.py) y [padaci/wsgi.py](../../../padaci/wsgi.py) incluyen logs de arranque y aplicaciones fallback para entornos donde Passenger o el host fallan silenciosamente.
- El proyecto usa `whitenoise` para estaticos y tiene logica defensiva para entornos compartidos en el arranque.

## Regla importante para produccion

- Si el usuario habla de subir cambios a GitHub para luego desplegar al hosting, recuerda que las migraciones en ese hosting dependen de su flujo real con cron. No des por hecho que puede entrar por SSH a ejecutar comandos manuales como en un VPS.

## Reglas de cambio

1. Mantener compatibilidad con cPanel y Passenger.
2. Preservar logs y mecanismos fallback cuando se toquen archivos WSGI.
3. No eliminar rutas de log en `tmp/` o `/tmp` sin una alternativa equivalente.
4. Si cambias estaticos o media, verifica el impacto sobre `STATIC_ROOT`, `collectstatic` y el enlace simbolico a `public_html/media`.
5. Si cambias configuracion SSL o proxy, revisa primero [padaci/settings.py](../../../padaci/settings.py).

## Cuando revisar mas contexto

- Cambios de dependencias: [requirements.txt](../../../requirements.txt)
- Variables de entorno: [.env.example](../../../.env.example)
- Arranque local en Windows: [start.bat](../../../start.bat)

## No hacer

- No proponer redisenar la infraestructura si el usuario solo pide un ajuste puntual.
- No asumir acceso root ni servicios persistentes administrados por el usuario.
- No quitar los fallbacks WSGI solo por limpiar codigo.

## Salida esperada al usuario

- Explica el cambio en terminos de hosting compartido.
- Si hay riesgo de romper el arranque, dilo antes de editar.
- Si el cambio requiere accion manual posterior en el hosting, dejalo explicitamente indicado.