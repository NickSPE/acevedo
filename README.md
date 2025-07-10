# 💰 FinGest - Sistema de Gestión Financi## 🎯 Descripción

FinGest es una **plataforma integral de gestión financiera** que combina herramientas prácticas de administración de dinero con recursos educativos para mejorar la alfabetización financiera.

### 🌟 Objetivos Principales
- **💡 Educación Financiera**: Recursos y herramientas para aprender sobre finanzas personales
- **📊 Gestión de Ingresos y Gastos**: Control detallado de las finanzas personales y familiares  
- **🎯 Toma de Decisiones**: Análisis y reportes para decisiones financieras informadas
- **🤝 Inclusión Social**: Especialmente dirigido a contextos de vulnerabilidad económica
- **🌍 Impacto Social**: Contribución a los Objetivos de Desarrollo Sostenible

---

## ✨ Características Principales

### 👤 **Gestión de Usuarios**
- 🔐 Autenticación segura con PIN de acceso rápido
- 👥 Perfiles personalizados con soporte multi-moneda
- 🛡️ Sistema de roles y permisos

### 💰 **Gestión Financiera**
- 📈 Seguimiento de ingresos y gastos
- 🏦 Gestión de cuentas principales y subcuentas
- 💸 Transferencias entre cuentas
- 🎯 Establecimiento de metas financieras
- 📊 Dashboard con estadísticas en tiempo real

### 📋 **Reportes y Análisis**
- 📄 Reportes en PDF, Excel y CSV ultra profesionales
- 📊 Gráficos interactivos y estadísticas
- 📈 Análisis de tendencias financieras
- 💼 Reportes personalizados por período

### 🔔 **Alertas y Notificaciones**
- ⚡ Notificaciones automáticas configurables
- 📧 Alertas por email
- 🎯 Recordatorios de metas y pagos
- 📱 Notificaciones en tiempo real

### 🎓 **Educación Financiera**
- 📚 Recursos educativos integrados
- 💡 Tips y consejos financieros
- 🏆 Gamificación del aprendizaje

