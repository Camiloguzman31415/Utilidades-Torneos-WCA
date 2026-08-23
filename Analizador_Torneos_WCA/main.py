"""
Analizador de Torneos WCA LIVE - Version Simple
Generador de Informes PDF para torneos de speedcubing
"""
import sys
import os
import argparse
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from statistics import mean
import requests
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Configuracion
WCA_LIVE_API_URL = "https://live.worldcubeassociation.org/api"
CHART_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
    '#F8C471', '#82E0AA', '#F1948A', '#D7BDE2', '#A9DFBF',
    '#F9E79F', '#D5DBDB', '#AEB6BF', '#D2B4DE', '#A3E4D7',
]

# Mapeo de codigos de eventos a nombres completos
EVENT_DISPLAY_NAMES = {
    '333': '3x3x3',
    '222': '2x2x2',
    '444': '4x4x4',
    '555': '5x5x5',
    '666': '6x6x6',
    '777': '7x7x7',
    '333bf': '3x3x3 a Ciegas',
    '333fm': '3x3x3 Menos Movimientos',
    '333oh': '3x3x3 Una Mano',
    'clock': 'Clock',
    'minx': 'Megaminx',
    'pyram': 'Pyraminx',
    'sq1': 'Square-1',
    'skewb': 'Skewb',
    '444bf': '4x4x4 a Ciegas',
    '555bf': '5x5x5 a Ciegas',
    '333mbf': '3x3x3 Multi a Ciegas',
}

def get_event_display_name(event_id: str) -> str:
    """Retorna el nombre completo de un evento"""
    return EVENT_DISPLAY_NAMES.get(event_id, event_id)

# ==================== MODELOS ====================

@dataclass
class Attempt:
    result: int
    event_id: str = '333'  # Por defecto 333
    
    @property
    def is_valid(self) -> bool:
        # Para 333fm (Fewest Moves), valores validos son 1-80
        if self.event_id == '333fm':
            return 1 <= self.result <= 80
        return self.result > 0
    
    @property
    def is_completed(self) -> bool:
        # Para 333fm (Fewest Moves), valores validos son 1-80
        if self.event_id == '333fm':
            return 1 <= self.result <= 80
        return self.result > 0

@dataclass
class Person:
    id: str
    name: str
    wca_id: Optional[str] = None
    country: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Person':
        country_data = data.get('country', {})
        country_name = country_data.get('name') if isinstance(country_data, dict) else None
        return cls(
            id=str(data.get('id', '')),
            name=data.get('name', 'Unknown'),
            wca_id=data.get('wcaId'),
            country=country_name
        )

@dataclass
class Result:
    person: Person
    attempts: List[Attempt]
    best: int
    average: int
    ranking: Optional[int] = None
    regional_single_record: Optional[str] = None
    regional_average_record: Optional[str] = None
    event_id: str = '333'
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], event_id: str = '333') -> 'Result':
        person = Person.from_dict(data.get('person', {}))
        attempts_data = data.get('attempts', [])
        attempts = [Attempt(result=a.get('result', 0), event_id=event_id) for a in attempts_data]
        return cls(
            person=person,
            attempts=attempts,
            best=data.get('best', 0),
            average=data.get('average', 0),
            ranking=data.get('ranking'),
            regional_single_record=data.get('singleRecordTag'),
            regional_average_record=data.get('averageRecordTag'),
            event_id=event_id
        )
    
    @property
    def has_attempted(self) -> bool:
        return len(self.attempts) > 0
    
    @property
    def valid_attempts(self) -> List[int]:
        return [a.result for a in self.attempts if a.is_valid]

@dataclass
class Round:
    id: str
    name: str
    number: int
    results: List[Result] = field(default_factory=list)
    event_id: str = '333'
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], event_id: str = '333') -> 'Round':
        results_data = data.get('results', [])
        results = [Result.from_dict(r, event_id) for r in results_data]
        return cls(
            id=str(data.get('id', '')),
            name=data.get('name', ''),
            number=data.get('number', 1),
            results=results,
            event_id=event_id
        )

@dataclass
class Event:
    id: str
    name: str
    rounds: List[Round] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        event_data = data.get('event', {})
        event_id = event_data.get('id', '333')
        rounds_data = data.get('rounds', [])
        rounds = []
        for round_data in rounds_data:
            if 'results' in round_data:
                rounds.append(Round.from_dict(round_data, event_id))
            else:
                rounds.append(Round(
                    id=str(round_data.get('id', '')),
                    name=round_data.get('name', ''),
                    number=round_data.get('number', 1),
                    results=[],
                    event_id=event_id
                ))
        return cls(
            id=event_id,
            name=event_data.get('name', 'Unknown'),
            rounds=rounds
        )
    
    @property
    def all_results(self) -> List[Result]:
        results = []
        for round_data in self.rounds:
            results.extend(round_data.results)
        return results
    
    @property
    def unique_competitors(self) -> int:
        competitor_ids = set()
        for result in self.all_results:
            if result.has_attempted:
                competitor_ids.add(result.person.id)
        return len(competitor_ids)

def generate_wca_competition_id(competition_name: str) -> str:
    """
    Genera el ID de competencia WCA a partir del nombre del torneo.
    Ejemplo: "Avenida Chile XXXI 2026" -> "AvenidaChileXXXI2026"
    """
    import re
    # Eliminar caracteres especiales y espacios
    # Mantener solo letras, números y espacios
    cleaned = re.sub(r'[^\w\s]', '', competition_name)
    # Eliminar espacios
    wca_id = cleaned.replace(' ', '')
    return wca_id

@dataclass
class StaffMember:
    """Representa un organizador o delegado"""
    name: str
    wca_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StaffMember':
        return cls(
            name=data.get('name', 'Unknown'),
            wca_id=data.get('wcaId')
        )
    
    @property
    def wca_profile_url(self) -> Optional[str]:
        """Retorna la URL del perfil WCA si tiene wcaId"""
        if self.wca_id:
            return f"https://worldcubeassociation.org/persons/{self.wca_id}"
        return None

