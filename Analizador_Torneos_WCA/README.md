# 📊 Analizador de Torneos WCA Live

Herramienta avanzada en Python para generar **informes ejecutivos globales en PDF** sobre torneos oficiales de speedcubing registrados en **WCA Live**.

---

## 🎯 Descripción General

El **Analizador de Torneos WCA** se conecta a la API GraphQL de WCA Live para recolectar, procesar y presentar estadísticas globales de una competencia: distribución de participantes, récords batidos, promedios generales y análisis detallado evento por evento.

---

## ✨ Características Principales

- **Conexión GraphQL en Tiempo Real:** Extracción directa de datos actualizados desde `live.worldcubeassociation.org`.
- **Resumen Ejecutivo:**
  - Cantidad total de competidores y categorías disputadas.
  - Gráfico circular de distribución de competidores por categoría (paleta de 20 colores de alto contraste).
  - Tasa global de resoluciones completadas vs. DNF/DNS.
  - Conteo total de récords personales (Single y Average).
- **Análisis Detallado por Categoría:**
  - Single más rápido y más lento (con nombre del competidor).
  - Average más rápido y más lento (con nombre del competidor).
  - Promedio global de tiempos (excluyendo DNFs/DNSs).
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

*Dependencias incluidas:* `requests`, `reportlab`, `matplotlib`, `python-dateutil`.

---

## 🚀 Modo de Uso

Ejecuta el script principal indicando el ID de la competencia en WCA Live:

```bash
python main.py [ID_DE_COMPETENCIA] [OPCIONES]
```

### Opciones Disponibles:
- `ID_DE_COMPETENCIA`: ID numérico que aparece en la URL de WCA Live (`https://live.worldcubeassociation.org/competitions/<ID>`).
- `-o, --output`: Especifica la carpeta o ruta de destino del PDF.
- `-v, --verbose`: Muestra información técnica detallada en la consola durante el procesamiento.

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
