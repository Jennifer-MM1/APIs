#  APIs Workspace — FastAPI Services

Este repositorio contiene una colección de microservicios y APIs RESTful desarrollados con **FastAPI** y **Python**. Cada directorio representa una API independiente con su propio propósito, configuración de entorno y base de datos o servicio externo integrado.

---

##  Estructura del Repositorio

A continuación se muestra una visión general de los proyectos incluidos en este workspace:

```text
APIS/
├── Autenticacion/       # Servicio de registro, login y roles con MongoDB Atlas
├── Clima/               # API de consulta climática a OpenWeatherMap con cache en memoria
├── Gestion_proyectos/   # API para gestión de proyectos, tareas y miembros
├── IA/                  # Generador de posts para redes sociales usando Google Gemini
├── Pagos/               # API de pagos multi-pasarela (Stripe, PayPal, MercadoPago) con Turso
├── Productos_ventas/    # Gestión de productos, inventario y ventas (Tienda de Tecnología)
└── README.md            # Documentación del espacio de trabajo (este archivo)
```

---

##  Detalle de las APIs

### 1.  API de Autenticación y Autorización (`/Autenticacion`)
* **Descripción**: Servicio centralizado de autenticación para el ecosistema de APIs.
* **Características**:
  * Registro e inicio de sesión de usuarios.
  * Emisión y validación de tokens JWT.
  * Control de acceso basado en roles (RBAC) y permisos.
* **Base de Datos**: MongoDB Atlas (a través de Motor/Beanie u ODM equivalente).

### 2.  API de Clima (`/Clima`)
* **Descripción**: Consulta climática global utilizando la API de OpenWeatherMap.
* **Características**:
  * Clima actual y pronóstico a 5 días (intervalos de 3 horas).
  * Búsqueda por nombre de ciudad o coordenadas geográficas (latitud/longitud).
  * Respuestas localizadas en español con unidades métricas (°C).
  * Sistema de cache en memoria (10 minutos) para optimizar el rendimiento y limitar peticiones externas.

### 3.  API de Gestión de Proyectos (`/Gestion_proyectos`)
* **Descripción**: API para la organización y seguimiento de proyectos colaborativos.
* **Características**:
  * Creación y administración de proyectos.
  * Asignación y cambio de estado de tareas (To-Do, In Progress, Done).
  * Gestión de miembros del equipo con roles asignados por proyecto.
  * Autenticación mediante tokens JWT compartidos.
* **Base de Datos**: SQLite / PostgreSQL con soporte de migraciones mediante **Alembic**.

### 4. API Generadora de Contenido con IA (`/IA`)
* **Descripción**: Herramienta de inteligencia artificial para creadores de contenido.
* **Características**:
  * Generación de posts optimizados para Twitter/X, Instagram, LinkedIn y Facebook.
  * Selección de múltiples tonos de voz (profesional, casual, humorístico, educativo, inspiracional).
  * Generación de hashtags automática e integraciones multi-idioma (Español/Inglés).
  * Generación de múltiples variaciones para un mismo tema.
  * Historial de generación almacenado durante la sesión.
* **Motor de IA**: Google Gemini API.

### 5. API de Pagos — Multi-Gateway (`/Pagos`)
* **Descripción**: Pasarela unificada para la gestión de transacciones comerciales y suscripciones.
* **Características**:
  * Soporte nativo para múltiples gateways: **Stripe**, **PayPal** y **MercadoPago**.
  * Creación de clientes, planes y suscripciones recurrentes.
  * Procesamiento de reembolsos y gestión de webhooks para eventos en tiempo real.
  * Seguridad con JWT compartido.
* **Base de Datos**: Turso (libSQL).

### 6. API de Productos y Ventas (`/Productos_ventas`)
* **Descripción**: Sistema de comercio electrónico enfocado en una tienda de tecnología.
* **Características**:
  * Catálogo de productos y categorías (laptops, celulares, accesorios).
  * Control de inventario y stock en tiempo real al realizar pedidos.
  * Procesamiento de pedidos de venta calculando IVA (16%) de forma automática.
  * Control de acceso basado en roles (`admin` para inventario y `customer` para compras).
* **Base de Datos**: SQL con soporte de migraciones mediante **Alembic**.

---

## Configuración e Instalación General

### Requisitos Previos
* **Python 3.10+** instalado en tu sistema.
* Claves de API para los servicios que vayas a utilizar (Google Gemini, OpenWeatherMap, Stripe, PayPal, MercadoPago, MongoDB Atlas, Turso).

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Jennifer-MM1/APIs.git
cd APIs
```

### 2. Configurar Variables de Entorno `.env`
Cada API tiene un archivo `.env.example` en su directorio correspondiente. Debes copiar este archivo y renombrarlo a `.env`, completando las variables con tus credenciales.


Ejemplo en bash/cmd (repetir para cada carpeta de API):
```bash
# Ejemplo para la API de Clima
cd Clima
cp .env.example .env  # En Windows: copy .env.example .env
```

### 3. Instalar Dependencias y Ejecutar
Cada API es independiente. Para ejecutar cualquiera de ellas:

1. Entra a la carpeta correspondiente:
   ```bash
   cd Nombre_De_La_API
   ```
2. Crea un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv venv
   # Activar en Windows:
   .\venv\Scripts\activate
   # Activar en macOS/Linux:
   source venv/bin/activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Inicia el servidor de desarrollo:
   ```bash
   uvicorn main:app --reload
   ```
5. Accede a la documentación interactiva en tu navegador en:
   * Swagger UI: `http://127.0.0.1:8000/docs`
   * ReDoc: `http://127.0.0.1:8000/redoc`

---


