# 📈 Analizador de Rendimiento WCA

Herramienta en Python para generar informes ejecutivos e individuales en formato PDF sobre el desempeño y progreso de un competidor en un torneo oficial de la **World Cube Association (WCA)**.

---

## 🎯 Descripción General

El **Analizador de Rendimiento WCA** extrae datos en tiempo real mediante la **Nueva API WCA Live** (`/api/v1/competitions/{id}/live/rounds`), la API clásica **WCA Live GraphQL** y la **WCA Official API (v0)**, generando un informe detallado por competidor que resume sus resultados, récords personales obtenidos durante la competencia, gráficos de progresión histórica y métricas de consistencia.

---

## ✨ Características Principales

- **Compatibilidad Dual de APIs Live:** Soporta automáticamente tanto la **Nueva API Live oficial de WCA** como el sistema clásico de **WCA Live GraphQL**, con detección y resolución transparente de identificadores.
- **Ficha del Competidor:** Nombre completo, WCA ID, país/representación y número de registro.
- **Resumen de Resultados:** Tiempos obtenidos (Single y Average), posición alcanzada por ronda y categoría.
- **Detección de Personal Records (PRs):** Identificación visual de récords personales superados en el evento.
- **Gráficos de Tendencia Histórica:** Evolución gráfica del rendimiento a lo largo de los últimos torneos oficiales (mediante `matplotlib`).
- **Métricas de Progreso:** Días transcurridos desde el último PR por cada evento disputado.
- **Exportación en PDF:** Documento profesional listo para imprimir o compartir digitalmente.

---

## 📦 Requisitos e Instalación

### Requisitos Previos
- Python 3.8 o superior
- Conexión a Internet activa

### Instalación de Dependencias
```bash
pip install reportlab matplotlib numpy requests
```

---

## 🚀 Modo de Uso

Ejecuta el script indicando el **ID de la competencia** (alfanumérico o numérico) y el **ID / WCA ID** del competidor:

```bash
python main.py <competition_id> <competitor_id> [nombre_archivo_salida.pdf]
```

### Parámetros:
- `<competition_id>`: ID alfanumérico oficial (ej. `SouthOmahaScramble2026`) o ID numérico clásico en WCA Live (ej. `11003`).
- `<competitor_id>`: WCA ID del competidor (ej. `2018KEEN04`), ID de registro o ID numérico dentro del torneo.
- `[nombre_archivo_salida.pdf]` *(Opcional)*: Ruta o nombre del archivo PDF generado.

### Ejemplos Prácticos
```bash
# Con ID oficial de WCA y WCA ID de competidor
python main.py SouthOmahaScramble2026 2018KEEN04

# Con ID numérico clásico de WCA Live
python main.py 11003 952155 "Informe_Jayben_Keene.pdf"
```

---

## 📊 Estructura del Informe Generado

1. **Encabezado y Portada:** Información personal y resumen del torneo.
2. **Tabla de Resultados:** Desglose por evento, ronda, tiempos individuales y promedio.
3. **Sección de Records:** Lista destacada de nuevos PRs establecidos.
4. **Gráfico Evolutivo:** Curva de tiempos en competiciones anteriores.
5. **Estadísticas de Constancia:** Días desde el último récord por categoría.
