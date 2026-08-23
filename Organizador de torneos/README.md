# 🏆 Organizador de Torneos WCA (Web Hub)

Aplicación web interactiva *Single Page Application* (SPA) diseñada para asistir a organizadores y delegados en la planificación de competencias y el análisis estadístico de la **World Cube Association (WCA)**.

---

## 🎯 Descripción General

El **Organizador de Torneos** es una herramienta integral en HTML5, CSS3 y JavaScript moderno que funciona directamente en el navegador sin requerir servidores locales ni configuraciones complejas. Ofrece utilidades clave para la gestión de torneos y el análisis de rendimiento por país.

---

## ✨ Módulos y Herramientas Integradas

### 1. 🌐 Country Averages (Promedios Nacionales por Evento)
- Consulta y calcula el promedio oficial en los **17 eventos oficiales de la WCA** para cualquier país y año seleccionado.
- Analiza todas las soluciones válidas de todas las competencias disputadas durante el periodo.
- Ejecución asíncrona mediante un *pool* concurrente con reintentos y tolerancia a límites de tasa de la API de la WCA.
- Visualización en tablas interactivas con tiempos formateados e iconografía oficial.

### 2. 📅 Asistente de Planificación de Competencias (Tournament Organizer)
Flujo guiado paso a paso para estructurar una competencia oficial según el reglamento de la WCA:
- **Paso 1 - Información General:** Nombre del torneo, delegados asignados, organizadores, fechas, sede/ubicación, límite de competidores y tarifas de inscripción.
- **Paso 1.5 - Avisos y Requisitos:** Plantillas de texto y reglas informativas con previsualización bilingüe/multilingüe.
- **Paso 2 - Configuración de Categorías y Rondas:**
  - Selección de eventos a disputar.
  - Definición de rondas por evento (Ronda 1, Semifinal, Final).
  - Formato de cada ronda: *Best of 1/2/3*, *Mean of 3*, *Average of 5*.
  - Configuración de *Cutoffs* (tiempos límite de clasificación), *Time Limits* estándar y *Cumulative Limits*.
  - Porcentaje o cantidad fija de clasificados a rondas posteriores.
- **Paso 3 - Cronograma y Exportación:** Estructuración de horarios y exportación de datos lista para cargar a la plataforma oficial de la WCA.

---

## 📦 Requisitos e Instalación

- **Sin dependencias externas ni instalación previa.**
- Solo necesitas un navegador web moderno (Google Chrome, Mozilla Firefox, Microsoft Edge, Safari, Brave, etc.).

---

## 🚀 Modo de Uso

1. Abre directamente el archivo `Organizador de torneos.html` haciendo doble clic o arrastrándolo a tu navegador preferido.
2. Selecciona la herramienta que deseas utilizar desde el panel principal:
   - Haz clic en **Country Averages** para consultar estadísticas nacionales.
   - Haz clic en **Tournament Organizer** para iniciar el asistente de configuración de un nuevo torneo.