@dataclass
class Competition:
    id: str
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    competitor_limit: Optional[int] = None
    competitors: List[Person] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    organizers: List[StaffMember] = field(default_factory=list)
    delegates: List[StaffMember] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Competition':
        start_date = None
        end_date = None
        if data.get('startDate'):
            try:
                start_date = date.fromisoformat(data['startDate'].split('T')[0])
            except:
                pass
        if data.get('endDate'):
            try:
                end_date = date.fromisoformat(data['endDate'].split('T')[0])
            except:
                pass
        
        competitors_data = data.get('competitors', [])
        competitors = [Person.from_dict(c) for c in competitors_data]
        
        events_data = data.get('competitionEvents', [])
        events = [Event.from_dict(e) for e in events_data]
        
        # Parsear organizadores
        organizers_data = data.get('organizers', [])
        organizers = [StaffMember.from_dict(o) for o in organizers_data]
        
        # Parsear delegados
        delegates_data = data.get('delegates', [])
        delegates = [StaffMember.from_dict(d) for d in delegates_data]
        
        return cls(
            id=str(data.get('id', '')),
            name=data.get('name', 'Unknown Competition'),
            start_date=start_date,
            end_date=end_date,
            competitor_limit=data.get('competitorLimit'),
            competitors=competitors,
            events=events,
            organizers=organizers,
            delegates=delegates
        )
    
    @property
    def competitor_count(self) -> int:
        competitor_ids = set()
        for event in self.events:
            for result in event.all_results:
                if result.has_attempted:
                    competitor_ids.add(result.person.id)
        return len(competitor_ids)
    
    @property
    def event_count(self) -> int:
        return len(self.events)

# ==================== API CLIENT ====================

class WCALiveClient:
    def __init__(self, api_url: str = WCA_LIVE_API_URL):
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        payload = {'query': query, 'variables': variables or {}}
        try:
            response = self.session.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            if 'errors' in data:
                raise Exception(f"GraphQL Error: {data['errors']}")
            return data.get('data', {})
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexion: {str(e)}")
        except Exception as e:
            raise Exception(f"Error al ejecutar query: {str(e)}")
    
    def get_competition(self, competition_id: str) -> Dict[str, Any]:
        query = """
        query GetCompetition($id: ID!) {
            competition(id: $id) {
                id
                name
                startDate
                endDate
                competitorLimit
                competitors { id name wcaId country { name } }
                competitionEvents {
                    id
                    event { id name }
                    rounds { id name number }
                }
            }
        }
        """
        return self.execute_query(query, {'id': competition_id})
    
    def get_competition_staff(self, competition_name: str) -> Dict[str, Any]:
        """Obtiene organizadores y delegados usando la API REST de WCA"""
        try:
            # Generar ID de WCA a partir del nombre del torneo
            wca_competition_id = generate_wca_competition_id(competition_name)
            
            # Intentar obtener desde la API REST de WCA
            rest_url = f"https://worldcubeassociation.org/api/v0/competitions/{wca_competition_id}"
            response = self.session.get(rest_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            staff_info = {
                'organizers': [],
                'delegates': []
            }
            
            # Extraer organizadores
            if 'organizers' in data:
                for org in data['organizers']:
                    staff_info['organizers'].append({
                        'name': org.get('name', 'Unknown'),
                        'wcaId': org.get('wca_id')
                    })
            
            # Extraer delegados
            if 'delegates' in data:
                for delg in data['delegates']:
                    staff_info['delegates'].append({
                        'name': delg.get('name', 'Unknown'),
                        'wcaId': delg.get('wca_id')
                    })
            
            return staff_info
        except Exception as e:
            # Si falla, retornar estructura vacia
            print(f"Advertencia: No se pudieron obtener datos de staff: {e}")
            return {'organizers': [], 'delegates': []}
    
    def get_round_results(self, round_id: str) -> Dict[str, Any]:
        query = """
        query GetRoundResults($id: ID!) {
            round(id: $id) {
                id
                name
                number
                results {
                    person { id name wcaId }
                    attempts { result }
                    best
                    average
                    ranking
                    singleRecordTag
                    averageRecordTag
                }
            }
        }
        """
        return self.execute_query(query, {'id': round_id})
    
    def get_competition_with_all_results(self, competition_id: str) -> Dict[str, Any]:
        competition_data = self.get_competition(competition_id)
        if not competition_data or 'competition' not in competition_data:
            return competition_data
        
        competition = competition_data['competition']
        
        # Obtener informacion de staff (organizadores y delegados) usando el nombre del torneo
        competition_name = competition.get('name', '')
        staff_info = self.get_competition_staff(competition_name)
        competition['organizers'] = staff_info.get('organizers', [])
        competition['delegates'] = staff_info.get('delegates', [])
        
        for event in competition.get('competitionEvents', []):
            for round_data in event.get('rounds', []):
                round_id = round_data['id']
                try:
                    round_results = self.get_round_results(round_id)
                    if round_results and 'round' in round_results:
                        round_data['results'] = round_results['round']['results']
                    else:
                        round_data['results'] = []
                except Exception as e:
                    print(f"Advertencia: No se pudieron obtener resultados para ronda {round_id}: {e}")
                    round_data['results'] = []
        
        return competition_data

class WCAOfficialClient:
    """Cliente para la API oficial de WCA (torneos publicados)"""
    
    def __init__(self):
        self.base_url = "https://www.worldcubeassociation.org/api/v0"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'WCA-Tournament-Analyzer/1.0'
        })
    
    def get_competition(self, competition_id: str) -> Dict[str, Any]:
        """Obtiene informacion de una competencia publicada"""
        url = f"{self.base_url}/competitions/{competition_id}"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Transformar datos al formato compatible con nuestro modelo
            competition = {
                'id': data.get('id'),
                'name': data.get('name'),
                'startDate': data.get('start_date'),
                'endDate': data.get('end_date'),
                'competitorLimit': data.get('competitor_limit'),
                'competitors': [],  # Se llenara con los resultados
                'organizers': [{'name': org.get('name'), 'wcaId': org.get('wca_id')} 
                              for org in data.get('organizers', [])],
                'delegates': [{'name': delg.get('name'), 'wcaId': delg.get('wca_id')} 
                             for delg in data.get('delegates', [])],
                'competitionEvents': []
            }
            
            return {'competition': competition}
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error al obtener competencia: {str(e)}")
    
    def get_competition_results(self, competition_id: str) -> Dict[str, Any]:
        """Obtiene todos los resultados de una competencia"""
        url = f"{self.base_url}/competitions/{competition_id}/results"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error al obtener resultados: {str(e)}")
    
    def get_competition_competitors(self, competition_id: str) -> Dict[str, Any]:
        """Obtiene la lista de competidores"""
        url = f"{self.base_url}/competitions/{competition_id}/competitors"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error al obtener competidores: {str(e)}")
    
    def get_competition_with_all_results(self, competition_id: str) -> Dict[str, Any]:
        """Obtiene competencia con todos los resultados"""
        # Obtener informacion basica
        comp_data = self.get_competition(competition_id)
        if not comp_data or 'competition' not in comp_data:
            return comp_data
        
        competition = comp_data['competition']
        
        # Obtener resultados primero (esto también nos da los competidores)
        try:
            results_data = self.get_competition_results(competition_id)
            
            # Extraer competidores únicos de los resultados
            competitors_dict = {}
            
            # Agrupar resultados por evento y ronda
            events_dict = {}
            
            for result in results_data:
                # Extraer información del competidor (API de WCA usa 'name' no 'person_name')
                person_name = result.get('name', 'Unknown')
                person_wca_id = result.get('wca_id')
                # Usar wca_id como ID, si no existe usar el nombre
                person_id = str(person_wca_id) if person_wca_id else person_name
                
                # Guardar competidor único
                if person_id not in competitors_dict:
                    competitors_dict[person_id] = {
                        'id': person_id,
                        'name': person_name,
                        'wcaId': person_wca_id,
                        'country': {'name': result.get('country_iso2', 'Unknown')}
                    }
                
                event_id = result.get('event_id')
                round_type = result.get('round_type_id', '')
                
                if event_id not in events_dict:
                    events_dict[event_id] = {
                        'id': event_id,
                        'event': {'id': event_id, 'name': get_event_display_name(event_id)},
                        'rounds': {}
                    }
                
                if round_type not in events_dict[event_id]['rounds']:
                    events_dict[event_id]['rounds'][round_type] = {
                        'id': f"{event_id}_{round_type}",
                        'name': round_type,
                        'number': 1,
                        'results': []
                    }
                
                # Transformar resultado al formato de WCA Live
                attempts = []
                
                # Obtener el format_id para saber el numero de intentos
                format_id = result.get('format_id', 'a')
                
                # Mapeo de format_id a numero de intentos
                format_to_attempts = {
                    '1': 1,  # 1 intento (ej: 333fm)
                    '3': 3,  # 3 intentos (ej: 666, 777)
                    'm': 3,  # 3 intentos (multi-blind)
                    'a': 5,  # 5 intentos (average)
                }
                expected_attempts = format_to_attempts.get(format_id, 5)
                
                # Obtener los intentos de la API
                raw_attempts = result.get('attempts', [])
                if raw_attempts:
                    # Usar la cantidad correcta de intentos segun el formato
                    for i, attempt in enumerate(raw_attempts[:expected_attempts]):
                        if isinstance(attempt, dict) and 'result' in attempt:
                            attempts.append({'result': attempt['result'], 'event_id': event_id})
                        elif isinstance(attempt, int):
                            attempts.append({'result': attempt, 'event_id': event_id})
                else:
                    # Fallback: usar value1, value2, etc.
                    for i in range(1, expected_attempts + 1):
                        val = result.get(f'value{i}')
                        if val is not None and val != 0:
                            attempts.append({'result': val, 'event_id': event_id})
                
                events_dict[event_id]['rounds'][round_type]['results'].append({
                    'person': {
                        'id': person_id,
                        'name': person_name,
                        'wcaId': person_wca_id
                    },
                    'attempts': attempts,
                    'best': result.get('best', 0),
                    'average': result.get('average', 0),
                    'ranking': result.get('position'),
                    'singleRecordTag': result.get('regional_single_record'),
                    'averageRecordTag': result.get('regional_average_record')
                })
            
            # Convertir diccionario de competidores a lista
            competition['competitors'] = list(competitors_dict.values())
            
            # Convertir a lista de eventos
            competition['competitionEvents'] = []
            for event_id, event_data in events_dict.items():
                event_data['rounds'] = list(event_data['rounds'].values())
                competition['competitionEvents'].append(event_data)
            
        except Exception as e:
            print(f"Advertencia: No se pudieron obtener resultados: {e}")
            competition['competitors'] = []
            competition['competitionEvents'] = []
        
        return comp_data

