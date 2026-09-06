# -*- coding: utf-8 -*-
"""
sor_wca_unificado.py
Calcula el Sum of Ranks de una competencia WCA.
Modos disponibles:
  1 - WCA Export (API REST de WCA)
  2 - WCA Live   (API GraphQL de live.worldcubeassociation.org)

Salida: un único PDF con las reglas + tabla SoR.
No se generan archivos intermedios en el directorio de trabajo.
"""

import importlib
import subprocess
import sys
import os
import math
import io
import tempfile
import warnings
warnings.filterwarnings("ignore")

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# ──────────────────────────────────────────────
# 0. AUTO-INSTALACIÓN DE DEPENDENCIAS
# ──────────────────────────────────────────────

REQUIRED = [
    ("reportlab", "reportlab"),
    ("pypdf",     "pypdf"),
    ("pandas",    "pandas"),
    ("requests",  "requests"),
]

def install_if_missing(packages):
    missing = []
    for import_name, pip_name in packages:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"📦 Instalando dependencias faltantes: {', '.join(missing)}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
            capture_output=True, text=True
        )
        if result.returncode != 0:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet",
                 "--break-system-packages"] + missing,
                capture_output=True, text=True
            )
        if result.returncode == 0:
            print("  ✅ Dependencias instaladas correctamente.")
        else:
            print("  ❌ No se pudieron instalar algunas dependencias:")
            print(result.stderr[:500])
            sys.exit(1)
    else:
        print("✅ Todas las dependencias Python están instaladas.")

def check_pdflatex():
    result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True)
    return result.returncode == 0

install_if_missing(REQUIRED)

PDFLATEX_AVAILABLE = check_pdflatex()
if not PDFLATEX_AVAILABLE:
    print()
    print("⚠  pdflatex no está instalado. El PDF de reglas no se adjuntará.")
    print("   Linux : sudo apt install texlive-latex-base texlive-latex-extra texlive-lang-spanish")
    print("   macOS : brew install --cask mactex")
    print()

import requests
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from pypdf import PdfWriter, PdfReader

# ──────────────────────────────────────────────
# 1. MENÚ DE SELECCIÓN
# ──────────────────────────────────────────────

print()
print("=" * 50)
print("        Sum of Ranks - WCA Calculator")
print("=" * 50)
print("Modos disponibles:")
print("  1 - WCA Export  (competencia terminada)")
print("  2 - WCA Live    (resultados en tiempo real)")
print()

while True:
    modo = input("Selecciona el modo [1/2]: ").strip()
    if modo in ("1", "2"):
        break
    print("  ⚠  Ingresa 1 o 2.")

print()
respuesta_multi = input("¿El torneo está dividido en varios eventos WCA distintos (ej. FMC SAC 2026 + SAC 2026)? [s/N]: ").strip().lower()
es_multi = respuesta_multi == "s"

competition_ids = []
if es_multi:
    while True:
        try:
            n_torneos = int(input("¿Cuántos torneos vas a unificar?: ").strip())
            if n_torneos >= 2:
                break
        except ValueError:
            pass
        print("  ⚠  Ingresa un número entero mayor o igual a 2.")
    for i in range(n_torneos):
        if modo == "1":
            cid = input(f"  ID de la competencia WCA #{i+1} (ej. RegionalesSantander2025): ").strip()
        else:
            cid = input(f"  ID de la competencia WCA / Live #{i+1} (ej. SouthOmahaScramble2026 o 11003): ").strip()
        competition_ids.append(cid)
else:
    if modo == "1":
        cid = input("ID de la competencia WCA (ej. RegionalesSantander2025): ").strip()
    else:
        cid = input("ID de la competencia WCA / Live (ej. SouthOmahaScramble2026 o 11003): ").strip()
    competition_ids.append(cid)

print()

# ──────────────────────────────────────────────
# 2. GENERACIÓN DEL PDF DE REGLAS EN MEMORIA
#    Se compila en un directorio temporal; nada queda en el cwd.
# ──────────────────────────────────────────────

