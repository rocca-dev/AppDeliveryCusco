"""
Módulo: Greedy (Algoritmo Voraz)
=================================
Implementa el vecino más cercano (Nearest Neighbor) para construir
rutas de reparto y un asignador greedy que distribuye pedidos entre
la flota de repartidores.

ESTRATEGIA
──────────
  1. NearestNeighborGreedy — desde la posición actual del repartidor,
     selecciona iterativamente el pedido más cercano no visitado.

  2. AsignacionGreedy — asigna cada pedido al repartidor más cercano
     que tenga capacidad disponible, luego construye la ruta con NN.

ANÁLISIS Big-O
──────────────
  Nearest Neighbor (por ruta):
      O(n²) — peor caso (n = pedidos)
      O(n log n) — con estructura de datos óptima (quadtree)

  Asignación Greedy:
      O(p × r) — donde p = pedidos, r = repartidores
      Más eficiente que asignación por fuerza bruta O(r^p)

  Ahorro vs Aleatorio:
      Tipicamente 30-50% mejor en distancia total.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math
import random

from modelos.pedido     import Pedido, EstadoPedido, Prioridad
from modelos.repartidor import Repartidor
from modelos.grafo      import Grafo


@dataclass
class ResultadoGreedy:
    repartidor        : Repartidor
    ruta_pedidos      : list[Pedido] = field(default_factory=list)
    distancia_total_m : float        = 0.0
    tiempo_total_min  : float        = 0.0
    pedidos_omitidos  : list[Pedido] = field(default_factory=list)

    def resumen(self) -> str:
        ids = [p.id_pedido for p in self.ruta_pedidos]
        return (f"Repartidor: {self.repartidor.id_repartidor} "
                f"({self.repartidor.nombre})\n"
                f"  Ruta     : {' → '.join(ids)}\n"
                f"  Distancia: {self.distancia_total_m:,.0f} m\n"
                f"  Tiempo   : {self.tiempo_total_min:.1f} min\n"
                f"  Pedidos  : {len(self.ruta_pedidos)}\n"
                f"  Omitidos : {len(self.pedidos_omitidos)}")

    def to_dict(self) -> dict:
        return {
            "repartidor"        : self.repartidor.id_repartidor,
            "nombre"            : self.repartidor.nombre,
            "ruta_pedidos"      : [p.id_pedido for p in self.ruta_pedidos],
            "distancia_total_m" : round(self.distancia_total_m, 2),
            "tiempo_total_min"  : round(self.tiempo_total_min, 2),
            "peso_total_kg"     : round(sum(p.peso_kg for p in self.ruta_pedidos), 2),
            "pedidos_omitidos"  : [p.id_pedido for p in self.pedidos_omitidos],
        }


class NearestNeighborGreedy:
    """
    Construye una ruta de reparto usando el vecino más cercano.

    Complejidad: O(n²) — n = pedidos candidatos.
    """

    def __init__(self, grafo: Grafo):
        self.grafo = grafo

    def construir_ruta(self,
                       repartidor   : Repartidor,
                       pedidos      : list[Pedido],
                       solo_urgentes: bool = False,
                       ) -> ResultadoGreedy:
        resultado = ResultadoGreedy(repartidor=repartidor)
        if not pedidos:
            return resultado

        if solo_urgentes:
            disponibles = [p for p in pedidos
                           if p.estado == EstadoPedido.PENDIENTE
                           and p.prioridad in (Prioridad.URGENTE, Prioridad.ALTA)]
        else:
            disponibles = [p for p in pedidos
                           if p.estado == EstadoPedido.PENDIENTE]

        if not disponibles:
            return resultado

        restantes    = list(disponibles)
        lat_act, lon_act = repartidor.latitud_actual, repartidor.longitud_actual
        dist_total   = 0.0
        tiempo_total = 0.0

        # FIX: antes la condición chequeaba solo restantes[0], ignorando pedidos
        # más ligeros que sí cabrían.  Ahora el loop continúa mientras haya
        # algún pedido que el repartidor pueda cargar.
        while restantes and any(repartidor.puede_cargar(p) for p in restantes):
            mejor_p    = None
            mejor_dist = float("inf")

            for p in restantes:
                if not repartidor.puede_cargar(p):
                    continue
                # Reutiliza haversine del Grafo (DRY)
                d = self.grafo._haversine(lat_act, lon_act, p.latitud, p.longitud)
                if d < mejor_dist:
                    mejor_dist = d
                    mejor_p    = p

            if mejor_p is None:
                break

            restantes.remove(mejor_p)
            dist_total += mejor_dist
            lat_act, lon_act = mejor_p.latitud, mejor_p.longitud

            # Velocidad estimada según peso del paquete
            if mejor_p.peso_kg <= 2.0:
                vel_kmh = 25
            elif mejor_p.peso_kg <= 10.0:
                vel_kmh = 20
            else:
                vel_kmh = 15
            tiempo_total += (mejor_dist / 1000) / vel_kmh * 60

            mejor_p.estado = EstadoPedido.ASIGNADO
            repartidor.pedidos_asignados.append(mejor_p)
            resultado.ruta_pedidos.append(mejor_p)

        resultado.pedidos_omitidos  = [p for p in disponibles
                                        if p not in resultado.ruta_pedidos]
        resultado.distancia_total_m = dist_total
        resultado.tiempo_total_min  = tiempo_total
        return resultado


class AsignacionGreedy:
    """
    Asigna pedidos a la flota completa usando NearestNeighbor por repartidor.

    Complejidad: O(p × r) asignación + O(k²) por ruta donde k ≤ p/r.
    """

    def __init__(self, grafo: Grafo):
        self.nn = NearestNeighborGreedy(grafo)

    def asignar(self,
                pedidos      : list[Pedido],
                repartidores : list[Repartidor],
                solo_urgentes: bool = False,
                ) -> list[ResultadoGreedy]:
        resultados : list[ResultadoGreedy] = []
        pendientes = [p for p in pedidos if p.estado == EstadoPedido.PENDIENTE]

        if not pendientes or not repartidores:
            return resultados

        for rep in repartidores:
            rep.pedidos_asignados.clear()
            # Solo ofrecer pedidos que físicamente caben en este repartidor
            candidatos = [p for p in pendientes if rep.puede_cargar(p)]
            res = self.nn.construir_ruta(rep, candidatos, solo_urgentes)
            resultados.append(res)
            for p_asig in res.ruta_pedidos:
                if p_asig in pendientes:
                    pendientes.remove(p_asig)

        # Intentar reasignar sobrantes en primer repartidor disponible
        for p_extra in list(pendientes):
            for rep in repartidores:
                if rep.puede_cargar(p_extra):
                    rep.asignar_pedido(p_extra)
                    for r in resultados:
                        if r.repartidor is rep:
                            r.ruta_pedidos.append(p_extra)
                    pendientes.remove(p_extra)
                    break

        return resultados


def distancia_ruta_aleatoria(
        pedidos   : list[Pedido],
        lat_origen: float,
        lon_origen: float,
        n_muestras: int = 500,
) -> float:
    """Baseline aleatorio para comparar con Greedy. O(n_muestras × n)."""
    if len(pedidos) < 2:
        return 0.0
    dists = []
    for _ in range(n_muestras):
        perm = list(pedidos)
        random.shuffle(perm)
        d = 0.0
        lat, lon = lat_origen, lon_origen
        for p in perm:
            dlat = p.latitud - lat
            dlon = p.longitud - lon
            d   += math.sqrt(dlat ** 2 + dlon ** 2) * 111_000
            lat, lon = p.latitud, p.longitud
        dists.append(d)
    return sum(dists) / len(dists) if dists else 0.0
