# 🥇 Generador de Medallería WCA

Generador automatizado en Python para el diseño y exportación de **plantillas de medallas personalizadas** para torneos de speedcubing oficiales y no oficiales de la WCA.

---

## 🎯 Descripción General

Este módulo genera un documento PDF de alta resolución con plantillas cuadradas de **1080 × 1080 px** por hoja, listas para producción gráfica e impresión en medallas o reconocimientos para premiación en torneos de speedcubing.

---

## ✨ Características Principales

- **Diseño por Posición en Podio:**
  - 🥇 **Primer Lugar:** Esquema dorado (#FFD700 / #FFFACD / #B8860B).
  - 🥈 **Segundo Lugar:** Esquema plateado (#C0C0C0 / #F8F8F8 / #707070).
  - 🥉 **Tercer Lugar:** Esquema bronce (#CD7F32 / #FDF0E0 / #8B4513).
- **Soporte Completo de Eventos:**
  - Todos los 17 eventos oficiales de la WCA (3x3x3, 2x2x2, 4x4x4, Blindfolded, Megaminx, Pyraminx, etc.).
  - Más de 30 eventos no oficiales populares (FTO, Relays, Mirror Blocks, Mini Guildford, Match the Scramble, Siameses, Team BLD, etc.).
- **Integración de Marca y Patrocinadores:**
  - Logo oficial del torneo (`logo/`).
  - Múltiples logotipos de patrocinadores alineados automáticamente (`patrocinadores/`).
  - Fondo visual personalizado (`fondo/`).
- **Iconografía Oficial de Cubing:**
  - Utiliza la fuente de iconos `@cubing/icons` para renderizar el pictograma correspondiente a cada evento.
- **Tipografía Personalizable:**
  - Soporte para fuentes personalizadas (incluye Bebas Neue en `fonts/`).

---

## 📦 Requisitos e Instalación

### Requisitos Previos
- Python 3.8 o superior

### Instalación de Dependencias de Python
```bash
pip install -r requirements.txt
```
*O manualmente:*
```bash
pip install pillow reportlab requests cairosvg
```

---

## 📁 Estructura de Recursos Requerida

El script busca los siguientes recursos en sus subdirectorios respectivos:

```
Creacion de Medallas/
├── wca_medal_generator.py      # Script principal
├── requirements.txt            # Dependencias de Python
├── README.md                   # Documentación del módulo
├── logo/                       # Imagen con el logo del torneo (PNG/JPG)
├── patrocinadores/             # Imágenes con logos de patrocinadores (PNG)
├── fondo/                      # Fondo decorativo (PNG)
├── fonts/                      # Fuentes personalizadas (.woff2, .ttf)
└── cubing_icons/               # CSS y fuente de iconos de eventos (@cubing/icons)
```

---

## 🚀 Modo de Uso

1. Coloca los recursos gráficos del torneo en las carpetas `logo/`, `patrocinadores/` y `fondo/`.
2. Ejecuta el script:
   ```bash
   python wca_medal_generator.py
   ```
3. Sigue las instrucciones interactivas en pantalla para seleccionar el torneo y los eventos a premiar.
4. El archivo PDF final se generará con las medallas de 1.º, 2.º y 3.º puesto para cada categoría seleccionada.
