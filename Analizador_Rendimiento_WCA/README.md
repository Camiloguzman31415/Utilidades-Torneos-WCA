# 📈 Analizador de Rendimiento WCA

Herramienta en Python para generar informes ejecutivos e individuales en formato PDF sobre el desempeño y progreso de un competidor en un torneo oficial de la **World Cube Association (WCA)**.

---

## 🎯 Descripción General

El **Analizador de Rendimiento WCA** extrae datos en tiempo real mediante las APIs de **WCA Live** y la **WCA Official API**, generando un informe detallado por competidor que resume sus resultados, récords personales obtenidos durante la competencia, gráficos de progresión histórica y métricas de consistencia.

---

## ✨ Características Principales

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

Ejecuta el script indicando el **ID de la competencia** en WCA Live y el **ID de registro** del competidor:

```bash
python main.py <competition_id> <registration_id> [nombre_archivo_salida.pdf]
```

### Parámetros:
- `<competition_id>`: Identificador numérico de la competencia en WCA Live (ej. `9678`).
- `<registration_id>`: Identificador numérico del competidor dentro del torneo en WCA Live (ej. `856510`).
- `[nombre_archivo_salida.pdf]` *(Opcional)*: Ruta o nombre del archivo PDF generado. Si no se especifica, se guardará en la carpeta `output/`.

### Ejemplo Práctico
```bash
# Generar informe para un competidor específico
python main.py 9678 856510

# Especificar un nombre personalizado para el PDF
python main.py 9678 856510 "Informe_Haiver_Reyes.pdf"
```

---

## 📊 Estructura del Informe Generado

1. **Encabezado y Portada:** Información personal y resumen del torneo.
2. **Tabla de Resultados:** Desglose por evento, ronda, tiempos individuales y promedio.
3. **Sección de Records:** Lista destacada de nuevos PRs establecidos.
4. **Gráfico Evolutivo:** Curva de tiempos en competiciones anteriores.
5. **Estadísticas de Constancia:** Días desde el último récord por categoría.
