"""
Módulo: Ordenación
Implementa Merge Sort para ordenar pedidos por distintos criterios.

Complejidad temporal : O(n log n) — todos los casos (mejor, promedio, peor)
Complejidad espacial : O(n)       — arreglo auxiliar en el merge
Estabilidad          : ESTABLE    — preserva orden relativo de iguales

¿Por qué Merge Sort y no Quick Sort?
  - Quick Sort tiene peor caso O(n²) con pivote malo.
  - Para listas de pedidos la ESTABILIDAD importa: dos pedidos con
    misma prioridad deben conservar su orden de llegada (timestamp).
  - Python usa TimSort (variante de Merge Sort) internamente por la misma razón.
"""

from __future__ import annotations
from typing import Callable, TypeVar
import math
from modelos.pedido import Pedido

T = TypeVar("T")


# ─────────────────────────────────────────────────────────────
#  MERGE SORT GENÉRICO
# ─────────────────────────────────────────────────────────────

def merge_sort(lista: list[T],
               clave: Callable[[T], any],
               descendente: bool = False) -> list[T]:
    """
    Ordena una lista usando Merge Sort con clave personalizable.

    Args:
        lista       : Lista de entrada (no se modifica).
        clave       : Función que extrae el valor de comparación.
        descendente : True → mayor primero.

    Returns:
        Nueva lista ordenada.

    Complejidad:
        Temporal O(n log n) — divide log(n) veces, cada nivel cuesta O(n)
        Espacial O(n)       — sublistas temporales en cada merge
    """
    if len(lista) <= 1:
        return lista[:]                    # caso base O(1)

    medio     = len(lista) // 2
    izquierda = merge_sort(lista[:medio], clave, descendente)
    derecha   = merge_sort(lista[medio:], clave, descendente)

    return _merge(izquierda, derecha, clave, descendente)


def _merge(izq: list[T],
           der: list[T],
           clave: Callable[[T], any],
           descendente: bool) -> list[T]:
    """Combina dos sublistas ordenadas. O(n)"""
    resultado = []
    i = j = 0

    while i < len(izq) and j < len(der):
        a, b = clave(izq[i]), clave(der[j])
        if (a >= b) if descendente else (a <= b):
            resultado.append(izq[i]); i += 1
        else:
            resultado.append(der[j]); j += 1

    resultado.extend(izq[i:])
    resultado.extend(der[j:])
    return resultado


# ─────────────────────────────────────────────────────────────
#  FUNCIONES ESPECIALIZADAS PARA PEDIDOS
# ─────────────────────────────────────────────────────────────

def ordenar_por_prioridad(pedidos: list[Pedido],
                          descendente: bool = True) -> list[Pedido]:
    """
    Por defecto: URGENTE → ALTA → MEDIA → BAJA.
    O(n log n)
    """
    return merge_sort(pedidos,
                      clave=lambda p: p.prioridad.value,
                      descendente=descendente)


def ordenar_por_peso(pedidos: list[Pedido],
                     descendente: bool = False) -> list[Pedido]:
    """
    Por defecto: más ligero primero.
    O(n log n)
    """
    return merge_sort(pedidos, clave=lambda p: p.peso_kg,
                      descendente=descendente)


def ordenar_por_valor(pedidos: list[Pedido],
                      descendente: bool = True) -> list[Pedido]:
    """
    Por defecto: más valioso primero.
    Útil como heurística previa al Knapsack.
    O(n log n)
    """
    return merge_sort(pedidos, clave=lambda p: p.valor,
                      descendente=descendente)


def ordenar_por_distancia(pedidos: list[Pedido],
                          lat_origen: float,
                          lon_origen: float) -> list[Pedido]:
    """
    Ordena por distancia euclidiana desde un punto origen.
    Útil para el Greedy (vecino más cercano).
    O(n log n)  — cálculo de distancia por pedido es O(1)
    """
    def dist(p: Pedido) -> float:
        dlat = p.latitud  - lat_origen
        dlon = p.longitud - lon_origen
        return math.sqrt(dlat ** 2 + dlon ** 2)

    return merge_sort(pedidos, clave=dist, descendente=False)


def ordenar_por_sector(pedidos: list[Pedido]) -> list[Pedido]:
    """
    Ordena alfabéticamente por sector.
    Agrupa entregas por zona antes de aplicar Divide y Vencerás.
    O(n log n)
    """
    return merge_sort(pedidos, clave=lambda p: p.sector,
                      descendente=False)


def ordenar_combinado(pedidos: list[Pedido]) -> list[Pedido]:
    """
    Clave compuesta: (prioridad DESC, valor DESC).
    Simula una cola de despacho real: primero lo urgente y valioso.
    Merge Sort compara tuplas elemento a elemento → O(n log n).
    """
    return merge_sort(
        pedidos,
        clave=lambda p: (p.prioridad.value, p.valor),
        descendente=True,
    )