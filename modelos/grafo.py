"""
modelos/grafo.py — Modelo de Dominio: Grafo Vial
=================================================
Grafo ponderado y dirigido que representa el mapa vial de Cusco.
Cada nodo = intersección o lugar de interés.
Cada arista = calle con distancia en metros y tiempo estimado.

CAMBIOS respecto a la versión original
───────────────────────────────────────
  1. Eliminado Grafo._haversine() (método estático duplicado).
     Ahora usa core.geo.haversine() directamente, que además está
     memoizado con @lru_cache → mejora de rendimiento en búsquedas
     de nodo más cercano (llamada O(V) × cálculo O(1) cacheado).

  2. distancia_euclidiana() y nodo_mas_cercano() delegan en core.geo.

  3. Sin cambios en la interfaz pública → compatibilidad total.

Análisis Big-O
──────────────
  agregar_nodo          : O(1)
  agregar_arista        : O(1)  (+inversa si bidireccional)
  vecinos               : O(grado(v))
  nodo_mas_cercano      : O(V) — itera todos los nodos
  distancia_euclidiana  : O(1) — haversine con caché
  bloquear_calle        : O(grado(origen) + grado(destino))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing      import Optional
import json

# Única dependencia de geometría → elimina _haversine local
from core.geo import haversine


# ─────────────────────────────────────────────────────────────────────────────
#  Nodo del grafo
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Nodo:
    """
    Intersección o punto de interés en el mapa de Cusco.

    Atributos
    ──────────
    id_nodo    : Identificador único  (ej. "plaza_armas")
    nombre     : Nombre legible
    latitud    : Coordenada GPS real
    longitud   : Coordenada GPS real
    sector     : Zona a la que pertenece
    es_deposito: True si es punto de partida de repartidores
    """
    id_nodo    : str
    nombre     : str
    latitud    : float
    longitud   : float
    sector     : str
    es_deposito: bool = False

    def coordenadas(self) -> tuple[float, float]:
        """Retorna (latitud, longitud)."""
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


# ─────────────────────────────────────────────────────────────────────────────
#  Arista del grafo
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Arista:
    """
    Calle entre dos nodos del mapa.

    Atributos
    ──────────
    origen        : id_nodo de origen
    destino       : id_nodo de destino
    distancia_m   : Distancia en metros
    tiempo_min    : Tiempo estimado en minutos (con tráfico promedio)
    bloqueada     : True si la calle está cerrada (Backtracking)
    bidireccional : True si la calle es de doble sentido
    """
    origen        : str
    destino       : str
    distancia_m   : float
    tiempo_min    : float
    bloqueada     : bool = False
    bidireccional : bool = True

    def to_dict(self) -> dict:
        return {
            "origen"        : self.origen,
            "destino"       : self.destino,
            "distancia_m"   : self.distancia_m,
            "tiempo_min"    : self.tiempo_min,
            "bloqueada"     : self.bloqueada,
            "bidireccional" : self.bidireccional,
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Grafo principal
# ─────────────────────────────────────────────────────────────────────────────
class Grafo:
    """
    Grafo de adyacencia que representa el mapa vial de Cusco.

    Internamente usa listas de adyacencia (dict de listas) para O(V+E)
    en espacio y O(grado) en consultas de vecinos.

    Complejidad espacial: O(V + E)
    """

    def __init__(self):
        self.nodos  : dict[str, Nodo]         = {}
        self.aristas: dict[str, list[Arista]] = {}   # lista de adyacencia

    # ── Construcción ──────────────────────────────────────────────────────────
    def agregar_nodo(self, nodo: Nodo):
        """O(1) — agrega un nodo al grafo."""
        self.nodos[nodo.id_nodo] = nodo
        if nodo.id_nodo not in self.aristas:
            self.aristas[nodo.id_nodo] = []

    def agregar_arista(self, arista: Arista):
        """
        O(1) — agrega una arista.
        Si es bidireccional, agrega también la arista inversa
        con bidireccional=False para evitar duplicación al serializar.
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
                bidireccional = False,   # marca: es inversa, no duplicar
            )
            if arista.destino not in self.aristas:
                self.aristas[arista.destino] = []
            self.aristas[arista.destino].append(inversa)

    # ── Consultas ─────────────────────────────────────────────────────────────
    def vecinos(self, id_nodo: str, solo_libres: bool = True) -> list[Arista]:
        """
        Retorna las aristas salientes de un nodo.

        Args:
            id_nodo    : Nodo de consulta.
            solo_libres: Si True, excluye calles bloqueadas.

        Complejidad: O(grado(v))
        """
        aristas = self.aristas.get(id_nodo, [])
        if solo_libres:
            return [a for a in aristas if not a.bloqueada]
        return aristas

    def nodo(self, id_nodo: str) -> Optional[Nodo]:
        """O(1) — retorna el Nodo o None si no existe."""
        return self.nodos.get(id_nodo)

    def distancia_euclidiana(self, id_a: str, id_b: str) -> float:
        """
        Distancia en línea recta entre dos nodos usando Haversine.
        Delega en core.geo.haversine() (memoizado).

        Útil como heurística para A*.
        Complejidad: O(1) con caché.
        """
        a = self.nodos.get(id_a)
        b = self.nodos.get(id_b)
        if not a or not b:
            return float("inf")
        return haversine(a.latitud, a.longitud, b.latitud, b.longitud)

    def nodo_mas_cercano(self, lat: float, lon: float) -> Optional[str]:
        """
        Dado un punto GPS, retorna el id del nodo más cercano.

        Usa core.geo.haversine() (memoizado) para cada comparación.
        Complejidad: O(V) — itera todos los nodos del grafo.

        Args:
            lat, lon : Coordenadas GPS del punto de consulta.

        Returns:
            id_nodo del nodo más cercano, o None si el grafo está vacío.
        """
        mejor_id   = None
        mejor_dist = float("inf")
        for id_n, nodo in self.nodos.items():
            d = haversine(lat, lon, nodo.latitud, nodo.longitud)
            if d < mejor_dist:
                mejor_dist = d
                mejor_id   = id_n
        return mejor_id

    def bloquear_calle(self, origen: str, destino: str):
        """Marca una calle (y su inversa si existe) como bloqueada."""
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

    def sectores(self) -> list[str]:
        """Lista de sectores únicos en el grafo."""
        return list({n.sector for n in self.nodos.values()})

    def nodos_por_sector(self, sector: str) -> list[Nodo]:
        """Filtra nodos por sector. O(V)"""
        return [n for n in self.nodos.values() if n.sector == sector]

    # ── Serialización ─────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        """
        Serializa el grafo a dict.
        Solo exporta aristas originales (bidireccional=True) para
        evitar duplicar las inversas al recargar desde JSON.
        """
        return {
            "nodos"  : [n.to_dict() for n in self.nodos.values()],
            "aristas": [
                a.to_dict()
                for lista in self.aristas.values()
                for a in lista
                if a.bidireccional
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

    def __repr__(self) -> str:
        total_aristas = sum(len(v) for v in self.aristas.values())
        return (f"Grafo(nodos={len(self.nodos)}, "
                f"aristas={total_aristas}, "
                f"sectores={len(self.sectores())})")
