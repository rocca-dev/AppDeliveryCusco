"""
algoritmos/backtracking — Backtracking
=======================================
Subpaquete con algoritmos de búsqueda exhaustiva con poda.

Exportaciones:
    BuscadorRutasBacktracking     : Búsqueda de rutas entre dos nodos.
    BuscadorConPuntosObligatorios : Búsqueda con puntos obligatorios.
    AsignadorPedidosBacktracking  : Asignación óptima de pedidos.
    buscar_rutas                  : Función de conveniencia (rutas).
    asignar_pedidos               : Función de conveniencia (asignación).
    RutaEncontrada                : Ruta individual encontrada.
    ResultadoBacktracking         : Resultado de búsqueda de rutas.
    AsignacionPedido              : Asignación individual.
    ResultadoAsignacion           : Resultado de asignación de pedidos.
"""

from algoritmos.backtracking.buscador_rutas import (
    BuscadorRutasBacktracking,
    BuscadorConPuntosObligatorios,
    buscar_rutas,
    RutaEncontrada,
    ResultadoBacktracking,
)
from algoritmos.backtracking.asignador_pedidos import (
    AsignadorPedidosBacktracking,
    asignar_pedidos,
    AsignacionPedido,
    ResultadoAsignacion,
)

__all__ = [
    "BuscadorRutasBacktracking",
    "BuscadorConPuntosObligatorios",
    "AsignadorPedidosBacktracking",
    "buscar_rutas",
    "asignar_pedidos",
    "RutaEncontrada",
    "ResultadoBacktracking",
    "AsignacionPedido",
    "ResultadoAsignacion",
]
