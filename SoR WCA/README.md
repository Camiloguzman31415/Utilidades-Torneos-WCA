# 🏆 Calculadora Sum of Ranks (SoR) WCA

Calculadora unificada en Python para determinar la clasificación **Sum of Ranks (SoR)** de competidores en torneos oficiales de la **World Cube Association (WCA)**.

---

## 🎯 ¿Qué es Sum of Ranks (SoR)?

El **Sum of Ranks (SoR)** es una métrica competitiva integral que evalúa la versatilidad de un competidor sumando las posiciones (rankings) obtenidas en todas las categorías del torneo. A menor puntuación total, mejor es el desempeño general del competidor en el certamen (similar a la clasificación del *All-Rounder*).

---

## ✨ Características Principales

- **Dos Modos de Operación Unificados:**
  1. **Modo 1 - WCA Export (Competencias Finalizadas):** Consulta los resultados oficiales consolidados a través de la API REST de la WCA.
  2. **Modo 2 - WCA Live (Competencias en Curso / En Vivo):** Extrae los resultados en tiempo real conectándose automáticamente a la **Nueva API WCA Live** (`/live/rounds`) o a la API GraphQL de **WCA Live clásico** (`live.worldcubeassociation.org`), aceptando tanto WCA IDs alfanuméricos como IDs numéricos.
- **Cálculo Preciso de Posiciones:** Asigna penalizaciones y rankings normalizados para competidores que no participan en determinados eventos según el reglamento de SoR.
- **Exportación en Documento PDF Único:**
  - Hoja informativa con el reglamento y sistema de puntuación aplicado.
  - Tabla completa de clasificación general (*Leaderboard*) con desglose por categoría, puntos y posición final.
- **Soporte Opcional de LaTeX:** Si el sistema cuenta con `pdflatex`, compila automáticamente la sección de reglas en alta calidad tipográfica; en su defecto, utiliza un generador nativo con ReportLab.

---

## 📦 Requisitos e Instalación

### Requisitos Previos
- Python 3.8 o superior

### Instalación de Dependencias
```bash
pip install -r requirements.txt
```
*O individualmente:*
```bash
pip install reportlab pypdf pandas requests
```

*(Opcional para renderizado tipográfico avanzado: distribución LaTeX como TeX Live / MiKTeX / MacTeX).*

---

## 🚀 Modo de Uso

1. Ejecuta el script principal:
   ```bash
   python sor_wca_unificado.py
   ```
2. Selecciona el modo de consulta:
   - `1`: Competencia finalizada (WCA Export).
   - `2`: Competencia en progreso (WCA Live: Nueva Live o Live clásico).
3. Introduce el identificador del torneo cuando sea solicitado (ejemplo: `SouthOmahaScramble2026` o ID numérico `11003`).
4. El programa generará el archivo PDF consolidado con los resultados del SoR.

---

## ⚙️ Configuración Opcional (`.env`)

Para implementaciones automatizadas de servidor o sondeos periódicos, puedes copiar `.env.example` a `.env` y configurar:
- `PORT`: Puerto del servidor web.
- `POLL_INTERVAL_MINUTES`: Minutos entre actualizaciones automáticas de WCA Live.
- `SESSION_SECRET` y credenciales de administración.
