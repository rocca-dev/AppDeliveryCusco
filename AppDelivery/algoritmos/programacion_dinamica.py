"""
Módulo: Programación Dinámica
=============================
Implementa dos algoritmos fundamentales de PD:

  1. Knapsack 0/1 — Maximiza el valor de pedidos cargados en un
     repartidor respetando restricciones de peso y volumen.

  2. Dijkstra con memoización — Ruta más corta entre dos nodos,
     con caché de resultados para consultas repetidas.

ESTRATEGIA
──────────
  Knapsack 0/1 (2 restricciones):
    Tabla DP[n+1][W+1] donde W = capacidad en kg (discretizada).
    Para mochila 2D, se usa aproximación: se discretiza volumen como
    segunda dimensión.

    Optimización: reducción de dimensionalidad con arreglo 1D
    cuando solo hay restricción de peso.

  Dijkstra:
    Cola de prioridad O((V+E)log V). Cache LRU guarda resultados
    de consultas anteriores → O(1) en hits.

ANÁLISIS Big-O
──────────────
  Knapsack 0/1:
      O(n × W) — tiempo
      O(W)     — espacio (con optimización 1D)
      donde n = pedidos, W = capacidad máxima (kg × 10)

  Knapsack Flota (k repartidores):
      O(r × n × W) — se resuelve un knapsack por repartidor

  Dijkstra:
      O((V+E) log V) — tiempo
      O(V)           — espacio
      Cache: O(1) en hits, O(V²) espacio para cache completo
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import heapq
import math

from modelos.pedido     import Pedido, EstadoPedido, Prioridad
from modelos.repartidor import Repartidor
from modelos.grafo      import Grafo


# ──────────────────────────────────────────────
# KNAPSACK 0/1
# ──────────────────────────────────────────────

@dataclass
class ResultadoMochila:
    pedidos_elegidos  : list[Pedido] = field(default_factory=list)
    peso_total        : float = 0.0
    volumen_total     : float = 0.0
    valor_total       : float = 0.0
    capacidad_usada_pct: float = 0.0

    def to_dict(self) -> dict:
        return {
            "pedidos_elegidos"  : [p.id_pedido for p in self.pedidos_elegidos],
            "peso_total"        : round(self.peso_total, 2),
            "volumen_total"     : round(self.volumen_total, 4),
            "valor_total"       : round(self.valor_total, 2),
            "capacidad_usada_pct": round(self.capacidad_usada_pct, 1),
            "num_pedidos"       : len(self.pedidos_elegidos),
        }


class Mochila01:
    def __init__(self, factor_escala: int = 10):
        self.factor_escala = factor_escala

    def resolver(self,
                 pedidos      : list[Pedido],
                 capacidad_kg : float,
                 capacidad_m3 : float,
                 bonus_urgente: float = 1.0,
                 ) -> ResultadoMochila:
        """
        Knapsack 0/1 con una sola dimensión de peso (kg).
        El volumen actúa como filtro previo: solo participan en la DP los
        pedidos que caben en m³.  Esto corrige el bug donde `eleccion` se
        dimensionaba con `n` (total de pedidos) pero `pesos_int/valores`
        podían tener menos elementos por el filtro de volumen.

        Complejidad: O(k × W)  donde k ≤ n son los pedidos que pasan el filtro.
        """
        if not pedidos or capacidad_kg <= 0:
            return ResultadoMochila()

        W = int(capacidad_kg * self.factor_escala)

        # --- Filtrar por volumen y construir listas alineadas ---
        candidatos : list[Pedido] = []
        pesos_int  : list[int]    = []
        valores    : list[float]  = []

        for p in pedidos:
            if p.volumen_m3 > capacidad_m3:
                continue
            w = max(1, int(p.peso_kg * self.factor_escala))
            v = p.valor * (bonus_urgente if p.prioridad == Prioridad.URGENTE else 1.0)
            candidatos.append(p)
            pesos_int.append(w)
            valores.append(v)

        k = len(candidatos)
        if k == 0:
            return ResultadoMochila()

        # --- Tabla DP 1-D + tabla de elecciones alineada con candidatos ---
        dp       = [0.0] * (W + 1)
        eleccion = [[-1] * (W + 1) for _ in range(k)]

        for i in range(k):
            for w in range(W, pesos_int[i] - 1, -1):
                nuevo = dp[w - pesos_int[i]] + valores[i]
                if nuevo > dp[w]:
                    dp[w] = nuevo
                    eleccion[i][w] = 1

        # --- Reconstrucción ---
        resultado  = ResultadoMochila()
        w_restante = W
        for i in range(k - 1, -1, -1):
            if eleccion[i][w_restante] == 1:
                p = candidatos[i]
                resultado.pedidos_elegidos.append(p)
                resultado.peso_total    += p.peso_kg
                resultado.volumen_total += p.volumen_m3
                resultado.valor_total   += valores[i]
                w_restante              -= pesos_int[i]
                p.estado = EstadoPedido.ASIGNADO

        resultado.pedidos_elegidos.reverse()
        resultado.capacidad_usada_pct = (
            (resultado.peso_total / capacidad_kg) * 100
            if capacidad_kg > 0 else 0
        )
        return resultado

    def resolver_flota(self,
                       pedidos      : list[Pedido],
                       repartidores : list[Repartidor],
                       bonus_urgente: float = 1.5,
                       ) -> list[ResultadoMochila]:
        resultados: list[ResultadoMochila] = []
        pendientes = [p for p in pedidos
                      if p.estado == EstadoPedido.PENDIENTE]

        for rep in repartidores:
            res = self.resolver(
                pendientes, rep.capacidad_kg, rep.capacidad_m3, bonus_urgente
            )
            resultados.append(res)
            for p in res.pedidos_elegidos:
                if p in pendientes:
                    pendientes.remove(p)
                    rep.pedidos_asignados.append(p)

        return resultados


def resultado_mochila(pedidos: list[Pedido],
                      capacidad_kg: float,
                      capacidad_m3: float,
                      bonus_urgente: float = 1.0,
                      ) -> ResultadoMochila:
    m = Mochila01()
    return m.resolver(pedidos, capacidad_kg, capacidad_m3, bonus_urgente)


def resultado_mochila_flota(pedidos: list[Pedido],
                            repartidores: list[Repartidor],
                            bonus_urgente: float = 1.5,
                            ) -> list[ResultadoMochila]:
    m = Mochila01()
    return m.resolver_flota(pedidos, repartidores, bonus_urgente)


# ──────────────────────────────────────────────
# DIJKSTRA CON MEMOIZACIÓN
# ──────────────────────────────────────────────

@dataclass
class ResultadoDijkstra:
    origen      : str
    destino     : str
    camino      : list[str]
    distancia_m : float
    tiempo_min  : float
    desde_cache : bool = False

    def to_dict(self) -> dict:
        return {
            "origen"      : self.origen,
            "destino"     : self.destino,
            "camino"      : self.camino,
            "distancia_m" : round(self.distancia_m, 2),
            "tiempo_min"  : round(self.tiempo_min, 2),
            "desde_cache" : self.desde_cache,
        }


class DijkstraMemo:
    def __init__(self, grafo: Grafo, max_cache: int = 200):
        self.grafo     = grafo
        self._cache    : dict[tuple[str, str], ResultadoDijkstra] = {}
        self._max_cache = max_cache
        self._hits     = 0
        self._misses   = 0

    def ruta_mas_corta(self,
                       origen : str,
                       destino: str,
                       usar_cache: bool = True,
                       ) -> ResultadoDijkstra:
        if usar_cache:
            key = (origen, destino)
            if key in self._cache:
                self._hits += 1
                cached = self._cache[key]
                cached.desde_cache = True
                return cached
            self._misses += 1

        if origen not in self.grafo.nodos:
            raise ValueError(f"Nodo origen '{origen}' no existe.")
        if destino not in self.grafo.nodos:
            raise ValueError(f"Nodo destino '{destino}' no existe.")

        if origen == destino:
            res = ResultadoDijkstra(
                origen=origen, destino=destino,
                camino=[origen], distancia_m=0.0, tiempo_min=0.0,
            )
            if usar_cache:
                self._cache[(origen, destino)] = res
            return res

        dist: dict[str, float] = {n: float("inf") for n in self.grafo.nodos}
        prev: dict[str, Optional[str]] = {n: None for n in self.grafo.nodos}
        dist[origen] = 0.0
        pq = [(0.0, origen)]

        while pq:
            d_act, nodo_act = heapq.heappop(pq)
            if d_act > dist[nodo_act]:
                continue
            if nodo_act == destino:
                break
            for arista in self.grafo.vecinos(nodo_act, solo_libres=True):
                nueva_d = d_act + arista.distancia_m
                if nueva_d < dist[arista.destino]:
                    dist[arista.destino] = nueva_d
                    prev[arista.destino] = nodo_act
                    heapq.heappush(pq, (nueva_d, arista.destino))

        if dist[destino] == float("inf"):
            raise ValueError(f"No hay ruta disponible de '{origen}' a '{destino}'.")

        camino = []
        nodo = destino
        while nodo is not None:
            camino.append(nodo)
            nodo = prev[nodo]
        camino.reverse()

        tiempo_total = 0.0
        for i in range(len(camino) - 1):
            for arista in self.grafo.vecinos(camino[i], solo_libres=True):
                if arista.destino == camino[i + 1]:
                    tiempo_total += arista.tiempo_min
                    break

        res = ResultadoDijkstra(
            origen=origen, destino=destino, camino=camino,
            distancia_m=dist[destino], tiempo_min=tiempo_total,
        )

        if usar_cache:
            if len(self._cache) >= self._max_cache:
                self._cache.pop(next(iter(self._cache)))
            self._cache[(origen, destino)] = res
            inv = ResultadoDijkstra(
                origen=destino, destino=origen,
                camino=list(reversed(camino)),
                distancia_m=dist[destino], tiempo_min=tiempo_total,
            )
            self._cache[(destino, origen)] = inv

        return res

    def stats_cache(self) -> dict:
        return {
            "tamano_cache": len(self._cache),
            "max_cache"   : self._max_cache,
            "hits"        : self._hits,
            "misses"      : self._misses,
            "hit_ratio"   : round(self._hits / max(self._hits + self._misses, 1), 3),
        }

    def limpiar_cache(self):
        self._cache.clear()
        self._hits = 0
        self._misses = 0


# ──────────────────────────────────────────────
# PLANIFICADOR DE RUTAS CON PD
# ──────────────────────────────────────────────

class PlanificadorRutasPD:
    def __init__(self, grafo: Grafo):
        self.dijkstra = DijkstraMemo(grafo)
        self.mochila  = Mochila01()

    def planificar_viaje(self,
                         repartidor: Repartidor,
                         pedidos   : list[Pedido],
                         bonus_urgente: float = 1.5,
                         ) -> dict:
        pendientes = [p for p in pedidos
                      if p.estado == EstadoPedido.PENDIENTE]
        carga = self.mochila.resolver(
            pendientes, repartidor.capacidad_kg,
            repartidor.capacidad_m3, bonus_urgente
        )
        ruta = []
        dist_total = 0.0
        tiempo_total = 0.0
        nodo_act = self.dijkstra.grafo.nodo_mas_cercano(
            repartidor.latitud_actual, repartidor.longitud_actual
        )
        if not nodo_act:
            return {"error": "No se pudo ubicar al repartidor en el grafo"}

        for p in carga.pedidos_elegidos:
            if not p.id_nodo:
                continue
            try:
                res = self.dijkstra.ruta_mas_corta(nodo_act, p.id_nodo)
                if len(res.camino) > 1:
                    ruta.extend(res.camino[1:])
                else:
                    ruta.append(res.camino[0])
                dist_total += res.distancia_m
                tiempo_total += res.tiempo_min
                nodo_act = p.id_nodo
            except ValueError:
                continue

        return {
            "repartidor"         : repartidor.id_repartidor,
            "nombre"             : repartidor.nombre,
            "pedidos_elegidos"   : [p.id_pedido for p in carga.pedidos_elegidos],
            "ruta_nodos"         : ruta,
            "distancia_total_m"  : round(dist_total, 2),
            "tiempo_total_min"   : round(tiempo_total, 2),
            "valor_total"        : round(carga.valor_total, 2),
            "peso_total_kg"      : round(carga.peso_total, 2),
        }


def ruta_optima_dijkstra(grafo: Grafo,
                         origen: str,
                         destino: str,
                         usar_cache: bool = True,
                         ) -> ResultadoDijkstra:
    d = DijkstraMemo(grafo)
    return d.ruta_mas_corta(origen, destino, usar_cache)
