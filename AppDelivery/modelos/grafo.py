"""
Modelo: Grafo
Grafo ponderado y dirigido que representa el mapa vial de Cusco.
Cada nodo = intersección/lugar. Cada arista = calle con distancia/tiempo.
"""

from dataclasses import dataclass, field
from typing import Optional
import math
import json


# ────────────────────────────────────────────────────────────────────────────
#  Nodo del grafo (intersección o punto de interés)
# ────────────────────────────────────────────────────────────────────────────
@dataclass
class Nodo:
    """
    Representa una intersección o lugar en el mapa de Cusco.

    Atributos:
        id_nodo  : Identificador único (ej. "plaza_armas")
        nombre   : Nombre legible
        latitud  : Coordenada GPS real
        longitud : Coordenada GPS real
        sector   : Zona a la que pertenece
        es_deposito: True si es punto de partida de repartidores
    """
    id_nodo    : str
    nombre     : str
    latitud    : float
    longitud   : float
    sector     : str
    es_deposito: bool = False

    def coordenadas(self) -> tuple[float, float]:
        return (self.latitud, self.longitud)

    def to_dict(self) -> dict:
        return {
            "id_nodo"    : self.id_nodo,
            "nombre"     : self.nombre,
            "latitud"    : self.latitud,
            "longitud"   : self.longitud,
            "sector"     : self.sector,
            "es_deposito": self.es_deposito,
        }

    def __repr__(self) -> str:
        return f"Nodo({self.id_nodo} | {self.nombre} | {self.sector})"


# ────────────────────────────────────────────────────────────────────────────
#  Arista del grafo (calle entre dos nodos)
# ────────────────────────────────────────────────────────────────────────────
@dataclass
class Arista:
    """
    Representa una calle entre dos nodos.

    Atributos:
        origen      : id_nodo de origen
        destino     : id_nodo de destino
        distancia_m : Distancia en metros
        tiempo_min  : Tiempo estimado en minutos (con tráfico promedio)
        bloqueada   : True si la calle está cerrada (Backtracking)
        bidireccional: Si la calle es de doble sentido
    """
    origen        : str
    destino       : str
    distancia_m   : float
    tiempo_min    : float
    bloqueada     : bool  = False
    bidireccional : bool  = True

    def to_dict(self) -> dict:
        return {
            "origen"        : self.origen,
            "destino"       : self.destino,
            "distancia_m"   : self.distancia_m,
            "tiempo_min"    : self.tiempo_min,
            "bloqueada"     : self.bloqueada,
            "bidireccional" : self.bidireccional,
        }