LATEX_CODE = r"""
\documentclass[12pt,a4paper]{article}

% ------------------------------
% Paquetes básicos
% ------------------------------
\usepackage[utf8]{inputenc}   % Acentos en UTF-8
\usepackage[T1]{fontenc}
\usepackage[spanish]{babel}   % Idioma español

% Márgenes cómodos
\usepackage[margin=2.5cm]{geometry}

% Interlineado
\usepackage{setspace}
\setstretch{1.3}

% Colores y enlaces
\usepackage{xcolor}
\usepackage[colorlinks=true, linkcolor=black, urlcolor=blue]{hyperref}

% ------------------------------
% Encabezados y pies
% ------------------------------
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\cfoot{\thepage}

% ------------------------------
% Estilo de títulos
% ------------------------------
\usepackage{titlesec}
\titleformat{\section}{\Large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\large\bfseries}{\thesubsection}{1em}{}

% ------------------------------
% Portada sencilla
% ------------------------------
\title{\textbf{Explicación del Formato Sum of Ranks}}
\author{Camilo Guzmán}
\date{}

\begin{document}
\maketitle

\section{Definición y cálculo del Sum of Ranks}

El formato \textit{Sum of Ranks} es un sistema de clasificación que se utiliza
para ordenar a los competidores de acuerdo con su desempeño en múltiples pruebas.
En lugar de depender únicamente de un promedio o de un solo resultado, este método
suma las posiciones obtenidas por cada participante en distintas categorías o
eventos, generando así una medida más equilibrada de su rendimiento global.

El procedimiento general es el siguiente:

\begin{enumerate}
    \item Se toman los resultados de cada participante en los eventos incluidos
    dentro del formato.
    \item A cada competidor se le asigna un \textbf{rango} o \textbf{posición}
    según su desempeño en cada evento.
    \item Se suman los rangos de todos los eventos considerados.
    \item El competidor con la suma más baja ocupa la mejor posición en la
    clasificación general.
\end{enumerate}

\subsection{Reglas para la asignación de rangos}

Para definir con precisión qué rango corresponde a cada competidor en un evento,
se aplican las siguientes reglas:

\begin{itemize}
    \item \textbf{Última ronda disputada:} El rango asignado a un participante
    corresponde siempre a la última ronda en la que haya competido.
    \begin{itemize}
        \item Si un competidor participa únicamente en la primera ronda de un
        evento, su rango será el que obtuvo en esa ronda.
        \item Si avanza a una segunda o tercera ronda, se tomará como válido el
        rango obtenido en la última ronda en la que haya participado.
    \end{itemize}

    \textit{Ejemplo:} si un competidor avanza a semifinales y termina en el
    puesto 12, aunque haya sido 3° en la primera ronda, se toma el puesto 12 de
    la semifinal como su rango definitivo.

    \item \textbf{No participación en un evento:} Si un competidor no participa
    en un evento, se le asignará un rango igual al número total de participantes
    en la primera ronda de ese evento más uno.
    \begin{itemize}
        \item \textit{Ejemplo:} si en la primera ronda de un evento participaron 20
        personas, cualquier competidor que no haya competido en esa categoría
        recibirá un rango de $20+1 = 21$.
    \end{itemize}
\end{itemize}

Este sistema premia la consistencia: un competidor que mantenga buenos lugares en
todas las pruebas suele obtener un resultado más favorable que otro que destaque
en una sola pero tenga posiciones bajas o ausencia en las demás.

\section{Criterios de desempate}

La clasificación principal se establece a partir de la suma de rangos
(\textit{Sum of Ranks}). Sin embargo, es posible que dos o más competidores
obtengan el mismo valor total. Para resolver estas situaciones se aplican los
siguientes criterios de desempate, en el orden descrito:

\subsection{Primer criterio: Desviación estándar}

En caso de empate en el \textit{Sum of Ranks}, se compara la \textbf{desviación
estándar} de los rangos obtenidos por cada competidor en los diferentes eventos.

La desviación estándar es una medida estadística que indica cuánto se alejan los
resultados respecto a la media. En este contexto, refleja qué tan uniforme fue el
desempeño de un competidor en los distintos eventos.

La fórmula general es:

\[
\sigma = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (x_i - \mu)^2}
\]

donde:
\begin{itemize}
    \item $n$ es el número de eventos considerados,
    \item $x_i$ es el rango obtenido en cada evento,
    \item $\mu$ es el promedio de los rangos,
    \item $\sigma$ es la desviación estándar.
\end{itemize}

El criterio establece que \textbf{un competidor con menor desviación estándar
ocupará la mejor posición en caso de empate}. De esta forma, se favorece a los
participantes que muestran un rendimiento más consistente en todas las categorías
y se penaliza a quienes, aunque puedan tener un buen \textit{Sum of Ranks}, lo
logran con resultados muy desiguales o sin competir en todos los eventos.

\subsection{Segundo criterio: ID de registro}

Si el empate persiste después de aplicar la desviación estándar, se utiliza como
criterio el \textbf{ID de registro} de los competidores en el torneo.

Cada participante recibe un identificador único en el momento de inscribirse. Los
que se registraron primero cuentan con IDs más bajos que aquellos que se inscribieron
más tarde. En caso de empate, se dará prioridad a los competidores con un ID más
bajo, premiando así a quienes realizaron su registro de manera más temprana.

Es importante destacar que, como el ID de registro es un valor único y no se repite
para ningún competidor, este criterio garantiza que el empate se resolverá de forma
definitiva y no existirán clasificaciones iguales.

\textbf{Nota:} Los criterios de desempate se aplican de manera secuencial: primero
la desviación estándar y, solo si persiste el empate, el ID de registro.

\end{document}
"""