# ==================== ANALISIS ====================

def format_time(centiseconds: int, event_id: str = '333') -> str:
    if centiseconds == -1:
        return "DNF"
    elif centiseconds == -2:
        return "DNS"
    elif centiseconds <= 0:
        return "N/A"
    
    # 333fm (Fewest Moves) se mide en numero de movimientos, no tiempo
    if event_id == '333fm':
        return str(centiseconds)
    
    total_seconds = centiseconds / 100
    if total_seconds < 60:
        return f"{total_seconds:.2f}"
    elif total_seconds < 3600:
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:05.2f}"
    else:
        hours = int(total_seconds // 3600)
        remaining = total_seconds % 3600
        minutes = int(remaining // 60)
        seconds = remaining % 60
        return f"{hours}:{minutes:02d}:{seconds:05.2f}"

def get_fastest_single(event: Event) -> Optional[Tuple[Result, int]]:
    best_result = None
    best_time = float('inf')
    for result in event.all_results:
        valid = result.valid_attempts
        if valid:
            best_single = min(valid)
            if best_single < best_time:
                best_time = best_single
                best_result = result
    return (best_result, best_time) if best_result else None

def get_slowest_single(event: Event) -> Optional[Tuple[Result, int]]:
    worst_result = None
    worst_time = 0
    for result in event.all_results:
        for attempt in result.attempts:
            if attempt.is_valid and attempt.result > worst_time:
                worst_time = attempt.result
                worst_result = result
    return (worst_result, worst_time) if worst_result else None

def get_fastest_average(event: Event) -> Optional[Tuple[Result, int]]:
    best_result = None
    best_avg = float('inf')
    for result in event.all_results:
        if result.average > 0 and result.average < best_avg:
            best_avg = result.average
            best_result = result
    return (best_result, best_avg) if best_result else None

def get_slowest_average(event: Event) -> Optional[Tuple[Result, int]]:
    worst_result = None
    worst_avg = 0
    for result in event.all_results:
        if result.average > 0 and result.average > worst_avg:
            worst_avg = result.average
            worst_result = result
    return (worst_result, worst_avg) if worst_result else None

def calculate_category_average_time(event: Event) -> Optional[float]:
    person_averages = []
    competitor_ids = set()
    for result in event.all_results:
        if result.has_attempted:
            competitor_ids.add(result.person.id)
    
    for person_id in competitor_ids:
        all_valid_times = []
        for result in event.all_results:
            if result.person.id == person_id:
                all_valid_times.extend(result.valid_attempts)
        if all_valid_times:
            person_averages.append(mean(all_valid_times))
    
    return mean(person_averages) if person_averages else None

def calculate_completion_ratio(event: Event) -> Tuple[float, int, int]:
    # Contar solo intentos realizados (no ceros = intentos no hechos)
    # 0 = no intento, -1 = DNF, positivo = completado
    total = sum(sum(1 for a in r.attempts if a.result != 0) for r in event.all_results)
    completed = sum(sum(1 for a in r.attempts if a.is_completed) for r in event.all_results)
    if total == 0:
        return (0.0, 0, 0)
    return (completed / total, completed, total)

def count_personal_records(event: Event) -> Dict[str, int]:
    # Contar personas unicas que rompieron PR (no resultados individuales)
    single_persons = set()
    average_persons = set()
    
    for result in event.all_results:
        if result.regional_single_record:
            single_persons.add(result.person.id)
        if result.regional_average_record:
            average_persons.add(result.person.id)
    
    return {'single': len(single_persons), 'average': len(average_persons)}

class EventAnalysis:
    def __init__(self, event: Event):
        self.event = event
        self.event_id = event.id
        self.event_name = event.name
        self.competitors_count = event.unique_competitors
        self.fastest_single = get_fastest_single(event)
        self.slowest_single = get_slowest_single(event)
        self.fastest_average = get_fastest_average(event)
        self.slowest_average = get_slowest_average(event)
        self.average_time = calculate_category_average_time(event)
        self.completion_ratio, self.completed_solves, self.total_solves = calculate_completion_ratio(event)
        self.records_count = count_personal_records(event)

class NewCompetitorAnalysis:
    """Analisis de competidores nuevos (sin WCA ID)"""
    def __init__(self, event: Event):
        self.event = event
        self.event_id = event.id
        self.event_name = event.name
        # Filtrar competidores nuevos (sin WCA ID)
        self.new_competitors_results = [r for r in event.all_results if r.has_attempted and r.person.wca_id is None]
        self.new_competitors_count = len(self.new_competitors_results)
    
    def get_fastest_single(self) -> Optional[Tuple[Result, int]]:
        """Competidor nuevo mas rapido en single"""
        if not self.new_competitors_results:
            return None
        best = None
        best_time = float('inf')
        for result in self.new_competitors_results:
            valid = result.valid_attempts
            if valid:
                best_single = min(valid)
                if best_single < best_time:
                    best_time = best_single
                    best = result
        return (best, best_time) if best else None
    
    def get_fastest_average(self) -> Optional[Tuple[Result, int]]:
        """Competidor nuevo mas rapido en average"""
        if not self.new_competitors_results:
            return None
        best = None
        best_avg = float('inf')
        for result in self.new_competitors_results:
            if result.average > 0 and result.average < best_avg:
                best_avg = result.average
                best = result
        return (best, best_avg) if best else None

class TournamentAnalysis:
    def __init__(self, competition: Competition):
        self.competition = competition
        self.events_analysis = [EventAnalysis(event) for event in competition.events]
        self.new_competitors_analysis = [NewCompetitorAnalysis(event) for event in competition.events]
    
    @property
    def total_new_competitors(self) -> int:
        """Total de competidores nuevos unicos en el torneo"""
        new_ids = set()
        for nca in self.new_competitors_analysis:
            for result in nca.new_competitors_results:
                new_ids.add(result.person.id)
        return len(new_ids)
    
    @property
    def categories_count(self) -> int:
        return len(self.events_analysis)
    
    @property
    def competitors_per_category(self) -> Dict[str, int]:
        return {ea.event_name: ea.competitors_count for ea in self.events_analysis}
    
    @property
    def total_personal_records(self) -> Dict[str, int]:
        single = sum(ea.records_count['single'] for ea in self.events_analysis)
        average = sum(ea.records_count['average'] for ea in self.events_analysis)
        return {'single': single, 'average': average}
    
    @property
    def overall_completion_ratio(self) -> float:
        total = sum(ea.total_solves for ea in self.events_analysis)
        completed = sum(ea.completed_solves for ea in self.events_analysis)
        return completed / total if total > 0 else 0.0

# ==================== GRAFICO DE DENSIDAD ====================

def create_density_chart(event_analysis, event_id: str):
    """Genera un grafico de densidad/histograma de los tiempos de la categoria en formato PDF vectorial"""
    # Obtener todos los tiempos validos (excluyendo DNF/DNS)
    all_times = []
    for result in event_analysis.event.all_results:
        for attempt in result.attempts:
            if attempt.is_valid:
                all_times.append(attempt.result)
    
    if not all_times or len(all_times) < 2:
        return None
    
    # 333fm (Fewest Moves) no se convierte a segundos
    is_fewest_moves = (event_id == '333fm')
    
    if is_fewest_moves:
        times_values = all_times  # Ya esta en numero de movimientos
    else:
        times_values = [t / 100 for t in all_times]  # Convertir centisegundos a segundos
    
    max_time = max(times_values)
    mean_time = np.mean(times_values)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(5, 2.5))
    
    # Crear histograma con densidad (solo azul)
    ax.hist(times_values, bins=min(50, len(times_values)//2 + 10), 
            density=True, alpha=0.7, color='#3498DB', edgecolor='white')
    
    # Agregar linea vertical en la media
    if is_fewest_moves:
        mean_label = f'Media: {int(mean_time)}'
    else:
        mean_label = f'Media: {format_time(int(mean_time * 100), event_id)}'
    ax.axvline(mean_time, color='#E74C3C', linestyle='--', linewidth=2, label=mean_label)
    
    # Agregar linea de densidad (KDE)
    from scipy import stats
    try:
        kde = stats.gaussian_kde(times_values)
        x_range = np.linspace(min(times_values), max(times_values), 100)
        ax.plot(x_range, kde(x_range), color='#E74C3C', linewidth=2)
    except:
        pass  # Si falla el KDE, solo mostrar histograma
    
    # Configurar ejes
    ax.set_ylabel('Densidad', fontsize=8)
    ax.set_title(f'Distribucion de tiempos - {event_analysis.event_name}', fontsize=9, fontweight='bold')
    ax.tick_params(axis='both', labelsize=7)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Agregar leyenda
    ax.legend(loc='upper right', fontsize=7, framealpha=0.9)
    
    # Formatear eje X segun el tipo de categoria
    if is_fewest_moves:
        ax.set_xlabel('Movimientos', fontsize=8)
    elif max_time >= 60:
        # Formato MM:SS para tiempos mayores a 1 minuto
        def format_time_axis(x, pos):
            minutes = int(x // 60)
            seconds = int(x % 60)
            if minutes > 0:
                return f"{minutes}:{seconds:02d}"
            return f"{seconds}"
        
        from matplotlib.ticker import FuncFormatter
        ax.xaxis.set_major_formatter(FuncFormatter(format_time_axis))
        ax.set_xlabel('Tiempo (min:seg)', fontsize=8)
    else:
        ax.set_xlabel('Tiempo (segundos)', fontsize=8)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Guardar en buffer como SVG vectorial (alta calidad)
    buf = io.BytesIO()
    plt.savefig(buf, format='svg', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf.getvalue()

# ==================== PDF GENERATOR ====================

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from svglib.svglib import svg2rlg
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.pdfgen import canvas

class PDFTemplate:
    """Template para manejar el pie de pagina en todas las paginas"""
    def __init__(self, competition_name, competition_date):
        self.competition_name = competition_name
        self.competition_date = competition_date
    
    def __call__(self, canvas, doc):
        # Pie de pagina
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#7F8C8D'))
        
        # Texto del pie: Nombre del torneo | Fecha | Pagina X
        footer_text = f"{self.competition_name}"
        if self.competition_date:
            footer_text += f"  |  {self.competition_date}"
        footer_text += f"  |  Pagina {doc.page}"
        
        # Dibujar linea decorativa arriba del pie de pagina
        canvas.setStrokeColor(colors.HexColor('#BDC3C7'))
        canvas.line(50, 45, A4[0]-50, 45)
        
        # Dibujar pie de pagina
        canvas.drawCentredString(A4[0]/2, 28, footer_text)
        canvas.restoreState()

def generate_pdf(analysis: TournamentAnalysis, output_path: str, use_wca_live: bool = False):
    comp = analysis.competition
    
    # Preparar fecha para el pie de pagina
    comp_date = ""
    if comp.start_date and comp.end_date:
        if comp.start_date == comp.end_date:
            comp_date = comp.start_date.strftime('%d/%m/%Y')
        else:
            comp_date = f"{comp.start_date.strftime('%d/%m/%Y')} - {comp.end_date.strftime('%d/%m/%Y')}"
    elif comp.start_date:
        comp_date = comp.start_date.strftime('%d/%m/%Y')
    
    from reportlab.platypus import BaseDocTemplate
    
    # Crear documento
    doc = BaseDocTemplate(
        output_path, 
        pagesize=A4, 
        rightMargin=50, 
        leftMargin=50, 
        topMargin=50, 
        bottomMargin=50
    )
    
    # Frame para el contenido
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    
    # Template con pie de pagina
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#7F8C8D'))
        
        footer_text = f"{comp.name}"
        if comp_date:
            footer_text += f"  |  {comp_date}"
        footer_text += f"  |  Pagina {doc.page}"
        
        canvas.setStrokeColor(colors.HexColor('#BDC3C7'))
        canvas.line(50, 45, A4[0]-50, 45)
        canvas.drawCentredString(A4[0]/2, 28, footer_text)
        canvas.restoreState()
    
    template = PageTemplate(id='default', frames=[frame], onPage=add_footer)
    doc.addPageTemplates([template])
    
    # Contadores para tablas y figuras
    table_counter = 0
    figure_counter = 0
    
    styles = getSampleStyleSheet()
    story = []
    
    # Estilos
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#2C3E50'), spaceAfter=15, alignment=TA_CENTER)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#34495E'), spaceAfter=10)
    event_style = ParagraphStyle('Event', parent=styles['Heading3'], fontSize=11, textColor=colors.HexColor('#2980B9'), spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9)
    table_caption_style = ParagraphStyle('TableCaption', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#555555'), spaceBefore=4, spaceAfter=8, alignment=TA_CENTER)
    figure_caption_style = ParagraphStyle('FigureCaption', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#555555'), spaceBefore=4, spaceAfter=8, alignment=TA_CENTER)
    index_style = ParagraphStyle('Index', parent=styles['Normal'], fontSize=10, spaceAfter=6)
    index_heading_style = ParagraphStyle('IndexHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#34495E'), spaceAfter=15, alignment=TA_CENTER)
    
    # PORTADA - Centrada verticalmente
    story.append(Spacer(1, 3.5*inch))
    story.append(Paragraph("INFORME EJECUTIVO", title_style))
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph("Analisis de Torneo WCA LIVE", ParagraphStyle('Subtitle', fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#7F8C8D'))))
    story.append(Spacer(1, 1.2*inch))
    story.append(Paragraph(comp.name, ParagraphStyle('CompName', fontSize=16, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.HexColor('#2C3E50'))))
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y')}", ParagraphStyle('Date', fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#95A5A6'))))
    
    # Salto de pagina despues de la portada
    story.append(PageBreak())
    
    # INDICE MEJORADO CON HIPERVINCULOS
    story.append(Paragraph("INDICE", ParagraphStyle('IndexTitle', parent=heading_style, fontSize=16, spaceAfter=20, alignment=TA_CENTER)))
    
    # Crear tabla de indice con hipervinculos
    index_data = [[Paragraph("<b>Contenido</b>", body_style), Paragraph("<b>Pag.</b>", body_style)]]
    
    # Definir secciones y sus bookmarks
    section4_number = "3" if not use_wca_live else "4"
    index_sections = [
        ("1. Informacion del Torneo", "section1", "3"),
        ("2. Definiciones y Metodologia", "section2", "4"),
    ]
    
    if use_wca_live:
        index_sections.append(("3. Competidores Nuevos", "section3", "5"))
    
    index_sections.append((f"{section4_number}. Analisis por Categoria", "section4", section4_number))
    
    for section_name, bookmark, page in index_sections:
        link_text = f'<a href="#{bookmark}" color="#2980B9">{section_name}</a>'
        index_data.append([Paragraph(link_text, body_style), Paragraph(page, body_style)])
    
    # Agregar subsecciones (categorias) dentro de Analisis por Categoria
    index_data.append([Paragraph("<b>Categorias:</b>", ParagraphStyle('SubIndex', parent=body_style, fontSize=9, textColor=colors.HexColor('#34495E'), spaceBefore=10)), Paragraph("", body_style)])
    for i, ea in enumerate(analysis.events_analysis, 1):
        sub_link = f'<a href="#cat_{ea.event_id}" color="#2980B9">{section4_number}.{i} {ea.event_name}</a>'
        index_data.append([Paragraph(f"   {sub_link}", body_style), Paragraph("", body_style)])
    
    index_table = Table(index_data, colWidths=[4.5*inch, 0.8*inch])
    index_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),  # Azul mas claro
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8F9FA')]),
    ]))
    story.append(index_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Salto de pagina antes del capitulo 1
    story.append(PageBreak())
    
    # SECCION 1: INFORMACION DEL TORNEO (con bookmark)
    story.append(Paragraph("<a name='section1'></a>1. INFORMACION DEL TORNEO", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    info_data = [
        ['Campo', 'Valor'],
        ['Nombre', comp.name],
        ['ID', comp.id],
        ['Fecha Inicio', comp.start_date.strftime('%d/%m/%Y') if comp.start_date else 'N/A'],
        ['Fecha Fin', comp.end_date.strftime('%d/%m/%Y') if comp.end_date else 'N/A'],
        ['Competidores', str(comp.competitor_count)],
        ['Categorias', str(comp.event_count)],
    ]
    
    table_counter += 1
    info_table = Table(info_data, colWidths=[1.8*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Paragraph(f"Tabla {table_counter}: Informacion General del Torneo", table_caption_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Tabla de Delegados
    if comp.delegates:
        delegate_data = [[Paragraph("<b>Nombre</b>", body_style), Paragraph("<b>WCA ID</b>", body_style)]]
        for delegate in comp.delegates:
            if delegate.wca_id and delegate.wca_profile_url:
                wca_link = f'<a href="{delegate.wca_profile_url}" color="blue">{delegate.wca_id}</a>'
                delegate_data.append([Paragraph(delegate.name, body_style), Paragraph(wca_link, body_style)])
            else:
                delegate_data.append([Paragraph(delegate.name, body_style), Paragraph('N/A', body_style)])
        
        table_counter += 1
        delegate_table = Table(delegate_data, colWidths=[4*inch, 1.8*inch])
        delegate_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8E44AD')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F4ECF7')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D7BDE2')),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        story.append(delegate_table)
        story.append(Paragraph(f"Tabla {table_counter}: Delegados del Torneo", table_caption_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Tabla de Organizadores
    if comp.organizers:
        organizer_data = [[Paragraph("<b>Nombre</b>", body_style), Paragraph("<b>WCA ID</b>", body_style)]]
        for organizer in comp.organizers:
            if organizer.wca_id and organizer.wca_profile_url:
                wca_link = f'<a href="{organizer.wca_profile_url}" color="blue">{organizer.wca_id}</a>'
                organizer_data.append([Paragraph(organizer.name, body_style), Paragraph(wca_link, body_style)])
            else:
                organizer_data.append([Paragraph(organizer.name, body_style), Paragraph('N/A', body_style)])
        
        table_counter += 1
        organizer_table = Table(organizer_data, colWidths=[4*inch, 1.8*inch])
        organizer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E8F8F5')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#A9DFBF')),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        story.append(organizer_table)
        story.append(Paragraph(f"Tabla {table_counter}: Organizadores del Torneo", table_caption_style))
        story.append(Spacer(1, 0.1*inch))
    
    # SECCION 2: DEFINICIONES Y METODOLOGIA (AHORA ES EL SEGUNDO CAPITULO)
    story.append(Spacer(1, 0.25*inch))
    story.append(Paragraph("<a name='section2'></a>2. DEFINICIONES Y METODOLOGIA", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    definitions = [
        ("Promedio de Tiempos (Average)", 
         "El promedio calculado segun las reglas de la WCA. Para la mayoria de categorias, se elimina el mejor y peor tiempo de 5 intentos, y se promedia los 3 tiempos restantes. En categorias como 3x3x3 Blindfolded, se promedian 3 de 3 intentos."),
        
        ("Competidor Nuevo", 
         "Un competidor que no tiene WCA ID asignado, indicando que es su primera participacion en torneos oficiales de la WCA."),
        
        ("Records Personales (PR - Personal Record)", 
         "Un competidor logra un record personal cuando su tiempo single o average es mejor que cualquier resultado anterior registrado en la base de datos de la WCA para esa categoria. Se indica con 'S' para single y 'A' para average."),
        
        ("Grafico de Densidad", 
         "Visualizacion que muestra la distribucion de todos los tiempos validos de una categoria. El eje X representa el tiempo y el eje Y la densidad de probabilidad. La linea roja punteada indica el tiempo promedio de la categoria. Permite identificar la concentracion de tiempos y la dispersion de los resultados."),
        
        ("Media vs Promedio",
         "En el grafico de densidad, la 'Media' representa el promedio simple de todos los tiempos validos de todos los competidores en esa categoria. En la tabla de resultados, el 'Promedio' se calcula de forma diferente: primero se calcula el promedio de cada competidor (incluyendo todos sus intentos de todas las rondas, excluyendo DNFs), y luego se calcula el promedio de esos promedios individuales de todos los competidores."),
        
        ("DNF (Did Not Finish)", 
         "Abreviatura de 'Did Not Finish' (No Termino). Se asigna cuando un competidor inicia el intento pero no completa el cubo correctamente dentro del limite de tiempo."),
        
        ("DNS (Did Not Start)", 
         "Abreviatura de 'Did Not Start' (No Inicio). Se asigna cuando un competidor esta registrado para una ronda pero no realiza ningun intento."),
        
        ("Ratio de Completacion", 
         "Porcentaje de soluciones completadas exitosamente respecto al total de soluciones intentadas. Se calcula como: (soluciones completadas / soluciones totales) x 100. Una solucion se considera completada cuando el competidor termina el cubo correctamente dentro del limite de tiempo, sin importar el tiempo obtenido."),
    ]
    
    for term, definition in definitions:
        story.append(Paragraph(f"<b>{term}</b>", ParagraphStyle('Term', parent=body_style, fontSize=9, textColor=colors.HexColor('#2980B9'), spaceBefore=8)))
        story.append(Paragraph(definition, ParagraphStyle('Definition', parent=body_style, fontSize=8, spaceAfter=6, leading=12)))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("<b>Nota Metodologica:</b>", ParagraphStyle('Note', parent=body_style, fontSize=9, textColor=colors.HexColor('#34495E'))))
    story.append(Paragraph("Los datos utilizados en este informe provienen de WCA Live API y representan los resultados oficiales registrados durante el torneo. Los tiempos se expresan en segundos o minutos:segundos segun la duracion de la categoria. Los calculos estadisticos excluyen los intentos DNF y DNS.", 
                           ParagraphStyle('NoteBody', parent=body_style, fontSize=8, leading=12)))
    story.append(Spacer(1, 0.15*inch))
    
    # SECCION 3: COMPETIDORES NUEVOS (solo para WCA Live)
    if use_wca_live:
        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph("<a name='section3'></a>3. COMPETIDORES NUEVOS", heading_style))
    
    if analysis.total_new_competitors > 0:
        story.append(Paragraph("Este capitulo presenta un analisis de los competidores que participaron por primera vez en un torneo oficial de la WCA. Se muestra el total de competidores nuevos en este torneo, asi como los mejores resultados obtenidos por estos en cada categoria, tanto en single como en average.", body_style))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"<b>Total Competidores Nuevos:</b> {analysis.total_new_competitors}", body_style))
        story.append(Spacer(1, 0.1*inch))
        
        new_comp_data = [['Categoria', 'Single Mas Rapido', 'Average Mas Rapido']]
        has_new_competitors = False
        
        for nca in analysis.new_competitors_analysis:
            if nca.new_competitors_count > 0:
                has_new_competitors = True
                fastest_single = nca.get_fastest_single()
                fastest_average = nca.get_fastest_average()
                
                single_text = "N/A"
                if fastest_single:
                    person = fastest_single[0].person
                    time = format_time(fastest_single[1], nca.event_id)
                    single_text = f"{time} - {person.name}"
                
                avg_text = "N/A"
                if fastest_average:
                    person = fastest_average[0].person
                    time = format_time(fastest_average[1], nca.event_id)
                    avg_text = f"{time} - {person.name}"
                
                new_comp_data.append([nca.event_name, single_text, avg_text])
        
        if has_new_competitors:
            table_counter += 1
            new_comp_table = Table(new_comp_data, colWidths=[2*inch, 2.3*inch, 2.3*inch])
            new_comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E67E22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FEF5E7')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FAD7A0')),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ]))
            story.append(new_comp_table)
            story.append(Paragraph(f"Tabla {table_counter}: Mejores Resultados de Competidores Nuevos por Categoria", table_caption_style))
            story.append(Spacer(1, 0.15*inch))
    
    # SECCION 4: ANALISIS POR CATEGORIA (Contenido del antiguo Resumen Ejecutivo integrado)
    story.append(Spacer(1, 0.25*inch))
    section4_title = "3. ANALISIS POR CATEGORIA" if not use_wca_live else "4. ANALISIS POR CATEGORIA"
    story.append(Paragraph(f"<a name='section4'></a>{section4_title}", heading_style))
    story.append(Paragraph("Este capitulo presenta un analisis estadistico detallado de cada categoria del torneo. Se incluye una vision general con la distribucion de competidores por categoria, los records personales obtenidos, y el ratio de completacion. Ademas, para cada categoria se muestra un grafico de densidad con la distribucion de tiempos, los mejores y peores resultados en single y average, y estadisticas adicionales.", body_style))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("<b>Resumen General del Torneo:</b>", ParagraphStyle('SubHeading', parent=body_style, fontSize=10, textColor=colors.HexColor('#34495E'), spaceBefore=6)))
    story.append(Paragraph(f"<b>Total Categorias:</b> {analysis.categories_count}", body_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Tabla de competidores por categoria
    comp_data = [['Categoria', 'Competidores']]
    for name, count in analysis.competitors_per_category.items():
        comp_data.append([name, str(count)])
    
    table_counter += 1
    comp_table = Table(comp_data, colWidths=[4.5*inch, 1.3*inch])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980B9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#EBF5FB')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#AED6F1')),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    story.append(comp_table)
    story.append(Paragraph(f"Tabla {table_counter}: Distribucion de Competidores por Categoria", table_caption_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Grafica de pastel - Distribucion de competidores por categoria
    categories = list(analysis.competitors_per_category.keys())
    counts = list(analysis.competitors_per_category.values())
    
    # Ordenar por cantidad descendente
    sorted_data = sorted(zip(categories, counts), key=lambda x: x[1], reverse=True)
    categories = [x[0] for x in sorted_data]
    counts = [x[1] for x in sorted_data]
    
    fig, ax = plt.subplots(figsize=(9, 9))
    pie_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                  '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
                  '#F8B500', '#00CED1', '#FF69B4', '#32CD32']
    
    wedges, texts, autotexts = ax.pie(
        counts, 
        labels=None,
        autopct='%1.1f%%',
        colors=pie_colors[:len(categories)],
        startangle=90,
        pctdistance=0.6,
        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2)
    )
    
    for i, (wedge, count) in enumerate(zip(wedges, counts)):
        angle = (wedge.theta2 - wedge.theta1)/2. + wedge.theta1
        x = 0.7 * np.cos(np.deg2rad(angle))
        y = 0.7 * np.sin(np.deg2rad(angle))
        ax.text(x, y, categories[i], ha='center', va='center', fontsize=7, fontweight='bold',
                color='white' if i % 2 == 0 else 'black')
    
    ax.set_title('Distribucion de Competidores por Categoria', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close()
    
    img = Image(img_buffer, width=5.5*inch, height=5*inch)
    chart_table = Table([[img]], colWidths=[6*inch])
    chart_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(chart_table)
    story.append(Paragraph(f"Grafica 1: Distribucion de Competidores por Categoria", table_caption_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Records - solo para WCA Live
    if use_wca_live:
        records = analysis.total_personal_records
        story.append(Paragraph(f"<b>Records:</b> {records['single']} Single, {records['average']} Average", body_style))
    story.append(Paragraph(f"<b>Ratio Completacion:</b> {analysis.overall_completion_ratio * 100:.1f}%", body_style))
    story.append(Spacer(1, 0.25*inch))
    story.append(Paragraph("<b>Analisis Detallado por Categoria:</b>", ParagraphStyle('SubHeading2', parent=body_style, fontSize=10, textColor=colors.HexColor('#34495E'), spaceBefore=6)))
    story.append(Spacer(1, 0.1*inch))
    
    section_prefix = "3" if not use_wca_live else "4"
    for i, ea in enumerate(analysis.events_analysis, 1):
        event_id = ea.event_id
        
        # Titulo de categoria con anchor para el indice
        story.append(Paragraph(f"<a name='cat_{event_id}'></a>{section_prefix}.{i} {ea.event_name}", event_style))
        story.append(Paragraph(f"Codigo: {event_id}  |  Competidores: {ea.competitors_count}", body_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Grafico de densidad (SVG vectorial)
        try:
            chart_data = create_density_chart(ea, event_id)
            if chart_data:
                figure_counter += 1
                # Convertir SVG a objeto reportlab
                svg_buffer = io.BytesIO(chart_data)
                chart_img = svg2rlg(svg_buffer)
                # Escalar el grafico
                chart_img.width = 4.5*inch
                chart_img.height = 2.25*inch
                chart_img.scale(4.5*inch/chart_img.width, 2.25*inch/chart_img.height)
                # Alinear el grafico mas a la izquierda con margen negativo
                chart_table = Table([[chart_img]], colWidths=[4.5*inch])
                chart_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), -30),  # Margen negativo para mover mas a la izquierda
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(chart_table)
                story.append(Paragraph(f"Figura {figure_counter}: Distribucion de Tiempos - {ea.event_name}", figure_caption_style))
                story.append(Spacer(1, 0.1*inch))
        except Exception as e:
            pass
        
        # Tabla de resultados
        result_data = [['Tipo', 'Metrica', 'Tiempo', 'Competidor']]
        
        if ea.fastest_single:
            result_data.append(['Single', 'Mas RAPIDO', format_time(ea.fastest_single[1], event_id), ea.fastest_single[0].person.name])
        if ea.slowest_single:
            result_data.append(['Single', 'Mas LENTO', format_time(ea.slowest_single[1], event_id), ea.slowest_single[0].person.name])
        if ea.fastest_average:
            result_data.append(['Average', 'Mas RAPIDO', format_time(ea.fastest_average[1], event_id), ea.fastest_average[0].person.name])
        if ea.slowest_average:
            result_data.append(['Average', 'Mas LENTO', format_time(ea.slowest_average[1], event_id), ea.slowest_average[0].person.name])
        
        if len(result_data) > 1:
            table_counter += 1
            result_table = Table(result_data, colWidths=[0.7*inch, 0.9*inch, 0.9*inch, 3.3*inch])
            result_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, 2), colors.HexColor('#FADBD8')),
                ('TEXTCOLOR', (0, 1), (0, 2), colors.HexColor('#C0392B')),
                ('FONTNAME', (0, 1), (0, 2), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 3), (-1, 4), colors.HexColor('#D6EAF8')),
                ('TEXTCOLOR', (0, 3), (0, 4), colors.HexColor('#2980B9')),
                ('FONTNAME', (0, 3), (0, 4), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
            ]))
            story.append(KeepTogether([result_table, Spacer(1, 0.02*inch)]))
            story.append(Paragraph(f"Tabla {table_counter}: Resumen de Resultados - {ea.event_name}", table_caption_style))
        
        # Estadisticas
        stats = []
        if ea.average_time:
            stats.append(f"Promedio: {format_time(int(ea.average_time), event_id)}")
        stats.append(f"Completadas: {ea.completed_solves}/{ea.total_solves} ({ea.completion_ratio * 100:.1f}%)")
        if ea.records_count['single'] > 0 or ea.records_count['average'] > 0:
            stats.append(f"Records: {ea.records_count['single']}S, {ea.records_count['average']}A")
        
        if stats:
            story.append(Paragraph("  |  ".join(stats), body_style))
            story.append(Spacer(1, 0.08*inch))
    
    doc.build(story)
    print(f"[OK] PDF generado: {output_path}")