### ⚙️ **Administración**
- 🛠️ Panel administrativo completo
- 📊 Gestión de usuarios y configuraciones
- 🔍 Herramientas de monitoreo y análisis
[![Python](https://img.shields.io/badge/Python-3.12.7-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**FinGest** es una aplicación web completa de gestión y educación financiera desarrollada con **Python** y **Django**. Diseñada para promover la alfabetización financiera y mejorar la toma de decisiones económicas de personas, familias y emprendedores.

> 🎯 **Alineado con los ODS**: Contribuye al ODS 1 (Fin de la pobreza) y ODS 8 (Trabajo decente y crecimiento económico)

---
      
## 📋 Tabla de Contenido
1. [🎯 Descripción](#-descripción)
2. [✨ Características Principales](#-características-principales)
3. [🖼️ Demo](#️-demo)
4. [🚀 Instalación](#-instalación)
5. [📁 Estructura del Proyecto](#-estructura-del-proyecto)
6. [📚 Guía de Uso](#-guía-de-uso)
7. [🛠️ Tecnologías](#️-tecnologías)
8. [👥 Colaboradores](#-colaboradores)
9. [📄 Licencia](#-licencia)yecto “Sistema de Gestión de Ingresos y Gastos” es una aplicacion web de gestion y educacion financiera, desarrollada usando el lenguaje de programacion Python, junto con la libreria de Django para desarrollo web, ademas de que se usara la base de datos PostgreSQL junto con el sistema de control de versiones de Git y Github como repositorio.

---

## Tabla de Contenido
1. [Descripcion](#descripcion)

2. [Demo](#demo)

3. [Instalacion del Codigo Fuente](#instalacion-del-codigo-fuente)

4. [Estructura del Proyecto](#estructura-del-proyecto)

5. [Guia de Uso](#guia-de-uso)

6. [Colaboradores](#guia-de-uso)

---

## Descripcion

El proyecto “Sistema de Gestión de Ingresos y Gastos” tiene como objetivo principal desarrollar una solución digital que promueva la alfabetización financiera y contribuya a una mejor toma de decisiones económicas entre personas, familias y emprendedores, especialmente en contextos de vulnerabilidad económica. 

Este sistema está alineado con los Objetivos de Desarrollo Sostenible (ODS), particularmente el ODS 1 (Fin de la pobreza) y el ODS 8 (Trabajo decente y crecimiento económico).

## 🖼️ Demo

> 🚧 **Demo en desarrollo** - Próximamente disponible online

### 📸 Capturas de Pantalla

**Dashboard Principal**
- Vista general de finanzas personales
- Gráficos interactivos de ingresos/gastos
- Resumen de cuentas y subcuentas

**Gestión de Subcuentas**
- Organización de dinero por categorías
- Seguimiento de metas financieras
- Transferencias entre cuentas

**Reportes Profesionales**
- Exportación en PDF, Excel y CSV
- Gráficos y estadísticas detalladas
- Reportes personalizados

---

## 🚀 Instalación
### 📋 Requerimientos

**Software necesario:**
- 🐍 **Python 3.12.7** o superior
- 💻 **VSCode** (recomendado) o cualquier editor de código
- 🔧 **Git** para control de versiones
- 🐘 **PostgreSQL** (opcional, incluye SQLite por defecto)

### 🔧 Instalación Rápida

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/FinGest.git
cd FinGest
```

2. **Crear y activar entorno virtual**
```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Crear superusuario (opcional)**
```bash
python manage.py createsuperuser
```

6. **Ejecutar servidor de desarrollo**
```bash
python manage.py runserver
```

7. **Acceder a la aplicación**
```
🌐 Aplicación: http://127.0.0.1:8000/
👨‍💼 Admin: http://127.0.0.1:8000/admin/
```

### 🐘 Configuración con PostgreSQL

1. **Instalar PostgreSQL**
2. **Crear base de datos**
```sql
CREATE DATABASE fingest_db;
CREATE USER fingest_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE fingest_db TO fingest_user;
```

3. **Configurar en `settings.py`**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'fingest_db',
        'USER': 'fingest_user',
        'PASSWORD': 'tu_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 📁 Estructura del Proyecto

```bash
FinGest/
├── 📁 administracion/           # App de administración del sistema
├── 📁 alertas_notificaciones/   # Sistema de notificaciones y alertas
├── 📁 analisis_reportes/        # Generación de reportes (PDF, Excel, CSV)
├── 📁 core/                     # Funcionalidades base del sistema
├── 📁 cuentas/                  # Gestión de cuentas y subcuentas
├── 📁 educacion_financiera/     # Módulo educativo
├── 📁 FinGest/                  # Configuración principal de Django
├── 📁 gestion_financiera_basica/ # Gestión básica de finanzas
├── 📁 usuarios/                 # Gestión de usuarios y autenticación
├── 📁 venv/                     # Entorno virtual de Python
├── 📄 manage.py                 # Script principal de Django
├── 📄 requirements.txt          # Dependencias del proyecto
├── 📄 README.md                 # Documentación del proyecto
└── 📄 LICENSE                   # Licencia del proyecto
```

### 🗂️ Descripción de Apps

| App | Descripción | Funcionalidades |
|-----|-------------|-----------------|
| **👨‍💼 administracion** | Panel administrativo | Gestión de sistema, configuraciones |
| **🔔 alertas_notificaciones** | Sistema de alertas | Notificaciones automáticas, emails |
| **📊 analisis_reportes** | Reportes y análisis | PDF, Excel, CSV profesionales |
| **⚙️ core** | Funcionalidades base | Dashboard, decoradores, utilidades |
| **💰 cuentas** | Gestión de cuentas | Cuentas principales, subcuentas, transferencias |
| **🎓 educacion_financiera** | Educación | Recursos educativos, tips financieros |
| **🏦 gestion_financiera_basica** | Finanzas básicas | Ingresos, gastos, categorías |
| **👤 usuarios** | Gestión de usuarios | Autenticación, perfiles, configuraciones |

## 📚 Guía de Uso

### 🚀 Primeros Pasos

1. **📝 Registro e Inicio de Sesión**
   - Crear cuenta nueva o iniciar sesión
   - Configurar PIN de acceso rápido
   - Completar perfil de usuario

2. **💰 Configuración Inicial**
   - Seleccionar moneda principal
   - Crear primera cuenta
   - Establecer metas financieras

3. **📊 Dashboard Principal**
   - Vista general de finanzas
   - Gráficos de ingresos/gastos
   - Resumen de cuentas activas

### 🏦 Gestión de Cuentas

**Cuentas Principales**
- Crear y gestionar cuentas bancarias
- Seguimiento de saldos
- Historial de movimientos

**Subcuentas**
- 🏪 **Subcuentas de Negocio**: Independientes para fuentes de ingresos
- 👤 **Subcuentas Personales**: Vinculadas para organización de dinero
- 💸 Transferencias entre subcuentas
- 🎯 Establecimiento de metas por subcuenta

### 📋 Reportes y Análisis

**Tipos de Reportes**
- 📄 **PDF**: Reportes profesionales para impresión
- 📊 **Excel**: Datos detallados para análisis
- 📈 **CSV**: Exportación de datos para herramientas externas

**Análisis Disponibles**
- Tendencias de ingresos y gastos
- Comparativas por períodos
- Estadísticas de cuentas y subcuentas
- Progreso de metas financieras

### 🔔 Notificaciones

**Configuración de Alertas**
- Alertas por email automáticas
- Recordatorios de metas
- Notificaciones de movimientos importantes
- Alertas personalizadas

### 🎓 Educación Financiera

- Recursos educativos integrados
- Tips y consejos financieros
- Guías de buenas prácticas
- Contenido adaptado al perfil del usuario

---

## 🛠️ Tecnologías

### 🖥️ Backend
- **🐍 Python 3.12.7** - Lenguaje de programación
- **🌐 Django 5.2** - Framework web
- **🐘 PostgreSQL** - Base de datos principal
- **📁 SQLite** - Base de datos de desarrollo

### 🎨 Frontend
- **🎨 HTML5/CSS3** - Estructura y estilos
- **⚡ JavaScript** - Interactividad
- **🎯 Bootstrap/Tailwind** - Framework CSS
- **📊 Chart.js** - Gráficos interactivos

### 📊 Librerías y Herramientas
- **📄 ReportLab** - Generación de PDF
- **📊 openpyxl** - Manejo de archivos Excel
- **🔐 Django Authentication** - Sistema de autenticación
- **📧 Django Email** - Sistema de emails
- **🎨 Pillow** - Procesamiento de imágenes
- **📱 Django Messages** - Sistema de mensajes

### 🔧 Desarrollo
- **🔧 Git** - Control de versiones
- **📝 VSCode** - Editor recomendado
- **🔍 Django Debug Toolbar** - Herramientas de desarrollo
- **✅ Django Testing** - Suite de pruebas

## 👥 Colaboradores

### 🎓 **Equipo de Desarrollo**

| Colaborador | Rol | Contribución |
|-------------|-----|--------------|
| **👨‍💻 Sebas** | Desarrollador Frontend | Interfaces de usuario, experiencia UX |
| **👨‍💻 Junior** | Desarrollador Backend | Lógica de negocio, APIs |
| **👨‍💻 Ordoñez** | Desarrollador Full Stack | Integración frontend-backend |
| **👨‍💻 Josué** | Desarrollador Backend | Base de datos, optimización |

### 👨‍🏫 **Supervisión Académica**
- **👨‍🏫 Docente Villegas** - *Supervisor del Proyecto*

### 🤝 **Contribuir al Proyecto**

¡Las contribuciones son bienvenidas! Para contribuir:

1. 🍴 Fork el proyecto
2. 🌿 Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. 💾 Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. 📤 Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. 🔄 Abre un Pull Request

### 📞 **Contacto**
- 📧 Email del proyecto: [fingest@proyecto.edu](mailto:fingest@proyecto.edu)
- 🐛 Reportar bugs: [Issues](https://github.com/tu-usuario/FinGest/issues)
- 💡 Sugerencias: [Discussions](https://github.com/tu-usuario/FinGest/discussions)

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

```
MIT License

Copyright (c) 2024 FinGest Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🙏 Agradecimientos

- 🎓 **Universidad**: Por el apoyo académico y recursos
- 🌍 **Comunidad Open Source**: Por las herramientas y librerías utilizadas
- 👥 **Beta Testers**: Por sus valiosos comentarios y sugerencias
- 🎯 **ODS**: Por inspirar el enfoque social del proyecto

---

## 📊 Estado del Proyecto

![Desarrollo](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow.svg)
![Cobertura](https://img.shields.io/badge/Tests-En%20Progreso-orange.svg)
![Documentación](https://img.shields.io/badge/Docs-Actualizada-green.svg)

### 🔄 **Versión Actual**: v1.0.0-beta
### 📅 **Última Actualización**: Diciembre 2024
### 🎯 **Próxima Release**: Q1 2025

---

<div align="center">

**⭐ Si este proyecto te ayuda, ¡dale una estrella! ⭐**

*Desarrollado con ❤️ por el equipo FinGest*

[🏠 Inicio](#-fingest---sistema-de-gestión-financiera) • [📋 Características](#-características-principales) • [🚀 Instalación](#-instalación) • [📚 Uso](#-guía-de-uso) • [👥 Equipo](#-colaboradores)

</div>
