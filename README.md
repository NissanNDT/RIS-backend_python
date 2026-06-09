# RIS - Backend Python / FastAPI

Este es el backend del sistema **RIS** (Reporte de Incidentes y Seguridad), reprogramado en **Python** utilizando **FastAPI** para ofrecer mayor rendimiento, documentación interactiva autogenerada y validaciones estrictas con Pydantic.

## Tecnologías y Librerías Utilizadas

- **Framework**: FastAPI
- **Servidor ASGI**: Uvicorn (para ejecutar la aplicación con recarga en caliente)
- **Base de Datos**: PostgreSQL en Supabase, utilizando `psycopg` para la gestión eficiente del pool de conexiones.
- **Validación de Datos**: Pydantic v2 (para la validación estricta de esquemas de datos entrantes y salientes).
- **Seguridad**: `bcrypt` para hash de contraseñas y `pyjwt` para la generación y validación de tokens de sesión JWT.
- **Generación de Reportes**: `openpyxl` para la lectura y escritura avanzada de archivos Excel, permitiendo exportar reportes idénticos a los del formato oficial.
- **Gestión de Entorno**: `python-dotenv` para la lectura de variables de entorno.

---

## Estructura del Proyecto

```text
backend_python/
├── config/                  # Configuración de conexiones de base de datos y pools
├── middlewares/             # Middlewares (ej. CORS, autenticación personalizada)
├── models/                  # Esquemas y modelos de datos de Pydantic
├── routes/                  # Routers de FastAPI para cada módulo / recurso
├── main.py                  # Archivo de inicio del servidor y configuración de la app
├── requirements.txt         # Dependencias de Python del proyecto
├── .env.local               # Configuración de variables de entorno locales
└── README.md                # Este archivo
```

---

## Configuración del Entorno

Crea un archivo `.env.local` en el directorio `backend_python` con las siguientes variables:

```env
DATABASE_URL=postgresql://usuario:contraseña@servidor:puerto/base_de_datos
JWT_SECRET=tu_clave_secreta_para_firmar_tokens
JWT_EXPIRES_IN=1h
ALLOWED_ORIGINS=http://localhost:5173,https://ris-frontend-peach.vercel.app,http://ris-frontend-peach.vercel.app
```

---

## Instalación y Ejecución

1. **Crear y Activar un Entorno Virtual** (Recomendado):
   ```bash
   python -m venv venv
   # En Windows:
   .\venv\Scripts\activate
   # En Linux/macOS:
   source venv/bin/activate
   ```

2. **Instalar Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el Servidor**:
   Puedes iniciar el servidor directamente con Python (que invoca a Uvicorn internamente):
   ```bash
   python main.py
   ```
   Or, llamando a Uvicorn desde la terminal:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 3000 --reload
   ```

El servidor estará disponible en `http://localhost:3000`.

---

## Documentación Interactiva (Swagger/Redoc)

Una de las principales ventajas de FastAPI es la autogeneración de documentación interactiva. Una vez que el servidor esté corriendo, puedes acceder a:

- **Swagger UI**: [http://localhost:3000/docs](http://localhost:3000/docs) (para probar los endpoints directamente en el navegador).
- **ReDoc**: [http://localhost:3000/redoc](http://localhost:3000/redoc) (para visualizar la documentación estructurada de la API).

---

## Endpoints Disponibles (Prefijo `/api`)

Todos los routers se encuentran registrados bajo el prefijo `/api` dentro de `main.py`:

- **Autenticación**: `routes/auth.py`
- **Usuarios y Roles**: `routes/users.py`, `routes/roles.py`
- **Áreas y Estructura**: `routes/plants.py`, `routes/areas.py`, `routes/sub_areas.py`, `routes/sv_by_area.py`, `routes/cost_centers.py`
- **Incidentes**: `routes/incidents.py`, `routes/incident_formats.py`, `routes/incident_images.py`
- **Árbol de Causas e Investigación**: `routes/factor_trees.py`, `routes/intervening_factors.py`, `routes/hazard_backgrounds.py`, `routes/countermeasure_plans.py`, `routes/control_hierarchies.py`, `routes/verification_methods.py`, `routes/analysis_participants.py`
- **Auditorías e Hallazgos**: `routes/audits.py`, `routes/findings.py`
- **Excel**: `routes/excel.py` (Mapea y genera los reportes de incidentes a formato de hojas de cálculo).
