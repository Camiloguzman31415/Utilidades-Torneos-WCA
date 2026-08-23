# 🧩 Utilidades Torneos WCA

Colección integral de herramientas, utilidades y scripts automatizados para la organización, gestión, análisis estadístico y producción gráfica de torneos oficiales de speedcubing avalados por la **World Cube Association (WCA)**.

---

## 📌 Tabla de Contenidos

1. [Visión General](#-visión-general)
2. [Herramientas Incluidas](#-herramientas-incluidas)
   - [1. Analizador de Torneos WCA Live](#1--analizador-de-torneos-wca-live)
   - [2. Analizador de Rendimiento WCA](#2--analizador-de-rendimiento-wca)
   - [3. Creación de Gafetes y Credenciales](#3--creación-de-gafetes-y-credenciales)
   - [4. Creación de Medallas](#4--creación-de-medallas)
   - [5. Organizador de Torneos (Hub Web)](#5--organizador-de-torneos-hub-web)
   - [6. Calculadora Sum of Ranks (SoR)](#6--calculadora-sum-of-ranks-sor)
3. [Requisitos Globales e Instalación](#-requisitos-globales-e-instalación)
4. [Estructura del Repositorio](#-estructura-del-repositorio)
5. [Tecnologías Utilizadas](#-tecnologías-utilizadas)
6. [Licencia](#-licencia)

---

## 🎯 Visión General

Organizar y gestionar competencias de cubos de Rubik requiere coordinar múltiples aspectos: desde la planificación de horarios y rondas, hasta la acreditación de competidores, la confección de medallas y el análisis post-torneo. 

Este repositorio reúne **6 módulos especializados** desarrollados para cubrir cada una de estas etapas de forma automatizada y profesional, interactuando directamente con las APIs oficiales de la WCA y WCA Live.

---

## 🛠️ Herramientas Incluidas

### 1. 📊 [Analizador de Torneos WCA Live](./Analizador_Torneos_WCA/)
- **Ubicación:** `Analizador_Torneos_WCA/`
- **Utilidad:** Genera un **informe ejecutivo global en PDF** sobre una competencia completa a partir de su ID en WCA Live.
- **Funcionalidades:**
  - Resumen ejecutivo con métricas de participación y tasas de completación.
  - Gráfico circular de distribución de competidores por categoría (paleta distintiva de 20 colores).
  - Análisis detallado por categoría: mejores/peores marcas (Single y Average), promedios de la competencia sin DNF, y récords alcanzados.
  - Soporte de eventos especiales (FMC, Multi-Blind).
- **Ejecución:** `python main.py <ID_WCA_LIVE>`

---

### 2. 📈 [Analizador de Rendimiento WCA](./Analizador_Rendimiento_WCA/)
- **Ubicación:** `Analizador_Rendimiento_WCA/`
- **Utilidad:** Genera un **informe individual en PDF** con el análisis de desempeño de un competidor específico en un torneo.
- **Funcionalidades:**
  - Desglose de resultados por ronda y posición alcanzada.
  - Detección de nuevos Récords Personales (PRs).
  - Gráficos de progresión histórica a través de torneos previos.
  - Estadísticas de constancia (días transcurridos desde el último récord por categoría).
- **Ejecución:** `python main.py <competition_id> <registration_id>`

---

### 3. 🪪 [Creación de Gafetes y Credenciales](./Creacion%20de%20Gafetes/)
- **Ubicación:** `Creacion de Gafetes/`
- **Utilidad:** Automatiza la generación e impresión de **escarapelas / credenciales personalizadas** para todos los competidores registrados.
- **Funcionalidades:**
  - Descarga automática de la lista de registros y récords vigentes (Single/Average) desde la API oficial de WCA.
  - Montaje dinámico de nombres, WCA ID, país y marcas personales sobre la plantilla base (`Plantilla Gafete.pdf`).
  - Ordenamiento alfabético para facilitar la entrega durante el registro.
- **Ejecución:** `python creacion_de_gafetes.py`

---

### 4. 🥇 [Creación de Medallas](./Creacion%20de%20Medallas/)
- **Ubicación:** `Creacion de Medallas/`
- **Utilidad:** Diseña y exporta en PDF **plantillas de medallería cuadradas (1080x1080 px)** para premiación en podios.
- **Funcionalidades:**
  - Diseños diferenciados para 1.º (Oro), 2.º (Plata) y 3.º (Bronce) lugar.
  - Soporte para los 17 eventos oficiales de la WCA y más de 30 eventos no oficiales (FTO, Relays, Mirror, Team BLD, etc.).
  - Integración de logo del torneo, logotipos de patrocinadores y fondo personalizado.
  - Renderizado de pictogramas de cubos mediante `@cubing/icons`.
- **Ejecución:** `python wca_medal_generator.py`

---

### 5. 🏆 [Organizador de Torneos (Hub Web)](./Organizador%20de%20torneos/)
- **Ubicación:** `Organizador de torneos/`
- **Utilidad:** Aplicación web moderna (SPA) para planificación de torneos y análisis estadístico por países.
- **Funcionalidades:**
  - **Country Averages:** Calcula los promedios oficiales de todos los eventos WCA en cualquier país para un año específico.
  - **Asistente de Torneos (Wizard):** Planificación guiada de competencias (fechas, sedes, delegados, rondas, cutoffs, límites de tiempo acumulados y cronogramas).
  - No requiere servidor ni backend: se ejecuta en cualquier navegador moderno.
- **Ejecución:** Abrir `Organizador de torneos.html` en el navegador.

---

### 6. 🧮 [Calculadora Sum of Ranks (SoR)](./SoR%20WCA/)
- **Ubicación:** `SoR WCA/`
- **Utilidad:** Calcula la clasificación general acumulada (**Sum of Ranks**) para determinar el mejor competidor integral (*All-Rounder*) del torneo.
- **Funcionalidades:**
  - **Modo 1:** Torneos finalizados (WCA API / Export).
  - **Modo 2:** Torneos en vivo (WCA Live GraphQL).
  - Genera un reporte PDF con la tabla general de posiciones y el reglamento de cálculo aplicado.
- **Ejecución:** `python sor_wca_unificado.py`

---

## 📦 Requisitos Globales e Instalación

### Entorno Recomendado
- **Python 3.8 o superior**
- **Navegador web moderno** (para el Organizador Web)

### Instalación de Dependencias de Python
Puedes instalar los paquetes principales utilizados por las herramientas ejecutando:

```bash
pip install requests reportlab matplotlib numpy pandas PyPDF2 pymupdf pillow cairosvg python-dateutil
```

*(Cada módulo cuenta además con su propio archivo `requirements.txt` o autoinstalador integrado).*

---

## 🗂️ Estructura del Repositorio

```text
Utilidades Torneos WCA/
├── README.md                          # Documentación general del repositorio
├── .gitignore                         # Archivos ignorados por Git
│
├── Analizador_Rendimiento_WCA/        # Informes individuales de competidores
│   ├── main.py
│   └── README.md
│
├── Analizador_Torneos_WCA/            # Informes globales ejecutivos de torneos
│   ├── main.py
│   ├── requirements.txt
│   ├── src/
│   ├── config/
│   └── README.md
│
├── Creacion de Gafetes/               # Generador de credenciales con PRs
│   ├── creacion_de_gafetes.py
│   ├── Plantilla Gafete.pdf
│   ├── requirements.txt
│   └── README.md
│
├── Creacion de Medallas/              # Generador de medallas (1080x1080)
│   ├── wca_medal_generator.py
│   ├── requirements.txt
│   ├── README.md
│   ├── logo/
│   ├── patrocinadores/
│   ├── fondo/
│   ├── fonts/
│   └── cubing_icons/
│
├── Organizador de torneos/            # Hub web: Averages por país y creador de torneos
│   ├── Organizador de torneos.html
│   └── README.md
│
└── SoR WCA/                           # Calculadora Sum of Ranks (Live y Export)
    ├── sor_wca_unificado.py
    ├── requirements.txt
    ├── .env.example
    └── README.md
```

---

## 💻 Tecnologías Utilizadas

- **Lenguajes:** Python 3, JavaScript (ES6+), HTML5, CSS3.
- **APIs:** WCA REST API v0, WCA Live GraphQL API.
- **Librerías de Procesamiento y PDF:** ReportLab, PyMuPDF (fitz), PyPDF2, Pillow, CairoSVG.
- **Ciencia de Datos y Gráficos:** Matplotlib, Pandas, NumPy.
- **Iconografía y Tipografía:** `@cubing/icons`, Bebas Neue, Space Mono, DM Sans.

---

## 📄 Licencia

Este proyecto está disponible para la comunidad de speedcubing y organizadores de torneos WCA para uso abierto y educativo.
