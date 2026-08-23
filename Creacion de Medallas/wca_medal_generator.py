#!/usr/bin/env python3
"""
WCA Medal Template Generator
Genera plantillas de medallería para torneos de la WCA en formato PDF (1080x1080 px por hoja).

Estructura de carpetas esperada junto al script:
  logo/           ← un archivo de imagen (png/jpg) con el logo del torneo
  patrocinadores/ ← uno o más archivos de imagen con logos de patrocinadores

Uso: python3 wca_medal_generator.py
Requiere: pip install pillow reportlab requests cairosvg
          npm install @cubing/icons  (en el mismo directorio)
"""

import math
import os
import re
import sys
import tempfile

import requests
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas as rl_canvas

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
SIZE = 1080   # px del lienzo cuadrado

LUGARES = ["Primer Lugar", "Segundo Lugar", "Tercer Lugar"]

COLORES_MEDALLA = {
    "Primer Lugar":  {"anillo": "#FFD700", "fondo": "#FFFACD", "borde": "#B8860B", "texto": "#7B5900"},
    "Segundo Lugar": {"anillo": "#C0C0C0", "fondo": "#F8F8F8", "borde": "#707070", "texto": "#404040"},
    "Tercer Lugar":  {"anillo": "#CD7F32", "fondo": "#FDF0E0", "borde": "#8B4513", "texto": "#5C2A00"},
}

WCA_EVENTOS = {
    "222":    "Cubo 2x2x2",
    "333":    "Cubo 3x3x3",
    "444":    "Cubo 4x4x4",
    "555":    "Cubo 5x5x5",
    "666":    "Cubo 6x6x6",
    "777":    "Cubo 7x7x7",
    "333bf":  "3x3x3 Vendado",
    "333fm":  "3x3x3 Menos Movimientos",
    "333oh":  "3x3x3 Una Mano",
    "clock":  "Clock",
    "minx":   "Megaminx",
    "pyram":  "Pyraminx",
    "skewb":  "Skewb",
    "sq1":    "Square-1",
    "444bf":  "4x4x4 Vendado",
    "555bf":  "5x5x5 Vendado",
    "333mbf": "3x3x3 Multi-Vendado",
}

WCA_EVENTOS_NO_OFICIALES = {
    "unofficial-222oh":                    "2x2x2 Una Mano",
    "unofficial-222bf":                    "2x2x2 Vendado",
    "unofficial-333_mirror_blocks":        "Mirror Blocks",
    "unofficial-333_mirror_blocks_bld":    "Mirror Blocks Vendado",
    "unofficial-333_linear_fm":            "3x3x3 Menos Movimientos Lineal",
    "unofficial-333_oven_mitts":           "3x3x3 Manoplas de Horno",
    "unofficial-333_siamese":              "Siameses 3x3x3",
    "unofficial-333_speed_bld":            "3x3x3 Speed Vendado",
    "unofficial-333_team_bld":             "3x3x3 Vendado en Equipo",
    "unofficial-333_team_factory":         "Team Factory 3x3x3",
    "unofficial-333mts":                   "3x3x3 Match the Scramble",
    "unofficial-333_oh_bld_relay":         "Relevo 3x3x3 OH Vendado",
    "unofficial-333_oh_bld_team_relay":    "Relevo OH Vendado en Equipo",
    "unofficial-333bf_2_person_relay":     "Relevo 3x3x3 Vendado (2 personas)",
    "unofficial-333bf_3_person_relay":     "Relevo 3x3x3 Vendado (3 personas)",
    "unofficial-333bf_4_person_relay":     "Relevo 3x3x3 Vendado (4 personas)",
    "unofficial-333bf_8_person_relay":     "Relevo 3x3x3 Vendado (8 personas)",
    "unofficial-234relay":                 "Relevo 2x2-4x4",
    "unofficial-2345relay":                "Relevo 2x2-5x5",
    "unofficial-23456relay":               "Relevo 2x2-6x6",
    "unofficial-234567relay":              "Relevo 2x2-7x7",
    "unofficial-234567relay_2_person":     "Relevo 2x2-7x7 (2 personas)",
    "unofficial-444ft":                    "4x4x4 Pies",
    "unofficial-666bf":                    "6x6x6 Vendado",
    "unofficial-777bf":                    "7x7x7 Vendado",
    "unofficial-baby_fto":                 "Baby FTO",
    "unofficial-curvycopter":              "Curvy Copter",
    "unofficial-fisher":                   "Fisher",
    "unofficial-fto":                      "FTO (Octaedro)",
    "unofficial-helicopter":               "Helicopter",
    "unofficial-kilominx":                 "Kilominx",
    "unofficial-magic_oh":                 "Magic Una Mano",
    "unofficial-miniguild":                "Mini Guildford",
    "unofficial-miniguild_2_person":       "Mini Guildford (2 personas)",
    "unofficial-miniguild_bld":            "Mini Guildford Vendado",
    "unofficial-minx_bld":                 "Megaminx Vendado",
    "unofficial-mpyram":                   "Master Pyraminx",
    "unofficial-mskewb":                   "Master Skewb",
    "unofficial-mtetram":                  "Master Tetraminx",
    "unofficial-pyramorphix":              "Pyramorphix",
    "unofficial-redi":                     "Redi",
    "unofficial-sq1_bld":                  "Square-1 Vendado",
}

EXTS_IMAGEN = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# ─────────────────────────────────────────────────────────────────────────────
# FUENTE DE ICONOS WCA (descarga directa desde npm registry, sin Node.js)
# ─────────────────────────────────────────────────────────────────────────────

# Codepoints hardcodeados — no dependen del CSS descargado
_CODEPOINTS_HARDCODED = {
    "222":    0xe900, "333":    0xe901, "444":    0xe902, "555":    0xe903,
    "666":    0xe904, "777":    0xe905, "333bf":  0xe906, "333fm":  0xe907,
    "333oh":  0xe908, "333mbf": 0xe909, "clock":  0xe90a, "minx":   0xe90b,
    "pyram":  0xe90c, "skewb":  0xe90d, "sq1":    0xe90e, "444bf":  0xe90f,
    "555bf":  0xe910,
}

