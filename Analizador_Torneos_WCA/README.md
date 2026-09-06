# 📊 Analizador de Torneos WCA Live

Herramienta avanzada en Python para generar **informes ejecutivos globales en PDF** sobre torneos oficiales de speedcubing registrados en **WCA Live**.

---

## 🎯 Descripción General

El **Analizador de Torneos WCA** se conecta a la **Nueva API WCA Live** (`/api/v1/competitions/{id}/live/rounds`), a la API clásica GraphQL de WCA Live y a la API oficial de WCA para recolectar, procesar y presentar estadísticas globales de una competencia: distribución de participantes, récords batidos, promedios generales y análisis detallado evento por evento.

---

## ✨ Características Principales

- **Compatibilidad Dual con APIs Live:** Compatible con la **Nueva API Live oficial de WCA** y con el sistema clásico de **WCA Live GraphQL** (`live.worldcubeassociation.org`).
- **Resolución Automática de Identificadores:** Acepta tanto IDs alfanuméricos oficiales (ej. `SouthOmahaScramble2026`) como IDs numéricos clásicos (ej. `11003`).
- **Resumen Ejecutivo:**
  - Cantidad total de competidores y categorías disputadas.
  - Gráfico circular de distribución de competidores por categoría (paleta de 20 colores de alto contraste).
  - Tasa global de resoluciones completadas vs. DNF/DNS.
  - Conteo total de récords personales (Single y Average).
- **Análisis Detallado por Categoría:**
  - Single más rápido y más lento (con nombre del competidor).
  - Average más rápido y más lento (con nombre del competidor).
  - Promedio global de tiempos (excluyendo DNFs/DNSs).
  - Curva de densidad estadística de tiempos (KDE).
  - Ratio de completación por evento.
  - Soporte para formatos especiales como **FMC (333fm)** y **Multi-Blind (333mbf)**.
- **Exportación en PDF Profesional:** Formato tipo reporte ejecutivo multipágina.

---

## 📦 Requisitos e Instalación

### Requisitos Previos
- Python 3.8 o superior

### Instalación de Dependencias
```bash
pip install -r requirements.txt
```

*Dependencias incluidas:* `requests`, `reportlab`, `matplotlib`, `numpy`, `python-dateutil`.

---

## 🚀 Modo de Uso

Ejecuta el script principal indicando el ID de la competencia (alfanumérico o numérico):

```bash
python main.py [ID_DE_COMPETENCIA] [OPCIONES]
```

### Opciones Disponibles:
- `ID_DE_COMPETENCIA`: ID oficial del torneo (ej. `SouthOmahaScramble2026`) o ID numérico en WCA Live (ej. `11003`).
- `--live`: Forzar consulta a los sistemas Live (Nueva API Live o Live clásico).
- `--wca`: Consultar directamente resultados oficiales publicados en la API REST v0.
- `-o, --output`: Especifica la carpeta o ruta de destino del PDF.

### Ejemplos Prácticos
```bash
# Analizar torneo con ID 9645
python main.py 9645

# Guardar en una carpeta específica
python main.py 9645 -o ./reportes_torneos

# Modo detallado
python main.py 9645 -v
```

---

## 🗂️ Estructura del Módulo

```
Analizador_Torneos_WCA/
├── main.py                 # Script de entrada CLI
├── requirements.txt        # Dependencias del proyecto
├── config/                 # Configuración general y constantes
├── src/
│   ├── api/                # Cliente GraphQL para WCA Live
│   ├── models/             # Estructuras y modelos de datos
│   ├── analyzers/          # Motor de cálculos estadísticos
│   ├── charts/             # Generador de gráficos con Matplotlib
│   └── exporters/          # Generador de documentos PDF con ReportLab
└── output/                 # Carpeta de destino de los informes generados
```