# ==================== MAIN ====================

def print_header():
    print("=" * 60)
    print("    ANALIZADOR DE TORNEOS WCA LIVE")
    print("=" * 60)
    print()

def sanitize_filename(name: str) -> str:
    """Limpia el nombre del torneo para usarlo como nombre de archivo"""
    # Caracteres no permitidos en nombres de archivo
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '')
    # Limitar longitud
    return name[:50]

def print_menu():
    """Imprime el menu de seleccion de fuente de datos"""
    print()
    print("=" * 60)
    print("    SELECCIONE EL TIPO DE TORNEO A ANALIZAR")
    print("=" * 60)
    print()
    print("1. Torneo recien finalizado (WCA Live)")
    print("   - El torneo acaba de terminar")
    print("   - Los datos estan en vivo en WCA Live")
    print("   - ID: Numero (ejemplo: 9645)")
    print()
    print("2. Torneo ya publicado (WCA Oficial)")
    print("   - El torneo fue publicado en la WCA")
    print("   - Los datos estan en la base de datos oficial")
    print("   - ID: Texto (ejemplo: AvenidaChile2024)")
    print()

def get_competition_id_from_user():
    """Obtiene el ID del torneo del usuario con explicacion detallada"""
    print()
    print("-" * 60)
    print("INFORMACION IMPORTANTE:")
    print("-" * 60)
    print()
    print("El ID del torneo se encuentra en la URL de la competencia:")
    print()
    print("Para torneos en WCA Live:")
    print("  URL: https://live.worldcubeassociation.org/competitions/9645")
    print("  ID:  9645 (numero)")
    print()
    print("Para torneos publicados en WCA:")
    print("  URL: https://www.worldcubeassociation.org/competitions/AvenidaChile2024")
    print("  ID:  AvenidaChile2024 (texto)")
    print()
    print("-" * 60)
    
    competition_id = input("\nDigite el ID del torneo: ").strip()
    if not competition_id:
        print("Error: Debe proporcionar un ID de torneo.")
        sys.exit(1)
    
    return competition_id