def _dir_iconos():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "cubing_icons")

def _encontrar_woff():
    ruta = os.path.join(_dir_iconos(), "cubing-icons.woff2")
    return ruta if os.path.exists(ruta) else None

def _encontrar_css():
    ruta = os.path.join(_dir_iconos(), "cubing-icons.css")
    return ruta if os.path.exists(ruta) else None

# Buscar tambien en node_modules por compatibilidad
def _encontrar_paquete_icons():
    # Primero carpeta local cubing_icons/
    woff = _encontrar_woff()
    css  = _encontrar_css()
    if woff:
        return woff, css
    # Luego node_modules
    for base in [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]:
        ruta = os.path.join(base, "node_modules", "@cubing", "icons",
                            "dist", "lib", "@cubing", "icons")
        w = os.path.join(ruta, "cubing-icons.woff2")
        c = os.path.join(ruta, "cubing-icons.css")
        if os.path.exists(w):
            return w, (c if os.path.exists(c) else None)
    return None, None


def _descargar_iconos_wca():
    """
    Descarga cubing-icons.woff2 directamente desde el registro de npm.
    No requiere Node.js ni npm instalados.
    """
    import urllib.request, json, tarfile, io

    destino = _dir_iconos()
    os.makedirs(destino, exist_ok=True)
    woff_dest = os.path.join(destino, "cubing-icons.woff2")
    css_dest  = os.path.join(destino, "cubing-icons.css")

    if os.path.exists(woff_dest):
        return True

    print("  📥 Descargando fuente de iconos WCA (sin necesidad de Node.js)...")
    try:
        # 1. Obtener URL del tarball desde el registro npm
        meta_url = "https://registry.npmjs.org/@cubing/icons/latest"
        with urllib.request.urlopen(meta_url, timeout=15) as r:
            meta = json.loads(r.read())
        tarball_url = meta["dist"]["tarball"]

        # 2. Descargar el tarball
        with urllib.request.urlopen(tarball_url, timeout=30) as r:
            data = r.read()

        # 3. Extraer solo los archivos que necesitamos
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("cubing-icons.woff2"):
                    f = tar.extractfile(member)
                    if f:
                        with open(woff_dest, "wb") as out:
                            out.write(f.read())
                        print(f"  ✅ cubing-icons.woff2 descargado.")
                elif member.name.endswith("cubing-icons.css"):
                    f = tar.extractfile(member)
                    if f:
                        with open(css_dest, "wb") as out:
                            out.write(f.read())

        return os.path.exists(woff_dest)

    except Exception as e:
        print(f"  ⚠  No se pudo descargar la fuente de iconos: {e}")
        print(f"     Los eventos se mostraran como texto.")
        return False


def _cargar_codepoints(css_path):
    if not css_path or not os.path.exists(css_path):
        return _CODEPOINTS_HARDCODED
    texto = open(css_path, encoding="utf-8").read()
    # Captura iconos oficiales (event-*) y no oficiales (unofficial-*)
    patron = (r'\.cubing-icon\.(event|unofficial)-(\w+):before\s*\{'
              r'[^}]*content:\s*"\\([0-9a-fA-F]+)"')
    resultado = {}
    for prefijo, nombre, cp in re.findall(patron, texto):
        clave = f"unofficial-{nombre}" if prefijo == "unofficial" else nombre
        resultado[clave] = int(cp, 16)
    return resultado if resultado else _CODEPOINTS_HARDCODED


_WOFF_PATH, _CSS_PATH = _encontrar_paquete_icons()
_CODEPOINTS = _cargar_codepoints(_CSS_PATH)
_ICON_FONT_CACHE = {}


def _asegurar_iconos():
    """Verifica la fuente de iconos; si no existe, la descarga automaticamente."""
    global _WOFF_PATH, _CSS_PATH, _CODEPOINTS
    if _WOFF_PATH:
        print(f"✅ Fuente de iconos WCA cargada ({len(_CODEPOINTS)} eventos)")
        return
    print("⚠  Fuente de iconos WCA no encontrada. Descargando...")
    if _descargar_iconos_wca():
        _WOFF_PATH, _CSS_PATH = _encontrar_paquete_icons()
        _CODEPOINTS = _cargar_codepoints(_CSS_PATH)
        if _WOFF_PATH:
            print(f"✅ Fuente de iconos WCA lista ({len(_CODEPOINTS)} eventos)")
        else:
            print("⚠  No se pudo cargar la fuente. Los eventos se mostraran como texto.")
    else:
        print("⚠  Continuando sin iconos. Los eventos se mostraran como texto.")


def _font_iconos(size):
    if not _WOFF_PATH:
        return None
    if size not in _ICON_FONT_CACHE:
        try:
            _ICON_FONT_CACHE[size] = ImageFont.truetype(_WOFF_PATH, size)
        except Exception:
            return None
    return _ICON_FONT_CACHE[size]


def render_icono_evento(event_id, size, color):
    cp   = _CODEPOINTS.get(event_id)
    font = _font_iconos(size)
    if cp is None or font is None:
        return None
    ch    = chr(cp)
    dummy = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    bb    = ImageDraw.Draw(dummy).textbbox((0, 0), ch, font=font)
    gw, gh = bb[2] - bb[0], bb[3] - bb[1]
    if gw <= 0 or gh <= 0:
        return None
    pad = 10
    img = Image.new("RGBA", (gw + pad * 2, gh + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad - bb[0], pad - bb[1]), ch, font=font, fill=color)
    return img

# ─────────────────────────────────────────────────────────────────────────────
# FUENTES DE TEXTO
# ─────────────────────────────────────────────────────────────────────────────

