# ⚔️ Generador de Fixtures y Torneos WCA

Aplicación web interactiva *standalone* (SPA) para generar, gestionar y exportar **cuadros de eliminación directa (brackets)** y **formatos de liga (todos contra todos)** para torneos oficiales o paralelos de speedcubing.

---

## 🎯 Descripción General

El **Generador de Fixtures WCA** permite importar competidores directamente desde cualquier torneo registrado en la WCA mediante su ID (utilizando el endpoint público WCIF), seleccionar participantes individuales o armar equipos, configurar el sistema de emparejamiento con semillas criptográficas o manuales, disputar los enfrentamientos interactivamente y exportar el resultado final a PDF de alta resolución.

---

## ✨ Características Principales

### 1. 📥 Importación Oficial desde WCA
- Conexión directa a la API de la WCA mediante el ID de la competencia (ej. `NorthwestChampionship2026`).
- Filtrado automático de competidores aceptados con su respectivo WCA ID y número de registro.
- Selector de competidores con checkboxes, selección masiva (*Todos/Ninguno*) y selección aleatoria de \(N\) participantes.

### 2. 👥 Modos de Competencia
- **Individual:** Cada competidor compite por su propia cuenta.
- **Por Equipos (Team Builder):**
  - Creación de equipos personalizados de 2 a 4 integrantes.
  - Asignación manual o generación automática y balanceada de equipos al azar.
  - Validación de integrantes únicos y cálculo de identificadores de desempate acumulados.

### 3. 🏟️ Formatos de Torneo Soportados
- **Eliminación Directa (Brackets):**
  - Soporte de cualquier cantidad de participantes de **2 a 64+** (tanto potencias de 2 exactas como números arbitrarios con distribución uniforme de *BYEs* o *Ronda Preliminar*).
  - Partido opcional por el **3er Puesto**.
  - Avance interactivo con un solo clic al ganador de cada enfrentamiento y botón para **deshacer (Undo)**.
  - Dos modos de visualización: **March Madness Horizontal (SVG)** y **Bracket Vertical**.
  - Detección automática del campeón, animación de confeti y podio con medallas de Oro 🥇, Plata 🥈 y Bronce 🥉.
- **Formato Liga (Todos contra Todos / Round Robin):**
  - Generación automática de todas las jornadas y enfrentamientos.
  - Tabla de posiciones en tiempo real (*Standings*) con partidos jugados (PJ), ganados (G), puntos (Pts) y desempate por *registrantId*.
  - Panel lateral con tabla fija (*sticky*) y lista de partidos con *scroll* optimizado para torneos multitudinarios (hasta 2.000+ partidos).

### 4. 🎲 Sistema de Semillas y Aleatoriedad
- **Semilla Automática (Auto Seed):** Generada mediante `window.crypto.getRandomValues` para garantizar aleatoriedad real sin sesgo.
- **Semilla Manual:** Permite introducir una cadena de bits binarios (ej. `10101100`) para replicar fixtures idénticos de manera determinista y transparente ante los competidores.

### 5. 📄 Exportación a PDF
- Exportación vectorial directa del fixture completo, incluyendo el cuadro principal, el partido por el 3.º puesto y la tabla de podio final en formato A4 apaisado.

---

## 📦 Requisitos e Instalación

- **Sin dependencias externas ni instalación previa.**
- Solo necesitas abrir el archivo `wca-fixture-standalone.html` en cualquier navegador web moderno (Google Chrome, Firefox, Edge, Safari, Brave, Opera, etc.).

---

## 🚀 Modo de Uso

1. Abre `wca-fixture-standalone.html` en tu navegador.
2. Ingresa el **WCA Competition ID** (por ejemplo: `NorthwestChampionship2026`).
3. Elige el **Modo de Competencia** (Individual o Equipos) y el **Formato** (Eliminación Directa o Liga).
4. Selecciona los competidores o arma los equipos.
5. Configura la semilla y orientación (si aplica).
6. ¡Haz clic en los ganadores en tiempo real a medida que se jueguen los enfrentamientos y exporta el PDF al finalizar!