def main():
    parser = argparse.ArgumentParser(
        description='Analizador de Torneos WCA - Analiza torneos en WCA Live o torneos ya publicados',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos de uso:
  python main.py                    # Modo interactivo con menu
  python main.py 9645 --live        # Analizar torneo en WCA Live
  python main.py AvenidaChile2024   # Analizar torneo publicado
        '''
    )
    
    parser.add_argument(
        'competition_id',
        type=str,
        nargs='?',
        default=None,
        help='ID de la competencia (ejemplo: 9645 para WCA Live, AvenidaChile2024 para WCA)'
    )
    
    parser.add_argument(
        '--live',
        action='store_true',
        help='Indica que el torneo esta en WCA Live (usa API de WCA Live)'
    )
    
    parser.add_argument(
        '--wca',
        action='store_true',
        help='Indica que el torneo esta publicado en WCA (usa API oficial de WCA)'
    )
    
    args = parser.parse_args()
    
    print_header()
    
    # Determinar la fuente de datos
    if args.competition_id is None:
        # Modo interactivo - mostrar menu
        print_menu()
        
        while True:
            choice = input("Seleccione una opcion (1 o 2): ").strip()
            if choice in ['1', '2']:
                break
            print("Opcion invalida. Por favor, seleccione 1 o 2.")
        
        use_wca_live = (choice == '1')
        competition_id = get_competition_id_from_user()
    else:
        # Modo argumentos - determinar fuente
        competition_id = args.competition_id
        
        if args.live and args.wca:
            print("Error: No puede usar --live y --wca al mismo tiempo.")
            sys.exit(1)
        elif args.live:
            use_wca_live = True
        elif args.wca:
            use_wca_live = False
        else:
            # Intentar detectar automaticamente
            # Si es solo numeros, probablemente es WCA Live
            # Si tiene letras, probablemente es WCA
            if competition_id.isdigit():
                use_wca_live = True
                print(f"\n[INFO] Detectado como ID de WCA Live (numerico): {competition_id}")
            else:
                use_wca_live = False
                print(f"\n[INFO] Detectado como ID de WCA (alfanumerico): {competition_id}")
    
    print(f"[ID] Competencia: {competition_id}")
    print()
    
    try:
        if use_wca_live:
            print("Conectando a WCA Live API...")
            client = WCALiveClient()
            print("[OK] Conectado a WCA Live")
            
            print("Obteniendo informacion del torneo...")
            raw_data = client.get_competition_with_all_results(competition_id)
            print("[OK] Datos obtenidos de WCA Live")
        else:
            print("Conectando a API oficial de WCA...")
            client = WCAOfficialClient()
            print("[OK] Conectado a WCA")
            
            print("Obteniendo informacion del torneo...")
            raw_data = client.get_competition_with_all_results(competition_id)
            print("[OK] Datos obtenidos de WCA")
        
        print("Procesando datos...")
        if 'competition' not in raw_data:
            raise Exception("No se encontro la competencia. Verifica el ID.")
        
        competition = Competition.from_dict(raw_data['competition'])
        print("[OK] Procesado")
        
        print(f"\n[TORNEO] {competition.name}")
        print(f"[COMPETIDORES] {competition.competitor_count}")
        print(f"[CATEGORIAS] {competition.event_count}")
        print()
        
        print("Analizando datos estadisticos...")
        analysis = TournamentAnalysis(competition)
        print("[OK] Analisis completado")
        
        # Crear directorio output relativo a la ubicacion del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generar nombre de archivo basado en el nombre del torneo
        safe_name = sanitize_filename(competition.name)
        pdf_filename = f"Analis {safe_name}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        
        # Si el archivo existe, se sobrescribe automaticamente
        print(f"\nGenerando PDF: {pdf_filename}")
        generate_pdf(analysis, pdf_path, use_wca_live)
        
        print()
        print("=" * 60)
        print("    INFORME GENERADO EXITOSAMENTE")
        print("=" * 60)
        print()
        print(f"Archivo: {pdf_path}")
        print(f"Ubicacion: {os.path.abspath(pdf_path)}")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("    ERROR")
        print("=" * 60)
        print()
        print(f"{str(e)}")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
