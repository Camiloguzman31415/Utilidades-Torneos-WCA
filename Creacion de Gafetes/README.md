# 🪪 Generador de Gafetes y Credenciales WCA

Herramienta en Python para la **generación automatizada de gafetes / credenciales personalizadas** para todos los competidores registrados en un torneo de la World Cube Association (WCA).

---

## 🎯 Descripción General

Este módulo automatiza la creación de escarapelas/gafetes oficiales para torneos de la WCA. Lee una plantilla base en PDF (`Plantilla Gafete.pdf`), consulta la lista de competidores y sus récords personales (PRs) oficiales mediante la API de la WCA, y genera un documento PDF final listo para imprimir con la información individual de cada participante ordenada alfabéticamente.

---

## ✨ Características Principales

- **Integración con la API Oficial de WCA:** Descarga automática de la lista de registros aprobados y sus mejores marcas personales (Single y Average).
- **Personalización Completa:**
  - Nombre completo del competidor.
  - WCA ID (o indicación de primerizo/nuevo competidor).
  - País / Representación.
  - Tabla formateada con los PRs actuales en los eventos en los que participa.
- **Superposición Dinámica:** Monta la información vectorial sobre la plantilla de diseño base (`Plantilla Gafete.pdf`).
- **Orden Alfabetizado:** Gafetes ordenados alfabéticamente por apellido/nombre para facilitar la entrega durante el registro del torneo.
- **Auto-instalación de dependencias:** El script verifica y descarga automáticamente librerías faltantes si es necesario.

---

## 📦 Requisitos e Instalación

### Requisitos Previos
- Python 3.8 o superior
- Plantilla base en PDF (`Plantilla Gafete.pdf`) colocada en la misma carpeta del script.

### Instalación de Dependencias
```bash
pip install -r requirements.txt
```
*O individualmente:*
```bash
pip install requests pandas reportlab PyPDF2 pymupdf
```

---

## 🚀 Modo de Uso

1. Coloca tu archivo de diseño base llamado `Plantilla Gafete.pdf` en la carpeta `Creacion de Gafetes/`.
2. Ejecuta el script:
   ```bash
   python creacion_de_gafetes.py
   ```
3. El programa te solicitará el identificador del torneo en la WCA:
   ```text
   Ingrese el competition_id de la WCA: DelacuestaPrs2026
   ```
4. El script procesará todos los competidores y generará un archivo con el nombre:
   `gafetes_final_<competition_id>.pdf`

---

## 🗂️ Estructura del Módulo

```
Creacion de Gafetes/
├── creacion_de_gafetes.py     # Script principal de generación
├── Plantilla Gafete.pdf       # Plantilla PDF base de diseño
├── requirements.txt           # Dependencias requeridas
└── README.md                  # Documentación del módulo
```