def cargar_fuente(size, negrita=False):
    # Rutas en Linux
    linux = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
         "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"]
        if negrita else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/usr/share/fonts/truetype/freefont/FreeSans.ttf"]
    )
    # Rutas en Windows (carpeta Fonts del sistema)
    win_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    windows = (
        [os.path.join(win_fonts, "arialbd.ttf"),
         os.path.join(win_fonts, "calibrib.ttf"),
         os.path.join(win_fonts, "verdanab.ttf"),
         os.path.join(win_fonts, "trebucbd.ttf")]
        if negrita else
        [os.path.join(win_fonts, "arial.ttf"),
         os.path.join(win_fonts, "calibri.ttf"),
         os.path.join(win_fonts, "verdana.ttf"),
         os.path.join(win_fonts, "trebuc.ttf")]
    )
    # macOS
    macos = (
        ["/System/Library/Fonts/Helvetica.ttc",
         "/Library/Fonts/Arial Bold.ttf"]
        if negrita else
        ["/System/Library/Fonts/Helvetica.ttc",
         "/Library/Fonts/Arial.ttf"]
    )
    # Fuente descargada como fallback junto al script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local = [
        os.path.join(base_dir, "fonts", "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf"),
    ]

    for p in local + windows + linux + macos:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass

    # Ultimo recurso: descargar DejaVu desde GitHub
    return _descargar_fuente_fallback(size, negrita)


def _descargar_fuente_fallback(size, negrita):
    """Descarga DejaVuSans desde GitHub si no hay fuente disponible."""
    import urllib.request
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    os.makedirs(fonts_dir, exist_ok=True)

    nombre = "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf"
    ruta_local = os.path.join(fonts_dir, nombre)

    if not os.path.exists(ruta_local):
        url_base = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/"
        try:
            print(f"  📥 Descargando fuente {nombre}...")
            urllib.request.urlretrieve(url_base + nombre, ruta_local)
            print(f"  ✅ Fuente descargada.")
        except Exception as e:
            print(f"  ⚠  No se pudo descargar la fuente: {e}")
            return ImageFont.load_default()

    try:
        return ImageFont.truetype(ruta_local, size)
    except Exception:
        return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────────────────────
# FUENTE DEPORTIVA (Bebas Neue — descarga automatica)
# ─────────────────────────────────────────────────────────────────────────────

_FUENTE_DEPORTIVA_CACHE = {}

def _descargar_fuente_deportiva():
    """Descarga Bebas Neue desde npm registry (sin necesidad de Node.js)."""
    import urllib.request, json, tarfile, io
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    ruta = os.path.join(fonts_dir, "BebasNeue-Regular.woff2")
    if os.path.exists(ruta):
        return ruta
    try:
        print("  📥 Descargando fuente deportiva (Bebas Neue)...")
        meta_url = "https://registry.npmjs.org/@fontsource/bebas-neue/latest"
        with urllib.request.urlopen(meta_url, timeout=15) as r:
            meta = json.loads(r.read())
        tarball_url = meta["dist"]["tarball"]
        with urllib.request.urlopen(tarball_url, timeout=30) as r:
            data = r.read()
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("bebas-neue-latin-400-normal.woff2"):
                    f = tar.extractfile(member)
                    if f:
                        with open(ruta, "wb") as out:
                            out.write(f.read())
                        print("  ✅ Fuente deportiva (Bebas Neue) lista.")
                        return ruta
        print("  ⚠  No se encontro el archivo de fuente en el paquete.")
        return None
    except Exception as e:
        print(f"  ⚠  No se pudo descargar Bebas Neue: {e}")
        return None

_RUTA_FUENTE_DEPORTIVA = None

def _asegurar_fuente_deportiva():
    global _RUTA_FUENTE_DEPORTIVA
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Buscar woff2 o ttf
    for nombre in ("BebasNeue-Regular.woff2", "BebasNeue-Regular.ttf"):
        ruta = os.path.join(base_dir, "fonts", nombre)
        if os.path.exists(ruta):
            _RUTA_FUENTE_DEPORTIVA = ruta
            return
    _RUTA_FUENTE_DEPORTIVA = _descargar_fuente_deportiva()

def cargar_fuente_deportiva(size):
    """Retorna Bebas Neue si esta disponible, sino la fuente normal en negrita."""
    if _RUTA_FUENTE_DEPORTIVA and os.path.exists(_RUTA_FUENTE_DEPORTIVA):
        if size not in _FUENTE_DEPORTIVA_CACHE:
            try:
                from PIL import ImageFont as _IF
                _FUENTE_DEPORTIVA_CACHE[size] = _IF.truetype(_RUTA_FUENTE_DEPORTIVA, size)
            except Exception:
                _FUENTE_DEPORTIVA_CACHE[size] = cargar_fuente(size, negrita=True)
        return _FUENTE_DEPORTIVA_CACHE[size]
    return cargar_fuente(size, negrita=True)

# ─────────────────────────────────────────────────────────────────────────────
# FONDO PERSONALIZADO DE MEDALLA
# ─────────────────────────────────────────────────────────────────────────────

def preparar_fondo_circular(img_fondo, radio, opacidad=1.0):
    """
    Recorta img_fondo en un circulo de diametro radio*2,
    aplica opacidad (0.0 transparente - 1.0 opaco) y retorna imagen RGBA.
    """
    d = radio * 2
    # Escalar para cubrir el circulo (crop centrado)
    w, h = img_fondo.size
    escala = max(d / w, d / h)
    nw, nh = int(w * escala), int(h * escala)
    img_scaled = img_fondo.resize((nw, nh), Image.LANCZOS).convert("RGBA")
    # Centrar crop
    x0 = (nw - d) // 2
    y0 = (nh - d) // 2
    img_crop = img_scaled.crop((x0, y0, x0 + d, y0 + d))
    # Mascara circular
    mascara = Image.new("L", (d, d), 0)
    ImageDraw.Draw(mascara).ellipse([0, 0, d - 1, d - 1], fill=255)
    # Aplicar opacidad a canal alpha
    r_, g_, b_, a_ = img_crop.split()
    if opacidad < 1.0:
        a_ = a_.point(lambda p: int(p * opacidad))
    # Combinar mascara con alpha original
    alpha_final = Image.fromarray(
        __import__("PIL").Image.fromarray(
            __import__("numpy", fromlist=["minimum"]).minimum(
                __import__("numpy").array(mascara),
                __import__("numpy").array(a_)
            )
        ).tobytes(), "L"
    ) if False else mascara  # usamos solo la mascara circular
    img_crop.putalpha(alpha_final)
    # Aplicar opacidad encima
    if opacidad < 1.0:
        bands = list(img_crop.split())
        bands[3] = bands[3].point(lambda p: int(p * opacidad))
        img_crop = Image.merge("RGBA", bands)
    return img_crop