# ────────────────────────────────────────────────────────────────────────────
#  Grafo principal
# ────────────────────────────────────────────────────────────────────────────
class Grafo:
    """
    Grafo de adyacencia que representa el mapa vial de Cusco.

    Complejidad espacial: O(V + E)
    donde V = nodos (intersecciones), E = aristas (calles)
    """

    def __init__(self):
        self.nodos  : dict[str, Nodo]        = {}
        self.aristas: dict[str, list[Arista]] = {}   # lista de adyacencia

    # ------------------------------------------------------------------ #
    #  Construcción del grafo                                              #
    # ------------------------------------------------------------------ #
    def agregar_nodo(self, nodo: Nodo):
        """O(1) — agrega un nodo al grafo."""
        self.nodos[nodo.id_nodo] = nodo
        if nodo.id_nodo not in self.aristas:
            self.aristas[nodo.id_nodo] = []

    def agregar_arista(self, arista: Arista):
        """
        O(1) — agrega una arista.
        Si es bidireccional, agrega también la inversa.
        """
        if arista.origen not in self.aristas:
            self.aristas[arista.origen] = []
        self.aristas[arista.origen].append(arista)

        if arista.bidireccional:
            inversa = Arista(
                origen        = arista.destino,
                destino       = arista.origen,
                distancia_m   = arista.distancia_m,
                tiempo_min    = arista.tiempo_min,
                bloqueada     = arista.bloqueada,
                bidireccional = False,   # evitar duplicación
            )
            if arista.destino not in self.aristas:
                self.aristas[arista.destino] = []
            self.aristas[arista.destino].append(inversa)

    # ------------------------------------------------------------------ #
    #  Consultas                                                           #
    # ------------------------------------------------------------------ #
    def vecinos(self, id_nodo: str, solo_libres: bool = True) -> list[Arista]:
        """
        Retorna las aristas salientes de un nodo.
        Si solo_libres=True, excluye calles bloqueadas.
        O(grado(v))
        """
        aristas = self.aristas.get(id_nodo, [])
        if solo_libres:
            return [a for a in aristas if not a.bloqueada]
        return aristas

    def nodo(self, id_nodo: str) -> Optional[Nodo]:
        """O(1)"""
        return self.nodos.get(id_nodo)

    def distancia_euclidiana(self, id_a: str, id_b: str) -> float:
        """
        Distancia en línea recta entre dos nodos (heurística para A*).
        Usa fórmula de Haversine para coordenadas GPS reales.
        O(1)
        """
        a = self.nodos.get(id_a)
        b = self.nodos.get(id_b)
        if not a or not b:
            return float("inf")
        return self._haversine(a.latitud, a.longitud, b.latitud, b.longitud)

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Fórmula de Haversine: distancia real entre dos puntos GPS en metros.
        """
        R = 6_371_000   # radio de la Tierra en metros
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi       = math.radians(lat2 - lat1)
        dlambda    = math.radians(lon2 - lon1)
        a = (math.sin(dphi / 2) ** 2
             + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def bloquear_calle(self, origen: str, destino: str):
        """Marca una calle como bloqueada (para Backtracking)."""
        for arista in self.aristas.get(origen, []):
            if arista.destino == destino:
                arista.bloqueada = True
        for arista in self.aristas.get(destino, []):
            if arista.destino == origen:
                arista.bloqueada = True

    def desbloquear_calle(self, origen: str, destino: str):
        """Desbloquea una calle previamente cerrada."""
        for arista in self.aristas.get(origen, []):
            if arista.destino == destino:
                arista.bloqueada = False
        for arista in self.aristas.get(destino, []):
            if arista.destino == origen:
                arista.bloqueada = False

    def nodo_mas_cercano(self, lat: float, lon: float) -> Optional[str]:
        """
        Dado un punto GPS, retorna el id del nodo más cercano.
        O(V) — útil para asignar id_nodo a pedidos.
        """
        mejor_id   = None
        mejor_dist = float("inf")
        for id_n, nodo in self.nodos.items():
            d = self._haversine(lat, lon, nodo.latitud, nodo.longitud)
            if d < mejor_dist:
                mejor_dist = d
                mejor_id   = id_n
        return mejor_id

    def sectores(self) -> list[str]:
        """Lista de sectores únicos en el grafo."""
        return list({n.sector for n in self.nodos.values()})

    def nodos_por_sector(self, sector: str) -> list[Nodo]:
        """Filtra nodos por sector. O(V)"""
        return [n for n in self.nodos.values() if n.sector == sector]

    # ------------------------------------------------------------------ #
    #  Estadísticas                                                        #
    # ------------------------------------------------------------------ #
    def __repr__(self) -> str:
        total_aristas = sum(len(v) for v in self.aristas.values())
        return (f"Grafo(nodos={len(self.nodos)}, "
                f"aristas={total_aristas}, "
                f"sectores={len(self.sectores())})")

    # ------------------------------------------------------------------ #
    #  Serialización                                                       #
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        """
        Serializa el grafo.  Solo exporta las aristas originales
        (bidireccional=True o unidireccionales explicitas bidireccional=False
        que vengan del JSON original).  Las inversas generadas internamente
        se omiten para no duplicar datos al recargar.
        """
        return {
            "nodos"  : [n.to_dict() for n in self.nodos.values()],
            "aristas": [
                a.to_dict()
                for lista in self.aristas.values()
                for a in lista
                if a.bidireccional        # solo aristas originales (inversas tienen bidireccional=False)
            ],
        }

    @staticmethod
    def from_dict(data: dict) -> "Grafo":
        g = Grafo()
        for nd in data.get("nodos", []):
            g.agregar_nodo(Nodo(**nd))
        for ar in data.get("aristas", []):
            g.agregar_arista(Arista(**ar))
        return g

    def guardar_json(self, ruta: str):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def cargar_json(ruta: str) -> "Grafo":
        with open(ruta, encoding="utf-8") as f:
            return Grafo.from_dict(json.load(f))