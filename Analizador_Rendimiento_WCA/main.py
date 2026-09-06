#!/usr/bin/env python3
"""
Analizador de Rendimiento de Competidor WCA Live
Todo en un solo archivo - Genera PDF completo
"""
import requests
import io
import sys
import os
import tempfile
from datetime import date

# Importaciones para PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.utils import ImageReader

# Importaciones para gráficos
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

def latex_to_image_bytes(formula, fontsize=14, dpi=150,
                         text_color="#2C3E50", bg_color="#ECF0F1"):
    """
    Render a LaTeX formula to PNG bytes.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import io

    fig = plt.figure(figsize=(0.01, 0.01))
    text = fig.text(0, 0, f"${formula}$",
                    fontsize=fontsize, color=text_color,
                    ha='left', va='bottom')
    fig.canvas.draw()
    fig.tight_layout(pad=0.1)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=dpi, facecolor=bg_color,
                edgecolor='none', transparent=False, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

# Configuración
WCA_NEW_LIVE_API = "https://www.worldcubeassociation.org/api/v1"
WCA_LIVE_API = "https://live.worldcubeassociation.org/api"
WCA_API = "https://www.worldcubeassociation.org/api/v0"
API_HEADERS = {"User-Agent": "utilidades-torneos-wca", "Accept": "application/json"}

# Nombres de eventos
EVENT_NAMES = {
    '333': '3x3x3', '222': '2x2x2', '444': '4x4x4', '555': '5x5x5',
    '666': '6x6x6', '777': '7x7x7', '333bf': '3x3x3 Ciegas',
    '333fm': '3x3x3 FM', '333oh': '3x3x3 Una Mano', 'clock': 'Clock',
    'minx': 'Megaminx', 'pyram': 'Pyraminx', 'sq1': 'Square-1',
    'skewb': 'Skewb', '444bf': '4x4x4 Ciegas', '555bf': '5x5x5 Ciegas',
    '333mbf': '3x3x3 Multi Ciegas',
}

def get_event_name(eid):
    return EVENT_NAMES.get(eid, eid)

def format_time(cs, eid="333"):
    """Convierte centésimos de segundo a formato legible"""
    if cs <= 0:
        return "N/A"
    if eid == "333fm":
        return str(cs)
    secs = cs / 100
    if secs < 60:
        return f"{secs:.2f}"
    mins = int(secs // 60)
    secs = secs % 60
    return f"{mins}:{secs:05.2f}"

def event_id_from_round_id(round_id):
    import re
    return re.sub(r'-r\d+$', '', str(round_id))

def round_number_from_id(round_id):
    import re
    m = re.search(r'-r(\d+)$', str(round_id))
    return int(m.group(1)) if m else 1

def round_name_for(total_rounds, idx):
    if total_rounds <= 1 or idx == total_rounds - 1:
        return 'Final'
    if total_rounds >= 4 and idx == total_rounds - 2:
        return 'Semi Final'
    return f'Round {idx + 1}'

def resolve_wca_live_id(input_id):
    """Resuelve el ID numérico de una competencia en WCA Live clásico si se pasa un WCA ID alfanumérico."""
    if not input_id:
        return None
    s_id = str(input_id).strip()
    if s_id.isdigit():
        return s_id

    meta = None
    try:
        r = requests.get(f"{WCA_API}/competitions/{s_id}", headers=API_HEADERS, timeout=15)
        if r.ok:
            meta = r.json()
    except:
        pass

    name = meta.get('name') if meta else None
    if name:
        try:
            q = 'query($filter: String!) { competitions(filter: $filter) { id name wcaId } }'
            r = requests.post(WCA_LIVE_API, json={'query': q, 'variables': {'filter': name}}, headers=API_HEADERS, timeout=15)
            if r.ok:
                comps = r.json().get('data', {}).get('competitions', [])
                for c in comps:
                    if c.get('wcaId', '').lower() == s_id.lower():
                        return c.get('id')
        except:
            pass
    return None

def fetch_new_live_competition(comp_id):
    """Obtiene datos de la competencia desde la Nueva API Live de WCA (/live/rounds)."""
    try:
        r_rounds = requests.get(f"{WCA_NEW_LIVE_API}/competitions/{comp_id}/live/rounds", headers=API_HEADERS, timeout=15)
        if not r_rounds.ok:
            return None
        rounds_json = r_rounds.json()
        raw_rounds = rounds_json.get('rounds', [])
        if not raw_rounds:
            return None
    except:
        return None

    meta = {}
    try:
        r_meta = requests.get(f"{WCA_API}/competitions/{comp_id}", headers=API_HEADERS, timeout=15)
        if r_meta.ok:
            meta = r_meta.json()
    except:
        pass

    wcif_persons = []
    try:
        r_wcif = requests.get(f"{WCA_API}/competitions/{comp_id}/wcif/public", headers=API_HEADERS, timeout=15)
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
    rounds_by_event = defaultdict(list)
    for r in raw_rounds:
        ev = event_id_from_round_id(r['id'])
        rounds_by_event[ev].append(r)

    all_competitors_map = {}
    competition_events = []

    for ev, ev_rounds in rounds_by_event.items():
        ev_rounds_sorted = sorted(ev_rounds, key=lambda x: round_number_from_id(x['id']))
        comp_event_rounds = []
        for idx, rnd in enumerate(ev_rounds_sorted):
            rid = rnd['id']
            r_det = requests.get(f"{WCA_NEW_LIVE_API}/competitions/{comp_id}/live/rounds/{rid}", headers=API_HEADERS, timeout=15)
            det = r_det.json() if r_det.ok else {}

            comp_by_id = {c['id']: c for c in det.get('competitors', [])}
            parsed_results = []

            for res in det.get('results', []):
                reg_id = res.get('registration_id')
                c_info = comp_by_id.get(reg_id, {})
                c_reg = c_info.get('registrant_id')
                c_user = c_info.get('user_id')

                mapped = wcif_by_reg.get(c_reg) or wcif_by_user.get(c_user) or wcif_by_id.get(reg_id) or {}
                wca_id = mapped.get('wcaId')
                c_name = c_info.get('name') or mapped.get('name') or 'Desconocido'
                country_name = c_info.get('country_iso2') or mapped.get('countryIso2') or ''

                person_key = str(reg_id) if reg_id is not None else str(c_reg)
                if person_key not in all_competitors_map:
                    all_competitors_map[person_key] = {
                        'id': person_key,
                        'registrantId': c_reg,
                        'name': c_name,
                        'wcaId': wca_id,
                        'country': {'name': country_name}
                    }

                parsed_results.append({
                    'person': {'id': person_key, 'name': c_name, 'wcaId': wca_id, 'country': {'name': country_name}},
                    'best': res.get('best', 0),
                    'average': res.get('average', 0),
                    'ranking': res.get('global_pos') or res.get('ranking'),
                    'singleRecordTag': res.get('single_record_tag'),
                    'averageRecordTag': res.get('average_record_tag'),
                    'attempts': [{'result': a.get('value', 0)} for a in res.get('attempts', [])]
                })

            comp_event_rounds.append({
                'id': rid,
                'name': round_name_for(len(ev_rounds_sorted), idx),
                'number': round_number_from_id(rid),
                '_raw_results': parsed_results
            })

        competition_events.append({
            'id': ev,
            'event': {'id': ev, 'name': get_event_name(ev)},
            'rounds': comp_event_rounds
        })

    return {
        'id': comp_id,
        'name': meta.get('name', comp_id),
        'startDate': meta.get('start_date'),
        'endDate': meta.get('end_date'),
        'competitorLimit': meta.get('competitor_limit'),
        'competitors': list(all_competitors_map.values()),
        'competitionEvents': competition_events,
        'source': 'NEW_LIVE'
    }

def wca_live_query(query):
    """Ejecuta una query GraphQL en WCA Live clásico"""
    r = requests.post(WCA_LIVE_API, json={'query': query}, headers=API_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get('data', {})

def get_competition(comp_id):
    """Obtiene información de un torneo intentando Nueva Live y luego WCA Live clásico"""
    # 1. Intentar Nueva Live API
    new_live_data = fetch_new_live_competition(comp_id)
    if new_live_data:
        return {'competition': new_live_data}

    # 2. Fallback a WCA Live clásico (GraphQL)
    live_id = resolve_wca_live_id(comp_id) or comp_id
    query = '{ competition(id: "%s") { id name startDate competitors { id name wcaId country { name } } competitionEvents { id event { id name } rounds { id name number } } } }' % live_id
    data = wca_live_query(query)
    return data

def get_round_results(round_obj_or_id):
    """Obtiene resultados de una ronda (desde objeto precargado de New Live o vía query GraphQL)"""
    if isinstance(round_obj_or_id, dict) and '_raw_results' in round_obj_or_id:
        return {'round': {'results': round_obj_or_id['_raw_results']}}
    round_id = round_obj_or_id.get('id') if isinstance(round_obj_or_id, dict) else str(round_obj_or_id)
    query = '{ round(id: "%s") { id results { person { id name wcaId } best average ranking singleRecordTag averageRecordTag } } }' % round_id
    return wca_live_query(query)

def get_competitor_wca_history(wca_id):
    """Obtiene historial de competidor de WCA API"""
    try:
        r = requests.get(f"{WCA_API}/persons/{wca_id}/competitions", timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return []

def get_competitor_pr(wca_id):
    """Obtiene los PR (Personal Records) oficiales de la WCA para un competidor
    
    Returns:
        dict: {event_id: {'single': tiempo_cs, 'average': tiempo_cs}}
    """
    try:
        r = requests.get(f"{WCA_API}/persons/{wca_id}", timeout=30)
        r.raise_for_status()
        data = r.json()
        
        pr_data = {}
        
        # Los PR vienen en data['personal_records'] como dict {event_id: {single: {...}, average: {...}}}
        personal_records = data.get('personal_records', {})
        
        for event_id, records in personal_records.items():
            single_best = records.get('single', {}).get('best', 0)
            avg_best = records.get('average', {}).get('best', 0)
            
            pr_data[event_id] = {
                'single': single_best if single_best > 0 else None,
                'average': avg_best if avg_best > 0 else None
            }
        
        return pr_data
    except Exception as e:
        print(f"Error al obtener PR: {e}")
        return {}

def get_competitor_results_history(wca_id, target_events=None):
    """Obtiene historial de resultados por evento - últimos 5 torneos donde participó en cada evento
    
    Args:
        wca_id: ID de WCA del competidor
        target_events: Set de event_ids que nos interesan (para optimizar). Si es None, busca todos.
    """
    history = {}
    
    # Obtener competencias del competidor (todos)
    comps = get_competitor_wca_history(wca_id)
    
    # Ordenar por fecha (más recientes primero)
    comps_sorted = sorted(comps, key=lambda x: x.get('start_date', ''), reverse=True)
    
    # Para cada evento, encontrar los últimos 5 torneos donde participó
    event_count = {}  # event_id -> contador de torneos encontrados
    event_tournaments = {}  # event_id -> lista de torneos (más recientes primero)
    
    # Si tenemos eventos objetivo, solo buscamos esos
    if target_events:
        for eid in target_events:
            event_count[eid] = 0
            event_tournaments[eid] = []
    
    max_torneos_a_analizar = 60  # Aumentado para asegurar encontrar 5 por evento
    torneos_analizados = 0
    
    for comp in comps_sorted:
        # Verificar si ya tenemos 5 torneos para todos los eventos objetivo
        if target_events and all(event_count.get(eid, 0) >= 5 for eid in target_events):
            break
        
        # Parar si ya analizamos suficientes torneos
        if torneos_analizados >= max_torneos_a_analizar:
            break
        
        comp_id = comp.get('id', '')
        comp_name = comp.get('name', '')
        comp_date_str = comp.get('start_date', '')
        
        try:
            comp_date = date.fromisoformat(comp_date_str)
        except:
            continue
        
        # Obtener resultados del torneo
        try:
            r = requests.get(f"{WCA_API}/competitions/{comp_id}/results", timeout=30)
            r.raise_for_status()
            results = r.json()
            
            # Diccionario temporal para este torneo - mejores resultados por evento
            tournament_best = {}
            competitor_in_tournament = False
            
            for result in results:
                if result.get('wca_id') == wca_id:
                    competitor_in_tournament = True
                    event_id = result.get('event_id', '')
                    
                    # Si tenemos eventos objetivo y este no está en la lista, saltamos
                    if target_events and event_id not in target_events:
                        continue
                    
                    single = result.get('best', 0)
                    avg = result.get('average', 0)
                    
                    if event_id not in tournament_best:
                        tournament_best[event_id] = {'single': 0, 'average': 0}
                    
                    # Guardar el mejor resultado
                    if single > 0 and (tournament_best[event_id]['single'] == 0 or single < tournament_best[event_id]['single']):
                        tournament_best[event_id]['single'] = single
                    if avg > 0 and (tournament_best[event_id]['average'] == 0 or avg < tournament_best[event_id]['average']):
                        tournament_best[event_id]['average'] = avg
            
            # Solo contar torneo si el competidor participó
            if competitor_in_tournament:
                # Agregar torneos a cada evento que tenga resultados
                for event_id, best_results in tournament_best.items():
                    if best_results['single'] > 0 or best_results['average'] > 0:
                        # Inicializar contador si es necesario
                        if event_id not in event_count:
                            event_count[event_id] = 0
                            event_tournaments[event_id] = []
                        
                        # Solo agregar si no hemos llegado a 5 torneos para este evento
                        if event_count[event_id] < 5:
                            event_tournaments[event_id].append({
                                'comp': comp_name,
                                'date': comp_date,
                                'single': best_results['single'],
                                'average': best_results['average']
                            })
                            event_count[event_id] += 1
                
                torneos_analizados += 1
        except Exception as e:
            print(f"Error al obtener resultados de {comp_id}: {e}")
            continue
    
    # Reordenar cronológicamente (del más antiguo al más reciente) para la gráfica
    for event_id in event_tournaments:
        history[event_id] = sorted(event_tournaments[event_id], key=lambda x: x['date'])
    
    return history

def create_trend_chart(event_name, data, event_id="333"):
    """Crea gráfico de tendencia vectorizado (SVG) con etiquetas de tiempos"""
    if not MATPLOTLIB_AVAILABLE or not data or len(data) < 2:
        return None
    
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Ordenar cronológicamente (del más antiguo al más reciente)
    data_sorted = sorted(data, key=lambda x: x['date'])
    
    # Nombres completos de torneos (sin truncar)
    labels = [d['comp'] for d in data_sorted]
    singles = [d['single']/100 if d['single'] > 0 else None for d in data_sorted]
    avgs = [d['average']/100 if d['average'] > 0 else None for d in data_sorted]
    
    # Crear figura con espacio extra para etiquetas largas
    num_points = len(labels)
    fig_width = max(10, num_points * 2.2)  # Ancho proporcional al número de puntos
    fig_height = 6.5  # Altura aumentada para dar espacio a etiquetas diagonales
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    x = np.arange(len(labels))
    
    # Espaciar los puntos horizontalmente más
    if num_points > 1:
        ax.set_xlim(-0.5, num_points - 0.5)
    
    valid_s = [(i, s) for i, s in enumerate(singles) if s]
    valid_a = [(i, a) for i, a in enumerate(avgs) if a]
    
    # Dibujar líneas y puntos
    if valid_s:
        xs, ss = zip(*valid_s)
        line_s, = ax.plot(xs, ss, marker="o", color="#E74C3C", linewidth=2.5, 
                         markersize=10, label="PR Single", zorder=3)
        
        # Agregar etiquetas con tiempos encima de cada punto
        for i, (xi, yi) in enumerate(zip(xs, ss)):
            time_label = format_time(int(yi * 100), event_id)
            ax.annotate(time_label, xy=(xi, yi), xytext=(0, 12), 
                       textcoords='offset points', fontsize=9, 
                       ha='center', fontweight='bold', color='#E74C3C')
    
    if valid_a:
        xa, aa = zip(*valid_a)
        line_a, = ax.plot(xa, aa, marker="s", color="#3498DB", linewidth=2.5, 
                         markersize=10, label="PR Average", zorder=3)
        
        # Agregar etiquetas con tiempos debajo de cada punto
        for i, (xi, yi) in enumerate(zip(xa, aa)):
            time_label = format_time(int(yi * 100), event_id)
            ax.annotate(time_label, xy=(xi, yi), xytext=(0, -18), 
                       textcoords='offset points', fontsize=9, 
                       ha='center', fontweight='bold', color='#3498DB')
    
    # Configurar título
    ax.set_title(f"{event_name} - Historial de Rendimiento", 
                fontsize=14, fontweight="bold", pad=35)
    
    # Configurar ejes X con etiquetas completas
    ax.set_xticks(x)
    # Rotación 45 grados diagonal - el estilo preferido
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
    
    # Configurar eje Y
    ax.set_ylabel('Tiempo (segundos)', fontsize=11, fontweight='bold')
    
    # Leyenda posicionada arriba del gráfico, centrada horizontalmente
    # bbox_to_anchor=(0.5, 1.15) la coloca arriba, centrada horizontalmente
    # ncol=2 para que los elementos estén en una fila horizontal
    ax.legend(fontsize=10, loc='upper center', bbox_to_anchor=(0.5, 1.12), 
             ncol=2, framealpha=0.95, fancybox=True, shadow=True,
             borderpad=0.5, labelspacing=0.3)
    
    # Grid más sutil
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    
    # Ajustar layout: más margen superior para el legend, inferior para etiquetas diagonales
    plt.subplots_adjust(bottom=0.40, left=0.08, right=0.95, top=0.82)
    
    # Guardar como SVG (vectorial) para mejor calidad
    # NOTA: No usamos bbox_inches='tight' para respetar los márgenes configurados
    buf = io.BytesIO()
    plt.savefig(buf, format="svg", 
                facecolor='white', edgecolor='none', dpi=150)
    buf.seek(0)
    plt.close()
    return buf.getvalue()

def analyze_competitor(comp_id, reg_id):
    """Analiza el rendimiento de un competidor"""
    print(f"Analizando competidor {reg_id}...")
    
    # Obtener info del torneo
    data = get_competition(comp_id)
    comp = data.get('competition', {})
    
    # Buscar al competidor (por id interno, registrantId o wcaId)
    competitor = None
    target_str = str(reg_id).strip()
    for c in comp.get('competitors', []):
        if (str(c.get('id', '')) == target_str or 
            str(c.get('registrantId', '')) == target_str or 
            (c.get('wcaId') and c.get('wcaId', '').lower() == target_str.lower())):
            competitor = c
            break

    if not competitor:
        print(f"Competidor {reg_id} no encontrado")
        return None

    matched_id = str(competitor.get('id', ''))
    matched_reg = str(competitor.get('registrantId', ''))
    matched_wca = str(competitor.get('wcaId', '')).lower() if competitor.get('wcaId') else None

    print(f"Competidor: {competitor['name']}")
    print(f"WCA ID: {competitor.get('wcaId', 'Sin WCA ID')}")

    # Obtener resultados - Agrupados por evento (mejor resultado de todas las rondas)
    event_results = {}  # Diccionario para agrupar por evento

    for event in comp.get('competitionEvents', []):
        event_id = event.get('event', {}).get('id', '')
        event_name = get_event_name(event_id)

        for round_data in event.get('rounds', []):
            round_results = get_round_results(round_data)

            for result in round_results.get('round', {}).get('results', []):
                person = result.get('person', {})
                person_id = str(person.get('id', ''))
                person_wca = str(person.get('wcaId', '')).lower() if person.get('wcaId') else None
                person_reg = str(person.get('registrantId', ''))

                is_match = (person_id == matched_id or 
                            (matched_reg and person_reg == matched_reg) or 
                            (matched_wca and person_wca == matched_wca))

                if is_match:
                    if event_id not in event_results:
                        event_results[event_id] = {
                            'event_id': event_id,
                            'event_name': event_name,
                            'best': result.get('best', 0),
                            'average': result.get('average', 0),
                            'ranking': result.get('ranking'),
                            'is_pr_s': result.get('singleRecordTag') is not None,
                            'is_pr_a': result.get('averageRecordTag') is not None
                        }
                    else:
                        # Actualizar con mejor resultado si es necesario
                        current = event_results[event_id]
                        if result.get('best', 0) > 0 and (current['best'] == 0 or result.get('best', 0) < current['best']):
                            current['best'] = result.get('best', 0)
                        if result.get('average', 0) > 0 and (current['average'] == 0 or result.get('average', 0) < current['average']):
                            current['average'] = result.get('average', 0)
                        # Actualizar PR si hay en cualquier ronda
                        if result.get('singleRecordTag') is not None:
                            current['is_pr_s'] = True
                        if result.get('averageRecordTag') is not None:
                            current['is_pr_a'] = True
    
    # Convertir diccionario a lista
    results = list(event_results.values())
    
    return {
        'competitor': competitor,
        'competition': comp,
        'results': results
    }

def generate_pdf(analysis, output_path):
    """Genera el informe PDF"""
    comp = analysis['competition']
    competitor = analysis['competitor']
    results = analysis['results']
    wca_id = competitor.get('wcaId', '')
    
    # Fecha de referencia
    ref_date = date.today()
    if comp.get('startDate'):
        try:
            ref_date = date.fromisoformat(comp['startDate'])
        except:
            pass
    
    # Crear PDF
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=A4, 
        rightMargin=40, 
        leftMargin=40, 
        topMargin=40, 
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # PORTADA CENTRADA VERTICALMENTE
    # Espaciado superior para centrar el contenido
    story.append(Spacer(1, 2.5*inch))
    
    # Encabezado con fondo de color
    header_style = ParagraphStyle(
        'Header',
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#FFFFFF"),
        backColor=colors.HexColor("#2C3E50"),
        spaceAfter=12,
        leading=14
    )
    story.append(Paragraph("WORLD CUBE ASSOCIATION - LIVE", header_style))
    story.append(Spacer(1, 1.0*inch))
    
    # Título principal
    title_style = ParagraphStyle(
        'Title',
        fontSize=26,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1A252F"),
        fontName="Helvetica-Bold",
        spaceAfter=8,
        leading=32
    )
    story.append(Paragraph("INFORME DE RENDIMIENTO", title_style))
    story.append(Spacer(1, 0.4*inch))
    
    # Subtítulo
    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#5D6D7E"),
        fontName="Helvetica",
        spaceAfter=6
    )
    story.append(Paragraph("Análisis de Competidor WCA", subtitle_style))
    story.append(Spacer(1, 0.8*inch))
    
    # Nombre del competidor
    name_box_style = ParagraphStyle(
        'NameBox',
        fontSize=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1A252F"),
        fontName="Helvetica-Bold",
        spaceAfter=16
    )
    story.append(Paragraph(competitor['name'], name_box_style))
    
    # WCA ID con badge de color
    if wca_id:
        wca_badge_style = ParagraphStyle(
            'WCABadge',
            fontSize=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#FFFFFF"),
            backColor=colors.HexColor("#2980B9"),
            spaceAfter=12,
            leading=14
        )
        story.append(Paragraph(f"  WCA ID: {wca_id}  ", wca_badge_style))
    else:
        story.append(Paragraph("NUEVO COMPETIDOR", 
            ParagraphStyle('NewBadge', fontSize=11, alignment=TA_CENTER, 
                          textColor=colors.HexColor("#FFFFFF"), 
                          backColor=colors.HexColor("#E67E22"),
                          spaceAfter=12, leading=14)))
    
    story.append(Spacer(1, 0.6*inch))
    
    # Información del torneo en tabla elegante
    tourney_data = [
        ["TORNEO", comp.get('name', 'Unknown')],
        ["FECHA", ref_date.strftime('%d/%m/%Y')],
        ["PAÍS", competitor.get('country', {}).get('name', 'N/A')]
    ]
    
    tourney_table = Table(tourney_data, colWidths=[1.2*inch, 4*inch])
    tourney_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), "Helvetica-Bold"),
        ('FONTNAME', (1, 0), (1, -1), "Helvetica"),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor("#34495E")),
        ('ALIGN', (0, 0), (0, -1), "RIGHT"),
        ('ALIGN', (1, 0), (1, -1), "LEFT"),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor("#BDC3C7")),
    ]))
    story.append(tourney_table)
    
    # Pie de portada
    story.append(Spacer(1, 1.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#95A5A6")
    )
    story.append(Paragraph(f"Generado el {date.today().strftime('%d/%m/%Y')}", footer_style))
    
    story.append(PageBreak())
    
    # SECCIÓN 1: DATOS DEL COMPETIDOR
    story.append(Paragraph("1. DATOS DEL COMPETIDOR", styles['Heading2']))
    story.append(Spacer(1, 0.05*inch))
    
    # Parágrafo descriptivo
    desc_style = ParagraphStyle(
        'Description',
        fontSize=9,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#2C3E50"),
        leftIndent=10,
        rightIndent=10,
        spaceAfter=6
    )
    story.append(Paragraph(
        "Información básica del competidor y sus datos de identificación en la WCA.",
        desc_style))
    story.append(Spacer(1, 0.05*inch))
    
    data_table = [
        ["Campo", "Valor"],
        ["Nombre", competitor['name']],
        ["WCA ID", wca_id or "Sin asignar"],
        ["País", competitor.get('country', {}).get('name', 'N/A')],
    ]
    
    t = Table(data_table, colWidths=[1.5*inch, 3*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), "Helvetica-Bold"),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#ECF0F1")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15*inch))
    
    # SECCIÓN 2: RESULTADOS
    story.append(Paragraph("2. RESULTADOS DEL TORNEO", styles['Heading2']))
    story.append(Spacer(1, 0.05*inch))
    
    # Parágrafo descriptivo
    desc_style = ParagraphStyle(
        'Description',
        fontSize=9,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#2C3E50"),
        leftIndent=10,
        rightIndent=10,
        spaceAfter=6
    )
    story.append(Paragraph(
        "Resumen de los resultados obtenidos por el competidor en cada categoría del torneo actual, "
        "incluyendo los mejores tiempos y ranking alcanzado.",
        desc_style))
    story.append(Spacer(1, 0.05*inch))
    
    if results:
        rows = [["Categoría", "Mejor Single", "Mejor Average", "Ranking", "PR"]]
        for r in results:
            pr = []
            if r['is_pr_s']: pr.append("S")
            if r['is_pr_a']: pr.append("A")
            rows.append([
                r['event_name'],
                format_time(r['best'], r['event_id']),
                format_time(r['average'], r['event_id']),
                str(r['ranking']) if r['ranking'] else "-",
                ", ".join(pr) if pr else "-"
            ])
        
        t2 = Table(rows, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 0.8*inch, 0.6*inch])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2980B9")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), "Helvetica-Bold"),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), "CENTER"),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t2)
    
    # SECCIÓN 3: PRs
    prs = [r for r in results if r['is_pr_s'] or r['is_pr_a']]
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("3. PERSONAL RECORDS OBTENIDOS", styles['Heading2']))
    story.append(Spacer(1, 0.05*inch))
    
    # Parágrafo descriptivo
    desc_style = ParagraphStyle(
        'Description',
        fontSize=9,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#2C3E50"),
        leftIndent=10,
        rightIndent=10,
        spaceAfter=6
    )
    story.append(Paragraph(
        "Lista de los Personal Records (PR) obtenidos por el competidor en este torneo específico. "
        "Un PR se registra cuando el competidor supera su mejor marca histórica oficial en la WCA.",
        desc_style))
    story.append(Spacer(1, 0.05*inch))
    
    if prs:
        for r in prs:
            ind = []
            if r['is_pr_s']: ind.append("Single")
            if r['is_pr_a']: ind.append("Average")
            story.append(Paragraph(f"• {r['event_name']}: {', '.join(ind)}", styles['Normal']))
    else:
        story.append(Paragraph("No se obtuvieron Personal Records en este torneo.", styles['Normal']))
    
    # SECCIÓN 4: RENDIMIENTO RELATIVO AL HISTÓRICO PERSONAL
    # Obtener PR oficiales de la WCA y historial para gráficos
    pr_data = {}
    history = None
    if wca_id:
        print("Obteniendo PR oficiales de la WCA...")
        pr_data = get_competitor_pr(wca_id)
        print("Obteniendo historial para gráficos...")
        target_events = set(r['event_id'] for r in results)
        history = get_competitor_results_history(wca_id, target_events)
    
    if wca_id and pr_data:
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("4. RENDIMIENTO RELATIVO AL HISTÓRICO PERSONAL", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        # Parágrafo descriptivo
        desc_style = ParagraphStyle(
            'Description',
            fontSize=9,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#2C3E50"),
            leftIndent=10,
            rightIndent=10,
            spaceAfter=6
        )
        story.append(Paragraph(
            "Este capítulo compara el rendimiento del competidor en el torneo actual "
            "con sus Personal Records (PR) oficiales registrados en la WCA.",
            desc_style))
        story.append(Spacer(1, 0.05*inch))
        
        # Mejorar la presentación de las ecuaciones con un estilo de código
        eq_style = ParagraphStyle(
            'Equation',
            fontSize=9,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#2C3E50"),
            leftIndent=20,
            rightIndent=20,
            backColor=colors.HexColor("#ECF0F1"),
            borderPadding=5,
            spaceAfter=3
        )
        story.append(Paragraph("δ_s = (Single_Torneo - Single_PR) / Single_PR", eq_style))
        story.append(Paragraph("δ_a = (Average_Torneo - Average_PR) / Average_PR", eq_style))
        story.append(Paragraph("X = 0.4×δ_s + 0.6×δ_a (si hay promedio disponible)", eq_style))
        story.append(Spacer(1, 0.05*inch))
        
        story.append(Paragraph(
            "Donde:",
            desc_style))
        story.append(Paragraph(
            "• Single_Torneo: Mejor tiempo en single del torneo actual", 
            ParagraphStyle('Bullet', fontSize=9, alignment=TA_LEFT, leftIndent=25, textColor=colors.HexColor("#2C3E50")))
        )
        story.append(Paragraph(
            "• Single_PR: Personal Record oficial de single en WCA", 
            ParagraphStyle('Bullet', fontSize=9, alignment=TA_LEFT, leftIndent=25, textColor=colors.HexColor("#2C3E50")))
        )
        story.append(Paragraph(
            "• Average_Torneo: Mejor tiempo en average del torneo actual (si aplica)", 
            ParagraphStyle('Bullet', fontSize=9, alignment=TA_LEFT, leftIndent=25, textColor=colors.HexColor("#2C3E50")))
        )
        story.append(Paragraph(
            "• Average_PR: Personal Record oficial de average en WCA (si aplica)", 
            ParagraphStyle('Bullet', fontSize=9, alignment=TA_LEFT, leftIndent=25, textColor=colors.HexColor("#2C3E50")))
        )
        story.append(Spacer(1, 0.05*inch))
        story.append(Spacer(1, 0.1*inch))
        
        # Mostrar escala de colores horizontalmente
        story.append(Paragraph("Escala de clasificación:", 
                              ParagraphStyle('ScaleLabel', fontSize=9, alignment=TA_LEFT, 
                                           textColor=colors.HexColor("#2C3E50"), spaceAfter=2)))
        # Crear barra de colores horizontal: una fila con celdas para cada categoría
        color_row = []
        categories = ["S", "A", "B", "C", "D"]
        labels = {
            "S": "Nuevo PB",
            "A": "0-5%",
            "B": "5-15%", 
            "C": "15-30%",
            "D": ">30%"
        }
        colors_hex = {
            "S": "#008000",
            "A": "#4CAF50", 
            "B": "#8BC34A",
            "C": "#FFEB3B",
            "D": "#FF9800"
        }
        for cat in categories:
            bg = colors_hex[cat]
            txt = "#FFFFFF" if cat in ["S", "A"] else "#000000"
            label = f"{labels[cat]} ({cat})"
            # Create a Paragraph with tight leading to avoid extra vertical space
            label_style = ParagraphStyle(f'ColorLabel_{cat}',
                                         fontSize=8,
                                         alignment=TA_CENTER,
                                         textColor=colors.HexColor(txt),
                                         fontName="Helvetica-Bold",
                                         leading=8)  # leading equals font size to avoid extra height
            cell = Table([[Paragraph(f"  {label}  ", label_style)]],
                         colWidths=[0.8*inch],
                         style=TableStyle([
                             ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg)),
                             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                             ('LEFTPADDING', (0, 0), (-1, -1), 2),
                             ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                             ('TOPPADDING', (0, 0), (-1, -1), 2),
                             ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                         ]))
            color_row.append(cell)
        color_table = Table([color_row], colWidths=[0.8*inch]*5)
        color_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(color_table)
        story.append(Spacer(1, 0.1*inch))
        
        # Calcular métricas para cada evento
        performance_data = []
        valid_events = []
        
        for r in results:
            eid = r['event_id']
            
            # Verificar si tenemos PR para este evento
            if eid not in pr_data:
                continue  # Excluir eventos sin PR registrado
            
            # PR oficiales de la WCA
            best_single_hist = pr_data[eid].get('single')
            best_avg_hist = pr_data[eid].get('average')
            
            # Si no hay PR single, no podemos calcular
            if not best_single_hist or best_single_hist <= 0:
                continue
            
            # Tiempos del torneo actual
            best_single_tourney = r['best']
            best_avg_tourney = r['average']
            
            # Manejar DNF
            is_dnf = best_single_tourney <= 0
            
            if is_dnf:
                category = "D (DNF)"
                delta_s = None
                delta_a = None
                x_value = None
            else:
                # Calcular δ_s y δ_a comparando con los PR oficiales
                delta_s = (best_single_tourney - best_single_hist) / best_single_hist
                
                if best_avg_hist and best_avg_tourney > 0:
                    delta_a = (best_avg_tourney - best_avg_hist) / best_avg_hist
                    x_value = 0.4 * delta_s + 0.6 * delta_a
                else:
                    delta_a = None
                    x_value = delta_s
                
                # Clasificar
                if x_value <= 0:
                    category = "S"
                elif x_value <= 0.05:
                    category = "A"
                elif x_value <= 0.15:
                    category = "B"
                elif x_value <= 0.30:
                    category = "C"
                else:
                    category = "D"
            
            performance_data.append({
                'event_name': r['event_name'],
                'single_tourney': best_single_tourney if best_single_tourney > 0 else None,
                'single_hist': best_single_hist,
                'avg_tourney': best_avg_tourney if best_avg_tourney > 0 else None,
                'avg_hist': best_avg_hist,
                'delta_s': delta_s,
                'delta_a': delta_a,
                'x': x_value,
                'category': category
            })
            
            if not is_dnf:
                valid_events.append(x_value)
        
        # Colores RETIQ para las categorías
        retiq_colors_bg = {
            "S": "#008000",  # Verde oscuro
            "A": "#4CAF50",  # Verde
            "B": "#8BC34A",  # Verde claro
            "C": "#FFEB3B",  # Amarillo
            "D": "#FF9800",  # Naranja
        }
        retiq_colors_text = {
            "S": "#FFFFFF",  # Texto blanco
            "A": "#FFFFFF",  # Texto blanco
            "B": "#000000",  # Texto negro
            "C": "#000000",  # Texto negro
            "D": "#000000",  # Texto negro
        }
        
        # Crear tabla de rendimiento
        if performance_data:
            rows = [["Evento", "Single\nTorneo", "PR Single\n(WCA)", "Avg\nTorneo", "PR Average\n(WCA)", "δ_s", "δ_a", "X", "Cat."]]
            
            for data in performance_data:
                rows.append([
                    data['event_name'],
                    format_time(data['single_tourney'], results[0]['event_id']) if data['single_tourney'] else "DNF",
                    format_time(data['single_hist'], results[0]['event_id']),
                    format_time(data['avg_tourney'], results[0]['event_id']) if data['avg_tourney'] else "N/A",
                    format_time(data['avg_hist'], results[0]['event_id']) if data['avg_hist'] else "N/A",
                    f"{data['delta_s']:.2%}" if data['delta_s'] is not None else "-",
                    f"{data['delta_a']:.2%}" if data['delta_a'] is not None else "-",
                    f"{data['x']:.2%}" if data['x'] is not None else "-",
                    data['category']
                ])
            
            t_perf = Table(rows, colWidths=[1.2*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.5*inch])
            
            # Estilo base de la tabla
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#9B59B6")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), "Helvetica-Bold"),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), "CENTER"),
                ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#F5EEF8")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]
            
            # Aplicar colores RETIQ a la columna de categoría (última columna)
            for i, data in enumerate(performance_data, start=1):
                cat = data['category']
                if cat in retiq_colors_bg:
                    table_style.append(('BACKGROUND', (-1, i), (-1, i), colors.HexColor(retiq_colors_bg[cat])))
                    table_style.append(('TEXTCOLOR', (-1, i), (-1, i), colors.HexColor(retiq_colors_text[cat])))
                    table_style.append(('FONTNAME', (-1, i), (-1, i), "Helvetica-Bold"))
            
            t_perf.setStyle(TableStyle(table_style))
            story.append(t_perf)
            
            # Clasificación global
            if valid_events:
                global_x = sum(valid_events) / len(valid_events)
                
                if global_x <= 0:
                    global_category = "S"
                elif global_x <= 0.05:
                    global_category = "A"
                elif global_x <= 0.15:
                    global_category = "B"
                elif global_x <= 0.30:
                    global_category = "C"
                else:
                    global_category = "D"
                
                story.append(Spacer(1, 0.2*inch))
                
                # Tabla simple con la clasificación global coloreada
                global_rows = [
                    ["Clasificación Global", "X Promedio", "Categoría"],
                    [f"{len(valid_events)} eventos", f"{global_x:.2%}", global_category]
                ]
                
                global_table = Table(global_rows, colWidths=[1.8*inch, 1.5*inch, 1.0*inch])
                global_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), "Helvetica-Bold"),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), "CENTER"),
                    ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                    ('BACKGROUND', (0, 1), (1, 1), colors.HexColor("#ECF0F1")),
                    ('BACKGROUND', (2, 1), (2, 1), colors.HexColor(retiq_colors_bg[global_category])),
                    ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor(retiq_colors_text[global_category])),
                    ('FONTNAME', (2, 1), (2, 1), "Helvetica-Bold"),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(global_table)
                
                # Leyenda de categorías
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(
                    "S:PB  |  A:0-5%  |  B:5-15%  |  C:15-30%  |  D:>30%",
                    ParagraphStyle('Legend', fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor("#7F8C8D"))
                ))
    
    # SECCIÓN 5: GRÁFICOS (si tiene WCA ID)
    if wca_id and MATPLOTLIB_AVAILABLE and history:
        print("Generando gráficos...")
        
        story.append(Spacer(1, 0.05*inch))
        story.append(Paragraph("5. GRÁFICOS DE TENDENCIA", styles['Heading2']))
        story.append(Spacer(1, 0.02*inch))
        # Parágrafo descriptivo
        desc_style = ParagraphStyle(
            'Description',
            fontSize=9,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#2C3E50"),
            leftIndent=10,
            rightIndent=10,
            spaceAfter=4
        )
        story.append(Paragraph(
            "Esta sección muestra la evolución histórica del rendimiento del competidor en cada evento "
            "competido en el torneo actual. Cada gráfico presenta los mejores tiempos de single y average "
            "obtenidos en los últimos cinco torneos donde participó en dicho evento, permitiendo observar "
            "tendencias de mejora o retroceso respecto a su desempeño previo.",
            desc_style))
        story.append(Spacer(1, 0.03*inch))
        
        for r in results:
                eid = r['event_id']
                if eid in history and len(history[eid]) >= 2:
                    chart_svg = create_trend_chart(r['event_name'], history[eid], eid)
                    if chart_svg:
                        # Guardar SVG temporalmente y convertir
                        import tempfile
                        import os
                        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as tmp:
                            tmp.write(chart_svg)
                            tmp_path = tmp.name
                        
                        try:
                            from svglib.svglib import svg2rlg
                            drawing = svg2rlg(tmp_path)
                            if drawing:
                                story.append(Paragraph(r['event_name'], styles['Heading3']))
                                # Escalar el dibujo para ajustar al ancho de página (máximo 6.5 pulgadas)
                                max_width = 6.5 * inch
                                max_height = 3.5 * inch
                                scale = min(max_width / drawing.width, max_height / drawing.height, 1.0)
                                drawing.width *= scale
                                drawing.height *= scale
                                drawing.scale(scale, scale)
                                # Centrar la gráfica usando una tabla
                                chart_table = Table([[drawing]], colWidths=[max_width])
                                chart_table.setStyle(TableStyle([
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ]))
                                story.append(chart_table)
                                story.append(Spacer(1, 0.15*inch))
                        except Exception as e:
                            print(f"Error al procesar SVG: {e}")
                            # Fallback a PNG
                            import matplotlib
                            matplotlib.use('Agg')
                            import matplotlib.pyplot as plt
                            # Recrear el gráfico
                            data = history[eid]
                            plt.figure(figsize=(7, 3.5))
                            labels = [d['comp'][:20] for d in data]
                            singles = [d['single']/100 if d['single'] > 0 else None for d in data]
                            avgs = [d['average']/100 if d['average'] > 0 else None for d in data]
                            # Código de fallback consistente
                            num_points = len(labels)
                            plt.figure(figsize=(max(10, num_points * 2.2), 6.5))
                            valid_s = [(i, s) for i, s in enumerate(singles) if s]
                            valid_a = [(i, a) for i, a in enumerate(avgs) if a]
                            if valid_s:
                                xs, ss = zip(*valid_s)
                                plt.plot(xs, ss, marker="o", color="#E74C3C", linewidth=2.5, label="Single")
                            if valid_a:
                                xa, aa = zip(*valid_a)
                                plt.plot(xa, aa, marker="s", color="#3498DB", linewidth=2.5, label="Average")
                            plt.title(r['event_name'], fontsize=14, fontweight='bold', pad=35)
                            plt.xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=7)
                            plt.ylabel('Tiempo (segundos)', fontsize=11)
                            plt.legend(fontsize=10, loc='upper center', bbox_to_anchor=(0.5, 1.12), 
                                     ncol=2, framealpha=0.95, fancybox=True, shadow=True,
                                     borderpad=0.5, labelspacing=0.3)
                            plt.subplots_adjust(bottom=0.40, left=0.08, right=0.95, top=0.82)
                            buf = io.BytesIO()
                            plt.savefig(buf, format="png", dpi=150, bbox_inches='tight')
                            buf.seek(0)
                            story.append(Image(buf, width=5.5*inch, height=3*inch))
                            plt.close()
                        finally:
                            # Limpiar archivo temporal
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass
            
    doc.build(story)
    return output_path

def main():
    # Verificar si se proporcionaron argumentos de línea de comandos
    if len(sys.argv) >= 3:
        comp_id = sys.argv[1]
        reg_id = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else None
        # Modo directo (no interactivo)
        print(f"=== Analizando competidor {reg_id} en torneo {comp_id} ===\n")
        analysis = analyze_competitor(comp_id, reg_id)
        if not analysis:
            print("No se pudo analizar al competidor")
            sys.exit(1)
        if not output:
            safe_name = "".join(c for c in analysis['competitor']['name'] if c.isalnum() or c in " -_")
            safe_comp = "".join(c for c in comp_id if c.isalnum() or c in " -_")
            output = f"Informe rendimiento {safe_comp} {safe_name}.pdf"
        print(f"Generando PDF: {output}")
        generate_pdf(analysis, output)
        print(f"Informe generado: {output}")
        return
    # Modo interactivo (solo si hay entrada estándar disponible)
    try:
        print("=" * 60)
        print("ANALIZADOR DE RENDIMIENTO WCA")
        print("=" * 60)
        print()
        
        comp_id = input("Ingrese el ID del torneo (competition_id): ").strip()
        if not comp_id:
            print("Error: El ID del torneo es obligatorio")
            sys.exit(1)
        
        # Obtener datos del torneo para listar competidores
        print("\nObteniendo información del torneo...")
        data = get_competition(comp_id)
        comp = data.get('competition', {})
        comp_name = comp.get('name', 'Desconocido')
        competitors = comp.get('competitors', [])
        if not competitors:
            print("No se encontraron competidores en este torneo.")
            sys.exit(1)
        
        print(f"\nTorneo: {comp_name}")
        print("Competidores disponibles:")
        for idx, c in enumerate(competitors, start=1):
            name = c.get('name', 'Sin nombre')
            reg = c.get('id', 'Sin ID')
            wca = c.get('wcaId', 'Sin WCA')
            print(f"  {idx}. {name} (ID registro: {reg}, WCA ID: {wca})")
        
        print("\nSeleccione modo de análisis:")
        print("  1. Análisis individual (especificar un competidor)")
        print("  2. Análisis de todos los competidores")
        mode = input("Ingrese 1 o 2: ").strip()
        
        if mode == "1":
            # Análisis individual
            sel = input("Ingrese el número de la lista o el ID de registro del competidor: ").strip()
            # Determinar si es número o ID
            try:
                idx = int(sel)
                if 1 <= idx <= len(competitors):
                    reg_id = str(competitors[idx-1].get('id', ''))
                else:
                    print("Número fuera de rango.")
                    sys.exit(1)
            except ValueError:
                # Tratar como ID de registro
                reg_id = sel
                # Verificar que exista
                if not any(str(c.get('id', '')) == reg_id for c in competitors):
                    print("ID de registro no encontrado en la lista.")
                    sys.exit(1)
            
            print(f"\n=== Analizando competidor {reg_id} en torneo {comp_id} ===\n")
            analysis = analyze_competitor(comp_id, reg_id)
            if not analysis:
                print("No se pudo analizar al competidor")
                sys.exit(1)
            
            # Nombre de archivo por defecto
            safe_name = "".join(c for c in analysis['competitor']['name'] if c.isalnum() or c in " -_")
            safe_comp = "".join(c for c in comp_name if c.isalnum() or c in " -_")
            output = f"Informe rendimiento {safe_comp} {safe_name}.pdf"
            print(f"Generando PDF: {output}")
            generate_pdf(analysis, output)
            print(f"Informe generado: {output}")
        
        elif mode == "2":
            # Análisis de todos los competidores
            import os
            output_dir = os.path.join(os.getcwd(), "output")
            os.makedirs(output_dir, exist_ok=True)
            print(f"\nGenerando informes para todos los competidores en carpeta: {output_dir}")
            for c in competitors:
                reg_id = str(c.get('id', ''))
                name = c.get('name', 'Desconocido')
                wca_id = c.get('wcaId', '')
                print(f"\n--- Procesando: {name} (ID registro: {reg_id}) ---")
                analysis = analyze_competitor(comp_id, reg_id)
                if not analysis:
                    print(f"  -> No se pudo analizar, se omite.")
                    continue
                safe_name = "".join(c for c in name if c.isalnum() or c in " -_")
                safe_comp = "".join(c for c in comp_name if c.isalnum() or c in " -_")
                filename = f"Informe rendimiento {safe_comp} {safe_name}.pdf"
                output_path = os.path.join(output_dir, filename)
                print(f"  Generando: {filename}")
                generate_pdf(analysis, output_path)
                print(f"  -> Guardado en: {output_path}")
            print("\n=== Proceso completado ===")
        else:
            print("Opción no válida.")
            sys.exit(1)
    except EOFError:
        # No hay entrada estándar disponible, usar modo argumentos (pero ya no hay suficientes argumentos)
        print("Modo interactivo no disponible (no hay entrada estándar). Use argumentos de línea de comandos:")
        print("  python main.py <competition_id> <registration_id> [output.pdf]")
        sys.exit(1)

if __name__ == "__main__":
    main()