# ─────────────────────────────────────────────────────────────────────────────
# CARPETAS Y RECURSOS
# ─────────────────────────────────────────────────────────────────────────────

def crear_carpetas(base_dir):
    """Crea las carpetas logo/, patrocinadores/ y fondo/ si no existen."""
    for nombre in ("logo", "patrocinadores", "fondo"):
        os.makedirs(os.path.join(base_dir, nombre), exist_ok=True)
    return (
        os.path.join(base_dir, "logo"),
        os.path.join(base_dir, "patrocinadores"),
        os.path.join(base_dir, "fondo"),
    )


def cargar_primera_imagen(carpeta):
    """Retorna la primera imagen encontrada en la carpeta, o None."""
    if not os.path.isdir(carpeta):
        return None
    for nombre in sorted(os.listdir(carpeta)):
        if os.path.splitext(nombre)[1].lower() in EXTS_IMAGEN:
            try:
                return Image.open(os.path.join(carpeta, nombre)).convert("RGBA")
            except Exception:
                pass
    return None


def cargar_todas_imagenes(carpeta):
    """Retorna lista de imágenes RGBA de todos los archivos en la carpeta."""
    imgs = []
    if not os.path.isdir(carpeta):
        return imgs
    for nombre in sorted(os.listdir(carpeta)):
        if os.path.splitext(nombre)[1].lower() in EXTS_IMAGEN:
            try:
                imgs.append(Image.open(os.path.join(carpeta, nombre)).convert("RGBA"))
            except Exception:
                pass
    return imgs

# ─────────────────────────────────────────────────────────────────────────────
# API WCA
# ─────────────────────────────────────────────────────────────────────────────

def consultar_competencia(wca_id):
    url = f"https://www.worldcubeassociation.org/api/v0/competitions/{wca_id}"
    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        data = r.json()
        return data.get("name", wca_id), data.get("event_ids", [])
    except requests.exceptions.ConnectionError:
        print("  ⚠  Sin conexion a la API de WCA.")
    except requests.exceptions.HTTPError as e:
        codigo = e.response.status_code
        msg = "no encontrada" if codigo == 404 else f"Error HTTP {codigo}"
        print(f"  ⚠  Competicion '{wca_id}' {msg}.")
    except Exception as e:
        print(f"  ⚠  Error inesperado: {e}")
    return None, None

# ─────────────────────────────────────────────────────────────────────────────
# TEXTO CURVO (arco superior)
# ─────────────────────────────────────────────────────────────────────────────