def build_rules_pdf_bytes():
    """Compila el LaTeX en un directorio temporal y devuelve el PDF como bytes.
    No deja ningún archivo en el directorio de trabajo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "ReglasSoR.tex")
        pdf_path = os.path.join(tmpdir, "ReglasSoR.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(LATEX_CODE)

        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, tex_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # Segunda pasada para referencias internas
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, tex_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if result.returncode == 0 and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return f.read()
        else:
            print("  ⚠  Error al compilar el PDF de reglas:")
            print(result.stderr.decode()[:500])
            return None

rules_pdf_bytes = None
if PDFLATEX_AVAILABLE:
    print("📄 Compilando PDF de reglas...")
    rules_pdf_bytes = build_rules_pdf_bytes()
    if rules_pdf_bytes:
        print("  ✅ Reglas compiladas en memoria.")

# ──────────────────────────────────────────────
# 3A. OBTENCIÓN DE DATOS — MODO WCA EXPORT (API REST)
# ──────────────────────────────────────────────

def fetch_wca_export(competition_id):
    """
    Usa exclusivamente la API REST de WCA (/results).
    Regla: tomar el pos de la ÚLTIMA ronda jugada por cada competidor.
    Si llegó a final → pos de final. Si solo llegó a primera ronda → pos de primera ronda.
    """
    print(f"\n🌐 Consultando API REST de WCA para '{competition_id}'...")

    # Nombre del torneo
    competition_name = competition_id
    try:
        meta = requests.get(
            f"https://www.worldcubeassociation.org/api/v0/competitions/{competition_id}",
            timeout=30
        )
        if meta.ok:
            competition_name = meta.json().get("name", competition_id)
    except Exception:
        pass

    # Resultados
    url = f"https://www.worldcubeassociation.org/api/v0/competitions/{competition_id}/results"
    resp = requests.get(url, timeout=30)
    if resp.status_code == 404:
        sys.exit(f"❌ No se encontró la competencia '{competition_id}' en WCA.")
    resp.raise_for_status()
    raw = resp.json()
    if not raw:
        sys.exit("❌ La API devolvió resultados vacíos. ¿El torneo ya tiene resultados publicados?")

    # registrantId y país desde WCIF público (para desempate y filtro por país)
    reg_map = {}
    country_map = {}
    try:
        wcif_resp = requests.get(
            f"https://www.worldcubeassociation.org/api/v0/competitions/{competition_id}/wcif/public",
            timeout=30
        )
        if wcif_resp.ok:
            for p in wcif_resp.json().get("persons", []):
                wca_id = p.get("wcaId") or ""
                reg_id = p.get("registrantId")
                if wca_id and reg_id is not None:
                    reg_map[wca_id] = reg_id
                if wca_id:
                    country_map[wca_id] = p.get("countryIso2", "??")
            print(f"  ✅ WCIF: {len(reg_map)} registrantIds obtenidos.")
    except Exception:
        print("  ⚠  WCIF no disponible. El ID de desempate usará wca_id y el país quedará vacío.")

    # Orden de rondas WCA
    # Orden oficial de rondas WCA (de primera a última)
    # d=primera, 2/3/4=intermedias, e=segunda(alt), b=semis, g=semifinal(alt), h=primera(alt), f=final, c=final_combinada, o=final_combinada(alt)
    ROUND_ORDER = ["d", "1", "h", "2", "e", "3", "b", "4", "g", "f", "c", "o"]

    from collections import defaultdict
    ev_rounds = defaultdict(lambda: defaultdict(list))
    for entry in raw:
        ev_rounds[entry["event_id"]][entry["round_type_id"]].append(entry)

    all_results = []
    event_participants = {}

    for event_id, rounds in ev_rounds.items():
        sorted_keys = sorted(
            rounds.keys(),
            key=lambda r: ROUND_ORDER.index(r) if r in ROUND_ORDER else 99
        )
        first_key = sorted_keys[0]
        event_participants[event_id] = len(rounds[first_key])

        # Última ronda jugada por cada persona → su pos en esa ronda es el rank
        person_last = {}
        for rkey in sorted_keys:
            for entry in rounds[rkey]:
                person_last[entry["wca_id"]] = (entry["pos"], entry["name"])

        for wca_id, (pos, name) in person_last.items():
            all_results.append({
                "personId": wca_id,
                "name":     name,
                "event":    event_id,
                "rank":     pos,
                "regId":    reg_map.get(wca_id, wca_id),
                "country":  country_map.get(wca_id, "??"),
            })

    return all_results, event_participants, competition_name
def resolve_wca_live_id(input_id):
    """Resuelve el ID numérico de una competencia en WCA Live clásico si se pasa un WCA ID alfanumérico."""
    if not input_id:
        return None
    s_id = str(input_id).strip()
    if s_id.isdigit():
        return s_id

    headers = {"User-Agent": "utilidades-torneos-wca", "Accept": "application/json"}
    meta = None
    try:
        r = requests.get(f"https://www.worldcubeassociation.org/api/v0/competitions/{s_id}", headers=headers, timeout=15)
        if r.ok:
            meta = r.json()
    except:
        pass

    name = meta.get('name') if meta else None
    if name:
        try:
            q = 'query($filter: String!) { competitions(filter: $filter) { id name wcaId } }'
            r = requests.post("https://live.worldcubeassociation.org/api", json={'query': q, 'variables': {'filter': name}}, headers=headers, timeout=15)
            if r.ok:
                comps = r.json().get('data', {}).get('competitions', [])
                for c in comps:
                    if c.get('wcaId', '').lower() == s_id.lower():
                        return c.get('id')
        except:
            pass
    return None

def fetch_wca_new_live(competition_id):
    """Intenta descargar datos de SoR desde la Nueva API Live de WCA (/live/rounds)."""
    headers = {"User-Agent": "utilidades-torneos-wca", "Accept": "application/json"}
    try:
        r_rounds = requests.get(f"https://www.worldcubeassociation.org/api/v1/competitions/{competition_id}/live/rounds", headers=headers, timeout=15)
        if not r_rounds.ok:
            return None
        rounds_json = r_rounds.json()
        raw_rounds = rounds_json.get('rounds', [])
        if not raw_rounds:
            return None
    except:
        return None

    print(f"\n🌐 Consultando Nueva API WCA Live para '{competition_id}'...")

    meta = {}
    try:
        r_meta = requests.get(f"https://www.worldcubeassociation.org/api/v0/competitions/{competition_id}", headers=headers, timeout=15)
        if r_meta.ok:
            meta = r_meta.json()
    except:
        pass
    competition_name = meta.get("name", competition_id)

    wcif_persons = []
    try:
        r_wcif = requests.get(f"https://www.worldcubeassociation.org/api/v0/competitions/{competition_id}/wcif/public", headers=headers, timeout=15)
        if r_wcif.ok:
            wcif_persons = r_wcif.json().get('persons', [])
    except:
        pass

    wcif_by_reg = {}
    wcif_by_user = {}
    wcif_by_id = {}
    for p in wcif_persons:
        w_id = p.get('wcaId')
        reg_id = p.get('registrantId')
        u_id = p.get('wcaUserId')
        country_iso2 = p.get('countryIso2')
        if reg_id is not None:
            wcif_by_reg[reg_id] = {'wcaId': w_id, 'countryIso2': country_iso2, 'name': p.get('name')}
        if u_id is not None:
            wcif_by_user[u_id] = {'wcaId': w_id, 'countryIso2': country_iso2, 'name': p.get('name')}
        if p.get('registration') and p.get('registration').get('wcaRegistrationId') is not None:
            wcif_by_id[p['registration']['wcaRegistrationId']] = {'wcaId': w_id, 'countryIso2': country_iso2, 'name': p.get('name')}

    from collections import defaultdict
    import re

    def event_id_from_round(rid):
        return re.sub(r'-r\d+$', '', str(rid))

    def round_num(rid):
        m = re.search(r'-r(\d+)$', str(rid))
        return int(m.group(1)) if m else 1

    rounds_by_event = defaultdict(list)
    for r in raw_rounds:
        ev = event_id_from_round(r['id'])
        rounds_by_event[ev].append(r)

    all_results = []
    event_participants = {}

    for ev, ev_rounds in rounds_by_event.items():
        ev_rounds_sorted = sorted(ev_rounds, key=lambda x: round_num(x['id']))
        last_rank = {}

        for idx, rnd in enumerate(ev_rounds_sorted):
            rid = rnd['id']
            r_det = requests.get(f"https://www.worldcubeassociation.org/api/v1/competitions/{competition_id}/live/rounds/{rid}", headers=headers, timeout=15)
            det = r_det.json() if r_det.ok else {}

            comp_by_id = {c['id']: c for c in det.get('competitors', [])}
            results_list = det.get('results', [])

            if idx == 0:
                event_participants[ev] = len(results_list)

            for res in results_list:
                ranking = res.get('global_pos') or res.get('ranking')
                if ranking is None:
                    continue

                reg_id = res.get('registration_id')
                c_info = comp_by_id.get(reg_id, {})
                c_reg = c_info.get('registrant_id')
                c_user = c_info.get('user_id')

                mapped = wcif_by_reg.get(c_reg) or wcif_by_user.get(c_user) or wcif_by_id.get(reg_id) or {}
                wca_id = mapped.get('wcaId')
                c_name = c_info.get('name') or mapped.get('name') or 'Desconocido'
                pais = c_info.get('country_iso2') or mapped.get('countryIso2') or '??'

                pid = wca_id if wca_id else f"LIVE_{competition_id}_{reg_id}"
                last_rank[pid] = {
                    "name": c_name,
                    "rank": ranking,
                    "regId": c_reg if c_reg is not None else (reg_id or pid),
                    "country": pais
                }

        for pid, info in last_rank.items():
            all_results.append({
                "personId": pid,
                "name": info["name"],
                "event": ev,
                "rank": info["rank"],
                "regId": info["regId"],
                "country": info["country"]
            })

    return all_results, event_participants, competition_name

def fetch_wca_live(competition_id):
    # 1. Probar Nueva API Live de WCA
    new_live_data = fetch_wca_new_live(competition_id)
    if new_live_data is not None:
        return new_live_data

    # 2. Fallback a WCA Live clásico (GraphQL)
    live_id = resolve_wca_live_id(competition_id) or competition_id
    print(f"\n🌐 Consultando WCA Live clásico (GraphQL) para id '{live_id}'...")
    url = "https://live.worldcubeassociation.org/api"
    headers = {"User-Agent": "utilidades-torneos-wca", "Accept": "application/json"}

    def build_query(con_pais):
        person_fields = "id\n                wcaId\n                name\n                registrantId"
        if con_pais:
            person_fields += "\n                country { iso2 }"
        return f"""
        {{
          competition(id: "{live_id}") {{
            id
            name
            competitionEvents {{
              event {{ id name }}
              rounds {{
                number
                results {{
                  ranking
                  person {{
                    {person_fields}
                  }}
                }}
              }}
            }}
          }}
        }}
        """

    resp = requests.post(url, json={"query": build_query(True)}, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    tiene_pais = True
    if "errors" in data:
        # El esquema puede no exponer "country" en Person; reintentamos sin ese campo
        tiene_pais = False
        resp = requests.post(url, json={"query": build_query(False)}, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            sys.exit(f"❌ Error GraphQL: {data['errors']}")

    competition = data.get("data", {}).get("competition")
    if competition is None:
        sys.exit(f"❌ No se encontró la competencia '{competition_id}' (Live ID: '{live_id}') en WCA Live.")

    competition_name = competition["name"]
    all_results = []
    event_participants = {}

    for ev in competition["competitionEvents"]:
        event_id = ev["event"]["id"]
        if not ev["rounds"]:
            continue

        event_participants[event_id] = len(ev["rounds"][0]["results"])

        last_rank = {}
        for rnd in ev["rounds"]:
            for result in rnd["results"]:
                # Usamos el wcaId (global) como llave de cruce entre torneos.
                wca_id = result["person"].get("wcaId")
                pid = wca_id if wca_id else f"LIVE_{live_id}_{result['person']['id']}"
                pais_obj = result["person"].get("country") if tiene_pais else None
                pais = pais_obj.get("iso2", "??") if pais_obj else "??"
                last_rank[pid] = {
                    "name":    result["person"]["name"],
                    "rank":    result["ranking"],
                    "regId":   result["person"].get("registrantId") or pid,
                    "country": pais,
                }

        for pid, info in last_rank.items():
            all_results.append({
                "personId": pid,
                "name":     info["name"],
                "event":    event_id,
                "rank":     info["rank"],
                "regId":    info["regId"],
                "country":  info["country"],
            })

    return all_results, event_participants, competition_name

# ──────────────────────────────────────────────
# 4. LLAMAR AL MODO CORRECTO
# ──────────────────────────────────────────────

all_results = []
event_participants = {}
nombres_torneos = []

for cid in competition_ids:
    if modo == "1":
        results, participants, name = fetch_wca_export(cid)
    else:
        results, participants, name = fetch_wca_live(cid)

    nombres_torneos.append(name)
    all_results.extend(results)

    # Si un evento aparece en más de un torneo (caso raro), se suman los
    # participantes de cada uno para calcular la penalización por no-participación.
    for ev, cnt in participants.items():
        event_participants[ev] = event_participants.get(ev, 0) + cnt

competition_name = " + ".join(nombres_torneos)

print(f"  ✅ Datos obtenidos: {len(all_results)} filas, {len(event_participants)} eventos, "
      f"{len(competition_ids)} torneo(s).")

# ──────────────────────────────────────────────
# 5. CÁLCULO DEL SUM OF RANKS
# ──────────────────────────────────────────────

df = pd.DataFrame(all_results)

# Nombre y regId representativos por persona (primer registro encontrado).
# Si la persona compitió en más de un torneo, el regId mostrado corresponde
# al primero con el que apareció — es solo un desempate determinístico,
# no representa un "ID de registro" oficial unificado entre torneos.
info_df = df.drop_duplicates(subset="personId", keep="first")[["personId", "name", "regId", "country"]]

pivot_df = df.pivot_table(
    index="personId",
    columns="event",
    values="rank",
    aggfunc="min"
).reset_index()
pivot_df.columns.name = None
pivot_df = pivot_df.merge(info_df, on="personId", how="left")

event_cols = list(event_participants.keys())
for ev in event_cols:
    penalty = event_participants[ev] + 1
    if ev not in pivot_df.columns:
        pivot_df[ev] = penalty
    else:
        pivot_df[ev] = pivot_df[ev].fillna(penalty)

pivot_df[event_cols] = pivot_df[event_cols].astype(int)

pivot_df["SoR"] = pivot_df[event_cols].sum(axis=1)

def std_poblacional(row):
    vals = row.values.astype(float)
    mu = vals.mean()
    return round(math.sqrt(sum((x - mu) ** 2 for x in vals) / len(vals)), 2)

pivot_df["Desv"] = pivot_df[event_cols].apply(std_poblacional, axis=1)

pivot_df["regId_num"] = pd.to_numeric(pivot_df["regId"], errors="coerce").fillna(999999).astype(int)

pivot_df = pivot_df.sort_values(
    by=["SoR", "Desv", "regId_num"],
    ascending=[True, True, True]
).reset_index(drop=True)

pivot_df.insert(0, "Puesto", range(1, len(pivot_df) + 1))

visible_cols = ["Puesto", "name"] + event_cols + ["SoR", "Desv", "regId_num"]
pivot_df_display = pivot_df[visible_cols].rename(columns={"name": "Nombre", "regId_num": "ID"})

print(f"\n{'─'*50}")
print(pivot_df_display.to_string(index=False))
print(f"{'─'*50}\n")

# ──────────────────────────────────────────────
# 6. TABLA SOR → PDF EN MEMORIA (buffer, sin archivo temporal)
# ──────────────────────────────────────────────

print("📄 Generando PDF de tabla SoR en memoria...")

from reportlab.lib.units import mm

# Anchos de columna fijos. El tamaño de página se calcula a partir de
# estos anchos (en vez de usar un tamaño fijo A4) para que la tabla
# nunca quede más ancha que la página, sin importar cuántos eventos tenga.
col_widths = []
for col in pivot_df_display.columns:
    if col == "Puesto":
        col_widths.append(12 * mm)
    elif col == "Nombre":
        col_widths.append(48 * mm)
    elif col in ("SoR", "Desv", "ID"):
        col_widths.append(16 * mm)
    else:  # columnas de evento (333, 444, 333bf, etc.)
        col_widths.append(14 * mm)

margin = 12 * mm
page_width = sum(col_widths) + 2 * margin
page_height = 297 * mm  # alto fijo tipo A4; el ancho se adapta al contenido

sor_buffer = io.BytesIO()
doc = SimpleDocTemplate(
    sor_buffer,
    pagesize=(page_width, page_height),
    leftMargin=margin, rightMargin=margin,
    topMargin=margin, bottomMargin=margin,
)
styles = getSampleStyleSheet()
elements = []

elements.append(Paragraph(f"Tabla Sum of Ranks - {competition_name}", styles["Heading1"]))
elements.append(Spacer(1, 10))

def construir_tabla(data_table, sor_col_idx, col_widths):
    t = Table(data_table, colWidths=col_widths, repeatRows=1)
    ts = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#2c3e50")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.whitesmoke),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  8),
        ("GRID",          (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ])
    PODIUM_COLORS = {
        1: colors.HexColor("#FFD700"),  # Oro
        2: colors.HexColor("#C0C0C0"),  # Plata
        3: colors.HexColor("#CD7F32"),  # Bronce
    }
    for puesto, color in PODIUM_COLORS.items():
        if puesto < len(data_table):
            ts.add("BACKGROUND", (0, puesto), (-1, puesto), color)
    ts.add("BACKGROUND", (sor_col_idx, 1), (sor_col_idx, -1), colors.HexColor("#fff176"))
    t.setStyle(ts)
    return t

data_table = [pivot_df_display.columns.tolist()] + [
    [str(v) for v in row] for row in pivot_df_display.values.tolist()
]
sor_col_idx = pivot_df_display.columns.tolist().index("SoR")

elements.append(construir_tabla(data_table, sor_col_idx, col_widths))

print("  ✅ Tabla SoR lista en memoria.")

# ──────────────────────────────────────────────
# 6B. TABLA(S) SOR FILTRADAS POR PAÍS (OPCIONAL)
# ──────────────────────────────────────────────

paises_disponibles = sorted(c for c in pivot_df["country"].dropna().unique() if c and c != "??")
if paises_disponibles:
    print(f"\nPaíses presentes en la tabla: {', '.join(paises_disponibles)}")
    quiere_filtro = input("¿Deseas generar tabla(s) SoR filtradas por país? [s/N]: ").strip().lower() == "s"

    if quiere_filtro:
        while True:
            pais = input("  Código de país (ISO2, ej. CO, PE, BR) o vacío para terminar: ").strip().upper()
            if not pais:
                break
            df_pais = pivot_df[pivot_df["country"] == pais].copy()
            if df_pais.empty:
                print(f"  ⚠  No hay competidores de '{pais}'. Disponibles: {', '.join(paises_disponibles)}")
                continue

            # Se recalcula el Puesto solo dentro de este país (no es el puesto global)
            df_pais = df_pais.sort_values(
                by=["SoR", "Desv", "regId_num"], ascending=[True, True, True]
            ).reset_index(drop=True)
            df_pais["Puesto"] = range(1, len(df_pais) + 1)

            df_pais_display = df_pais[visible_cols].rename(columns={"name": "Nombre", "regId_num": "ID"})

            print(f"\n── SoR filtrado: {pais} ──")
            print(df_pais_display.to_string(index=False))

            data_table_pais = [df_pais_display.columns.tolist()] + [
                [str(v) for v in row] for row in df_pais_display.values.tolist()
            ]

            elements.append(PageBreak())
            elements.append(Paragraph(f"Tabla Sum of Ranks - {competition_name} (País: {pais})", styles["Heading1"]))
            elements.append(Spacer(1, 10))
            elements.append(construir_tabla(data_table_pais, sor_col_idx, col_widths))

doc.build(elements)

# ──────────────────────────────────────────────
# 7. COMBINAR REGLAS + TABLA → ÚNICO PDF FINAL
# ──────────────────────────────────────────────

safe_name = competition_name.replace("/", "-").replace("\\", "-")
if len(safe_name) > 80:
    safe_name = safe_name[:80] + "..."
modo_label = "WCA_Live" if modo == "2" else "WCA_Export"
final_pdf  = f"SoR_{safe_name}_{modo_label}.pdf"

print(f"📎 Ensamblando PDF final: {final_pdf}")

writer = PdfWriter()

# Primero las reglas (si están disponibles)
if rules_pdf_bytes:
    rules_reader = PdfReader(io.BytesIO(rules_pdf_bytes))
    for page in rules_reader.pages:
        writer.add_page(page)

# Luego la tabla SoR
sor_buffer.seek(0)
sor_reader = PdfReader(sor_buffer)
for page in sor_reader.pages:
    writer.add_page(page)

with open(final_pdf, "wb") as f:
    writer.write(f)

if rules_pdf_bytes:
    print(f"  ✅ PDF completo (reglas + tabla): {final_pdf}")
else:
    print(f"  ✅ PDF generado (solo tabla, sin reglas): {final_pdf}")

print(f"\n🏁 Listo. Archivo final: {final_pdf}\n")
