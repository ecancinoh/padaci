# PADACI – Sistema de Logística de Entrega de Paquetería

Sistema web de gestión logística para el control y seguimiento de entregas de paquetería con módulo de optimización de rutas asistido por Inteligencia Artificial.

---

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.11 + Django 4.2 |
| Frontend | Bootstrap 4 + SB Admin 2 Template |
| Base de Datos | MySQL 8+ |
| OCR (IA) | EasyOCR (open-source, sin costo) |
| Optimización de Rutas | Nearest Neighbor TSP (libre) |
| Mapas | Leaflet.js + OpenStreetMap (libre) |
| Navegación | Integración Waze (deep link) |

---

## Módulos / Aplicaciones

| # | App | Descripción |
|---|---|---|
| 1 | `accounts` | Mantenedor de usuarios (conductores, operadores, admins) |
| 2 | `companies` | Mantenedor de empresas distribuidoras/solicitantes |
| 3 | `clients` | Mantenedor de clientes receptores con geolocalización |
| 4 | `deliveries` | Registro de entregas de productos (CRUD completo) |
| 5 | `history` | Historial de entregas por día con métricas |
| 6 | `maps` | Vista de mapa de Chile con marcadores de clientes (Leaflet) |
| 7 | `routes` | Ruta del día con OCR de foto + optimización IA |
| 8 | `dashboard` | Dashboard con KPIs y gráficos |

---

## Modelo de Datos y Relaciones

```
Empresa (1) ──────────────── (N) Cliente
Empresa (1) ──────────────── (N) Entrega
Cliente (1) ──────────────── (N) Entrega
CustomUser (1) ───────────── (N) Entrega  [conductor]
CustomUser (1) ───────────── (N) RutaDia  [conductor]
RutaDia (1) ──────────────── (N) ParadaRuta
ParadaRuta (N) ─────────────── (1) Entrega
HistorialDia (1) ─────────── (N) DetalleHistorial
DetalleHistorial (N) ─────────── (1) Entrega
```

---

## Instalación y Configuración

### Requisitos previos
- Python 3.11+
- MySQL 8.0+
- Git

### 1. Clonar repositorio
```bash
git clone <url-repo>
cd padaci
```

### 2. Entorno virtual (ya creado)
```bash
# Windows
venv\Scripts\activate
```

### 3. Configurar base de datos MySQL
```bash
# En MySQL Workbench o terminal
mysql -u root -p < setup_db.sql
```

### 4. Configurar variables de entorno
Edita el archivo `.env`:
```ini
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=padaci_db
DB_USER=root
DB_PASSWORD=tu_password_mysql
DB_HOST=127.0.0.1
DB_PORT=3306

# Seguridad producción (recomendado)
CSRF_TRUSTED_ORIGINS=https://padaci.cl,https://www.padaci.cl
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### 5. Aplicar migraciones
```bash
python manage.py migrate
```

### 6. Crear superusuario
```bash
python manage.py createsuperuser
```

### 7. Iniciar servidor
```bash
python manage.py runserver
# o doble clic en start.bat (Windows)
```

### 8. Acceder al sistema
- **Dashboard:** http://127.0.0.1:8000/
- **Admin Django:** http://127.0.0.1:8000/admin/

---

## Funcionalidades Destacadas

### 🤖 Módulo IA – Ruta del Día
1. El usuario sube una **foto de la hoja de ruta** física
2. **EasyOCR** extrae el texto de la imagen (sin GPU, gratis)
3. El sistema hace **match** de los nombres con los clientes en BD
4. El algoritmo **Nearest Neighbor** ordena las entregas para minimizar distancia
5. Las paradas se guardan ordenadas y se visualizan en el **mapa Leaflet**
6. Botón de **Waze** por cada parada para navegación directa

### 🗺️ Mapa de Chile
- Visualización de todos los clientes geolocalizados
- Clustering de marcadores para grandes cantidades de clientes
- Popup con datos del cliente y link a Waze
- Identifica clientes sin coordenadas para completarlas

### 📊 Dashboard
- KPIs en tiempo real de entregas del día
- Gráfico de línea: historial de 7 días
- Gráfico donut: entregas por estado
- Tabla de últimas entregas con acceso rápido

### 🔗 Integración Waze
- En el detalle de cada entrega: botón "Abrir en Waze"
- En cada parada de la ruta: botón de navegación
- En el mapa de clientes: enlace en el popup

---

## URLs del Sistema

| URL | Módulo |
|---|---|
| `/` | Redirige a dashboard |
| `/accounts/login/` | Login |
| `/dashboard/` | Dashboard principal |
| `/clientes/` | Gestión clientes |
| `/empresas/` | Gestión empresas |
| `/entregas/` | Gestión entregas |
| `/historial/` | Historial por día |
| `/mapa/` | Mapa de Chile |
| `/rutas/` | Ruta del día |
| `/admin/` | Administración Django |

---

## Notas Técnicas

- **EasyOCR** descarga los modelos de IA en el primer uso (~350MB). Requiere conexión a Internet la primera vez.
- Las coordenadas (latitud/longitud) de los clientes se obtienen manualmente desde [latlong.net](https://www.latlong.net/) o similar.
- El algoritmo de optimización es **Nearest Neighbor** (greedy TSP). Para rutas más complejas, se puede activar **Google OR-Tools** (`ortools` ya instalado).
- Las imágenes se almacenan en `media/`. Configura tu servidor web para servir archivos media en producción.

---

**PADACI** © 2026