def dibujar_texto_curvo(img, texto, cx, cy, radio, fuente, color, arco_max=200,
                        fondo_alpha=0):
    """
    Dibuja texto curvado en el arco superior.
    fondo_alpha > 0: usa borde blanco en las letras (stroke) para legibilidad.
    """
    dummy = Image.new("RGBA", (4, 4))
    dd    = ImageDraw.Draw(dummy)
    anchos, altos = [], []
    for ch in texto:
        bb = dd.textbbox((0, 0), ch, font=fuente)
        anchos.append(max(bb[2] - bb[0], 1))
        altos.append(max(bb[3] - bb[1], 1))

    alto_max     = max(altos) if altos else 1
    angulo_total = min(math.degrees(sum(anchos) / radio), arco_max)
    angulo_actual = 270 - angulo_total / 2

    usar_stroke  = fondo_alpha > 0
    grosor_borde = 3   # px de borde blanco

    capa = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    angulo_actual_letra = angulo_actual

    for i, ch in enumerate(texto):
        delta      = math.degrees(anchos[i] / radio)
        ang_centro = angulo_actual_letra + delta / 2
        rad        = math.radians(ang_centro)
        x = cx + radio * math.cos(rad)
        y = cy + radio * math.sin(rad)

        margen = grosor_borde + 18
        cw = anchos[i] + margen * 2
        ch_h = alto_max + margen * 2
        ch_img = Image.new("RGBA", (cw, ch_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(ch_img)

        # Borde blanco: dibujar el carácter desplazado en 8 direcciones
        if usar_stroke:
            for dx in range(-grosor_borde, grosor_borde + 1):
                for dy in range(-grosor_borde, grosor_borde + 1):
                    if dx == 0 and dy == 0:
                        continue
                    if dx*dx + dy*dy <= grosor_borde*grosor_borde + 1:
                        d.text((margen + dx, margen + dy), ch, font=fuente,
                               fill=(255, 255, 255, 255))

        # Letra principal encima
        d.text((margen, margen), ch, font=fuente, fill=color)

        ch_rot = ch_img.rotate(-(ang_centro + 90), expand=True, resample=Image.BICUBIC)
        capa.paste(ch_rot, (int(x - ch_rot.width / 2), int(y - ch_rot.height / 2)), ch_rot)
        angulo_actual_letra += delta

    img.paste(capa, (0, 0), capa)

# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────────────────────

def centrar_imagen_en(img_base, img_pegar, cx, cy_centro):
    px = cx - img_pegar.width  // 2
    py = cy_centro - img_pegar.height // 2
    mask = img_pegar if img_pegar.mode == "RGBA" else None
    img_base.paste(img_pegar, (px, py), mask)


def ajustar_icono(icono, max_size):
    w, h   = icono.size
    escala = min(max_size / w, max_size / h)
    return icono.resize((int(w * escala), int(h * escala)), Image.LANCZOS)


def dividir_texto(texto, fuente, max_ancho):
    dummy = Image.new("RGB", (4, 4))
    d     = ImageDraw.Draw(dummy)
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        prueba = (actual + " " + p).strip()
        bb = d.textbbox((0, 0), prueba, font=fuente)
        if bb[2] - bb[0] <= max_ancho:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas or [texto]


def componer_banda_patrocinadores(logos, alto_max, ancho_max):
    """
    Banda BLANCA con logos ajustados al contenido real.
    Retorna (imagen_RGBA, ancho_real).
    """
    padding_v = 14
    padding_h = 18
    alto = alto_max
    max_logo_h = alto - padding_v * 2

    if not logos:
        fuente = cargar_fuente(24)
        texto  = "Patrocinadores"
        dummy  = Image.new("RGBA", (4, 4))
        bb     = ImageDraw.Draw(dummy).textbbox((0, 0), texto, font=fuente)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        ancho_real = min(tw + padding_h * 2, ancho_max)
        banda  = Image.new("RGBA", (ancho_real, alto), "#FFFFFFFF")
        draw   = ImageDraw.Draw(banda)
        draw.rectangle([0, 0, ancho_real - 1, alto - 1], outline="#CCCCCC", width=2)
        draw.text(((ancho_real - tw) // 2, (alto - th) // 2), texto, font=fuente, fill="#AAAAAA")
        return banda, ancho_real

    # Escalar logos al alto disponible
    logos_fit = [ajustar_icono(logo, max_logo_h) for logo in logos]

    # Ancho real basado en el contenido, no en el contenedor
    ancho_contenido = sum(l.width for l in logos_fit) + padding_h * (len(logos_fit) + 1)
    ancho_real = min(ancho_contenido, ancho_max)

    banda = Image.new("RGBA", (ancho_real, alto), "#FFFFFFFF")
    draw  = ImageDraw.Draw(banda)
    draw.rectangle([0, 0, ancho_real - 1, alto - 1], outline="#CCCCCC", width=2)

    # Distribuir con padding uniforme calculado para el ancho real
    total_logos_w  = sum(l.width for l in logos_fit)
    padding_h_real = max(padding_h, (ancho_real - total_logos_w) // (len(logos_fit) + 1))
    x = padding_h_real
    for logo_fit in logos_fit:
        y = (alto - logo_fit.height) // 2
        banda.paste(logo_fit, (x, y), logo_fit)
        x += logo_fit.width + padding_h_real

    return banda, ancho_real

# ─────────────────────────────────────────────────────────────────────────────
# TEXTO CURVO INFERIOR
# ─────────────────────────────────────────────────────────────────────────────

def dibujar_texto_curvo_inferior(img, texto, cx, cy, radio, fuente, color, arco_max=170):
    """Texto siguiendo la curvatura inferior del circulo (centrado en 90 deg PIL)."""
    dummy = Image.new("RGBA", (4, 4))
    dd    = ImageDraw.Draw(dummy)
    anchos, altos = [], []
    for ch in texto:
        bb = dd.textbbox((0, 0), ch, font=fuente)
        anchos.append(max(bb[2] - bb[0], 1))
        altos.append(max(bb[3] - bb[1], 1))

    alto_max     = max(altos) if altos else 1
    angulo_total = min(math.degrees(sum(anchos) / radio), arco_max)
    angulo_actual = 90 - angulo_total / 2

    capa = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for i, ch in enumerate(texto):
        delta      = math.degrees(anchos[i] / radio)
        ang_centro = angulo_actual + delta / 2
        rad        = math.radians(ang_centro)
        x = cx + radio * math.cos(rad)
        y = cy + radio * math.sin(rad)

        margen = 16
        ch_img = Image.new("RGBA", (anchos[i] + margen * 2, alto_max + margen * 2), (0, 0, 0, 0))
        ImageDraw.Draw(ch_img).text((margen, margen), ch, font=fuente, fill=color)
        ch_rot = ch_img.rotate(-(ang_centro - 90), expand=True, resample=Image.BICUBIC)
        capa.paste(ch_rot, (int(x - ch_rot.width / 2), int(y - ch_rot.height / 2)), ch_rot)
        angulo_actual += delta

    img.paste(capa, (0, 0), capa)

# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA DE PORTADA (logo del torneo)
# ─────────────────────────────────────────────────────────────────────────────

def generar_portada(nombre_torneo, logo_img):
    """
    Portada simple: circulo centrado igual tamaño que las medallas,
    con el logo dentro. Sin texto adicional.
    """
    radio_ext = SIZE // 2   # 540 px — toca los 4 bordes
    cx = cy = SIZE // 2

    img  = Image.new("RGB", (SIZE, SIZE), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Circulo exterior (mismo tamaño que las medallas)
    draw.ellipse(
        [cx - radio_ext, cy - radio_ext, cx + radio_ext, cy + radio_ext],
        fill="#E8E8E8", outline="#AAAAAA", width=5,
    )

    # Logo centrado dentro del circulo, escalado para llenar bien
    if logo_img is not None:
        logo_fit = ajustar_icono(logo_img, radio_ext * 2 - 200)
        centrar_imagen_en(img, logo_fit, cx, cy)
    else:
        fuente_ph = cargar_fuente(44)
        bb = draw.textbbox((0, 0), "[ Logo ]", font=fuente_ph)
        draw.text(
            (cx - (bb[2] - bb[0]) // 2, cy - (bb[3] - bb[1]) // 2),
            "[ Logo ]", font=fuente_ph, fill="#AAAAAA"
        )

    return img

# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA DE MEDALLA
# ─────────────────────────────────────────────────────────────────────────────

def generar_pagina_medalla(nombre_torneo, nombre_evento, lugar, event_id,
                           logos_patrocinadores, fondo_img=None, opacidad_fondo=0.85):
    """
    Diseño:
      • Círculo exterior toca los 4 bordes (radio = SIZE//2 = 540 px). SIN sombra.
      • Línea de borde interior decorativa a 30 px del borde.
      • Texto curvo del nombre del torneo en el arco superior del anillo.
      • Círculo blanco interior pequeño (radio 260) con:
          - Icono del evento (o texto si no hay icono) arriba
          - Separador
          - "Primer/Segundo/Tercer Lugar" en negrita
          - Nombre del evento
      • Franja rectangular de patrocinadores en la zona inferior del lienzo,
        fuera del círculo blanco pero dentro del cuadrado.
    """
    cols = COLORES_MEDALLA[lugar]
    cx = cy_medalla = SIZE // 2

    radio_ext = SIZE // 2   # 540 px — toca los 4 bordes
    radio_int = 320          # circulo blanco central

    img  = Image.new("RGB", (SIZE, SIZE), cols["fondo"])
    draw = ImageDraw.Draw(img)

    # ── Circulo exterior: fondo personalizado o color solido ────────────────────
    draw.ellipse(
        [cx - radio_ext, cy_medalla - radio_ext,
         cx + radio_ext, cy_medalla + radio_ext],
        fill=cols["anillo"], outline=cols["borde"], width=5,
    )
    if fondo_img is not None:
        capa_fondo = preparar_fondo_circular(fondo_img, radio_ext, opacidad_fondo)
        img.paste(capa_fondo, (cx - radio_ext, cy_medalla - radio_ext), capa_fondo)
        draw.ellipse(
            [cx - radio_ext, cy_medalla - radio_ext,
             cx + radio_ext, cy_medalla + radio_ext],
            fill=None, outline=cols["borde"], width=5,
        )
    # Linea decorativa interior del anillo
    m = 30
    draw.ellipse(
        [cx - radio_ext + m, cy_medalla - radio_ext + m,
         cx + radio_ext - m, cy_medalla + radio_ext - m],
        fill=None, outline=cols["borde"], width=3,
    )

    # ── Texto curvo nombre del torneo (arco superior del anillo) ──────────────
    radio_texto = radio_int + int((radio_ext - radio_int) * 0.55)
    dibujar_texto_curvo(img, nombre_torneo, cx, cy_medalla,
                        radio_texto, cargar_fuente_deportiva(62),
                        cols["texto"], arco_max=210,
                        fondo_alpha=255 if fondo_img is not None else 0)

    # ── Circulo blanco central (desplazado ligeramente hacia arriba) ──────────
    cy_blanco = cy_medalla - 40

    draw.ellipse(
        [cx - radio_int, cy_blanco - radio_int,
         cx + radio_int, cy_blanco + radio_int],
        fill="white", outline=cols["borde"], width=4,
    )

    # ── Contenido dentro del circulo blanco ───────────────────────────────────
    max_icono     = radio_int + 60
    icono_img     = render_icono_evento(event_id, size=500, color=cols["texto"]) if event_id else None
    zona_icono_cy = cy_blanco - 60

    if icono_img is not None:
        ajustado  = ajustar_icono(icono_img, max_icono)
        centrar_imagen_en(img, ajustado, cx, zona_icono_cy)
        limite_inf = zona_icono_cy + ajustado.height // 2
    else:
        fuente_cat = cargar_fuente_deportiva(72)
        lineas     = dividir_texto(nombre_evento, fuente_cat, radio_int * 2 - 40)
        alto_linea = 88
        total_h    = len(lineas) * alto_linea
        y0 = zona_icono_cy - total_h // 2
        for linea in lineas:
            bb = draw.textbbox((0, 0), linea, font=fuente_cat)
            draw.text((cx - (bb[2] - bb[0]) // 2, y0), linea,
                      font=fuente_cat, fill=cols["texto"])
            y0 += alto_linea
        limite_inf = zona_icono_cy + total_h // 2

    # Separador
    sep_y = limite_inf + 16
    draw.line([cx - 170, sep_y, cx + 170, sep_y], fill=cols["anillo"], width=5)

    # Lugar
    fuente_lugar = cargar_fuente_deportiva(68)
    y_lugar = sep_y + 16
    bb_l = draw.textbbox((0, 0), lugar, font=fuente_lugar)
    draw.text((cx - (bb_l[2] - bb_l[0]) // 2, y_lugar), lugar,
              font=fuente_lugar, fill=cols["texto"])

    # Nombre del evento (solo si tiene icono WCA)
    if icono_img is not None:
        fuente_ev = cargar_fuente(40)
        y_ev = y_lugar + (bb_l[3] - bb_l[1]) + 10
        bb_ev = draw.textbbox((0, 0), nombre_evento, font=fuente_ev)
        draw.text((cx - (bb_ev[2] - bb_ev[0]) // 2, y_ev), nombre_evento,
                  font=fuente_ev, fill="#666666")

    # ── Banda de patrocinadores en el ANILLO ─────────────────────────────────
    borde_sup_zona = cy_blanco + radio_int + 10
    borde_inf_zona = cy_medalla + radio_ext - 40

    espacio_v   = borde_inf_zona - borde_sup_zona
    alto_franja = max(40, espacio_v // 2)

    y_franja  = borde_sup_zona + (espacio_v - alto_franja) // 2
    y_top_rel = y_franja - cy_medalla
    ancho_max = int(2 * math.sqrt(max(0, radio_ext**2 - y_top_rel**2))) - 50

    banda, ancho_real = componer_banda_patrocinadores(
        logos_patrocinadores, alto_franja, ancho_max
    )

    x_franja = cx - ancho_real // 2
    fondo_banda = Image.new("RGB", (ancho_real, alto_franja), "white")
    fondo_banda.paste(banda, (0, 0), banda)
    img.paste(fondo_banda, (x_franja, y_franja))

    return img

# ─────────────────────────────────────────────────────────────────────────────
# EXPORTAR PDF
# ─────────────────────────────────────────────────────────────────────────────

def exportar_pdf(imagenes, ruta_salida):
    if not imagenes:
        print("No hay imagenes para exportar.")
        return
    pt = float(SIZE)
    c  = rl_canvas.Canvas(ruta_salida, pagesize=(pt, pt))
    for img in imagenes:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name, "PNG", dpi=(150, 150))
            tmp_path = tmp.name
        c.drawImage(tmp_path, 0, 0, pt, pt)
        c.showPage()
        os.unlink(tmp_path)
    c.save()
    print(f"\n✅ PDF generado: {ruta_salida}  ({len(imagenes)} paginas)")

# ─────────────────────────────────────────────────────────────────────────────
# FLUJO INTERACTIVO
# ─────────────────────────────────────────────────────────────────────────────

def preguntar(prompt, defecto=""):
    try:
        val = input(prompt).strip()
        return val if val else defecto
    except (EOFError, KeyboardInterrupt):
        return defecto


def main():
    print("=" * 62)
    print("  🏅  Generador de Plantillas de Medalleria WCA")
    print("=" * 62)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ── Instalar iconos y fuente deportiva automaticamente ───────────────────
    _asegurar_iconos()
    _asegurar_fuente_deportiva()
    if _RUTA_FUENTE_DEPORTIVA:
        print(f"✅ Fuente deportiva lista (Bebas Neue)")
    else:
        print(f"⚠  Fuente deportiva no disponible, usando fuente estandar")

    # ── Crear carpetas ────────────────────────────────────────────────────────
    dir_logo, dir_patros, dir_fondo = crear_carpetas(base_dir)

    # ── Flujo: logo ───────────────────────────────────────────────────────────
    print(f"\n{'─'*62}")
    print(f"  PASO 1 — Logo del torneo")
    print(f"{'─'*62}")
    print(f"  Carpeta: {dir_logo}")

    while True:
        logo_torneo = cargar_primera_imagen(dir_logo)
        if logo_torneo:
            archivos_logo = [f for f in os.listdir(dir_logo)
                             if os.path.splitext(f)[1].lower() in EXTS_IMAGEN]
            print(f"\n  🖼  Archivo encontrado: {archivos_logo[0]}")
            confirmar = preguntar("  ¿Usar este archivo como logo? [s/n]: ").lower()
            if confirmar in ("s", "si", "sí", "y", "yes"):
                break
            else:
                print("  Reemplaza el archivo en la carpeta y presiona Enter para reintentar.")
                preguntar("  [Enter para continuar]: ")
        else:
            print(f"\n  ⚠  No hay imagen en la carpeta de logo.")
            print(f"  Coloca un archivo PNG o JPG en:")
            print(f"  {dir_logo}")
            resp = preguntar("\n  [Enter para reintentar | 's' para continuar sin logo]: ").lower()
            if resp in ("s", "si", "sí", "y", "yes"):
                logo_torneo = None
                break

    # ── Flujo: patrocinadores ─────────────────────────────────────────────────
    print(f"\n{'─'*62}")
    print(f"  PASO 2 — Logos de patrocinadores")
    print(f"{'─'*62}")
    print(f"  Carpeta: {dir_patros}")

    while True:
        logos_patros = cargar_todas_imagenes(dir_patros)
        if logos_patros:
            archivos = [f for f in sorted(os.listdir(dir_patros))
                        if os.path.splitext(f)[1].lower() in EXTS_IMAGEN]
            print(f"\n  🤝 {len(logos_patros)} archivo(s) encontrado(s):")
            for f in archivos:
                print(f"     • {f}")
            confirmar = preguntar("  ¿Usar estos archivos como patrocinadores? [s/n]: ").lower()
            if confirmar in ("s", "si", "sí", "y", "yes"):
                break
            else:
                print("  Modifica los archivos en la carpeta y presiona Enter para reintentar.")
                preguntar("  [Enter para continuar]: ")
        else:
            print(f"\n  ⚠  No hay imagenes en la carpeta de patrocinadores.")
            print(f"  Coloca archivos PNG o JPG en:")
            print(f"  {dir_patros}")
            resp = preguntar("\n  [Enter para reintentar | 's' para continuar sin patrocinadores]: ").lower()
            if resp in ("s", "si", "sí", "y", "yes"):
                logos_patros = []
                break

    # ── Flujo: fondo personalizado ────────────────────────────────────────────
    print(f"\n{'─'*62}")
    print(f"  PASO 3 — Fondo personalizado de medallas (opcional)")
    print(f"{'─'*62}")
    print(f"  Carpeta: {dir_fondo}")
    print(f"  Si colocas una imagen aqui, se usara como fondo de todas las medallas.")

    fondo_img      = cargar_primera_imagen(dir_fondo)
    opacidad_fondo = 0.85

    if fondo_img:
        archivos_fondo = [f for f in os.listdir(dir_fondo)
                          if os.path.splitext(f)[1].lower() in EXTS_IMAGEN]
        print(f"\n  🎨 Imagen de fondo encontrada: {archivos_fondo[0]}")
        confirmar = preguntar("  ¿Usar esta imagen como fondo de las medallas? [s/n]: ").lower()
        if confirmar not in ("s", "si", "sí", "y", "yes"):
            fondo_img = None
            print("  ℹ  Sin fondo personalizado.")
        else:
            while True:
                try:
                    val = preguntar("  Opacidad del fondo [0-100, default 85]: ", "85")
                    opacidad_fondo = max(0, min(100, int(val))) / 100
                    break
                except ValueError:
                    print("  Ingresa un numero entre 0 y 100.")
            print(f"  ✓ Fondo activado con opacidad {int(opacidad_fondo*100)}%")
    else:
        print(f"\n  ℹ  No hay imagen en la carpeta fondo/. Las medallas usaran color solido.")
        print(f"     (Coloca un PNG/JPG en '{dir_fondo}' y vuelve a ejecutar para usar fondo)")

    # ── ID de la competicion ──────────────────────────────────────────────────
    print(f"\n{'─'*62}")
    print(f"  PASO 4 — Competicion WCA")
    print(f"{'─'*62}")
    wca_id = preguntar("\n  🔑 WCA Competition ID\n     (ej: NadaQueVerBucaramanga2026): ")
    if not wca_id:
        print("❌ ID vacio. Saliendo.")
        sys.exit(1)

    print(f"\n  🌐 Consultando API de WCA para '{wca_id}'...")
    nombre_torneo, event_ids = consultar_competencia(wca_id)

    if nombre_torneo is None:
        print("\n  ⚠  No se pudo obtener la informacion automaticamente.")
        nombre_torneo = preguntar("     ✏  Nombre del torneo: ", wca_id)
        print(f"     IDs disponibles: {', '.join(WCA_EVENTOS.keys())}")
        raw = preguntar("     ✏  IDs de eventos separados por coma: ", "")
        event_ids = [e.strip() for e in raw.split(",") if e.strip()] if raw else []
    else:
        print(f"  ✅ Torneo: {nombre_torneo}")
        print(f"     Eventos ({len(event_ids)}): {', '.join(event_ids)}")

    # ── Categorias no oficiales ───────────────────────────────────────────────
    print(f"\n{'─'*62}")
    print(f"  PASO 5 — Categorias no oficiales (opcional)")
    print(f"{'─'*62}")
    print(f"  Puedes añadir medallas de categorias no oficiales de la lista")
    print(f"  (con icono WCA) o crear una categoria personalizada.")

    eventos_no_oficiales = []   # tuplas (nombre, event_id, n_medallas)

    def preguntar_cantidad(nombre_cat, defecto=3):
        while True:
            try:
                n = int(preguntar(f"  ¿Cuantas medallas para '{nombre_cat}'? [1-10, default {defecto}]: ", str(defecto)))
                if 1 <= n <= 10:
                    return n
                print("  Ingresa un numero entre 1 y 10.")
            except ValueError:
                print("  Numero no valido.")

    if preguntar("\n  ¿Agregar categorias no oficiales? [s/n]: ").lower() in ("s", "si", "sí", "y", "yes"):
        # ── Seleccion de la lista de iconos no oficiales ────────────────────
        lista = list(WCA_EVENTOS_NO_OFICIALES.items())
        print(f"\n  Categorias no oficiales disponibles ({len(lista)}):")
        for i, (eid, nombre) in enumerate(lista, 1):
            print(f"    {i:2d}. {nombre}   [{eid}]")
        print(f"\n  Ingresa los numeros de las categorias a añadir, separados por coma.")
        print(f"  (Enter para saltar a una categoria personalizada)")

        seleccionados = set()
        while True:
            raw = preguntar("  Numeros [ej: 1,4,9]: ").strip()
            if not raw:
                break
            valido = True
            for parte in raw.split(","):
                parte = parte.strip()
                if not parte:
                    continue
                try:
                    idx = int(parte)
                except ValueError:
                    print(f"  '{parte}' no es un numero valido.")
                    valido = False
                    break
                if 1 <= idx <= len(lista):
                    seleccionados.add(idx)
                else:
                    print(f"  El numero {idx} no esta en la lista (1-{len(lista)}).")
                    valido = False
                    break
            if valido and seleccionados:
                break

        for idx in sorted(seleccionados):
            eid, nombre = lista[idx - 1]
            n = preguntar_cantidad(nombre)
            eventos_no_oficiales.append((nombre, eid, n))
            print(f"  ✓ '{nombre}' → {n} medalla(s)")

        # ── Categorias personalizadas (no estan en la lista) ────────────────
        print(f"\n  ¿Añadir una categoria personalizada que no este en la lista?")
        if preguntar("  (Ej: 'Categoria Infantil', 'Mejor Promedio') [s/n]: ").lower() in ("s", "si", "sí", "y", "yes"):
            while True:
                nombre_cat = preguntar("  Nombre de la categoria (Enter para terminar): ")
                if not nombre_cat:
                    break
                n = preguntar_cantidad(nombre_cat)
                eventos_no_oficiales.append((nombre_cat, None, n))
                print(f"  ✓ '{nombre_cat}' → {n} medalla(s)")
        elif seleccionados:
            print("  ℹ  Sin categorias personalizadas.")
    else:
        print("\n  ℹ  Sin categorias no oficiales. Solo medallas de la competencia.")

    # ── Archivo de salida ─────────────────────────────────────────────────────
    nombre_safe = "".join(c for c in wca_id if c.isalnum() or c in "-_")
    defecto_pdf = f"medallas_{nombre_safe}.pdf"
    ruta_pdf    = preguntar(f"\n  💾 Nombre del archivo PDF [{defecto_pdf}]: ", defecto_pdf)
    if not ruta_pdf.endswith(".pdf"):
        ruta_pdf += ".pdf"

    # ── Generar ───────────────────────────────────────────────────────────────
    print(f"\n{'─'*62}")
    total = len(event_ids) * 3 + sum(n for _, _, n in eventos_no_oficiales)
    print(f"  🎨 Generando {total + 1} paginas (1 portada + {total} medallas)...")
    print(f"{'─'*62}\n")

    paginas = [generar_portada(nombre_torneo, logo_torneo)]
    print("  ✓ Portada")

    for eid in event_ids:
        nombre_ev = WCA_EVENTOS.get(eid, eid.upper())
        for lugar in LUGARES:
            paginas.append(generar_pagina_medalla(nombre_torneo, nombre_ev, lugar, eid, logos_patros,
                fondo_img=fondo_img, opacidad_fondo=opacidad_fondo))
        ico = "🖼" if (_CODEPOINTS.get(eid) and _WOFF_PATH) else "📝"
        print(f"  {ico} {nombre_ev}")

    for nombre_cat, eid_cat, n_medallas in eventos_no_oficiales:
        for i in range(n_medallas):
            lugar = LUGARES[i] if i < len(LUGARES) else f"{i+1}° Lugar"
            paginas.append(generar_pagina_medalla(nombre_torneo, nombre_cat, lugar, eid_cat, logos_patros,
                fondo_img=fondo_img, opacidad_fondo=opacidad_fondo))
        ico = "🖼" if (eid_cat and _CODEPOINTS.get(eid_cat) and _WOFF_PATH) else "📝"
        print(f"  {ico} {nombre_cat}")

    ruta_completa = os.path.join(base_dir, ruta_pdf)
    exportar_pdf(paginas, ruta_completa)
    print(f"\n  📂 Archivo guardado en:\n     {ruta_completa}")


if __name__ == "__main__":
    main()
