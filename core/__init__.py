"""
core — Núcleo del sistema: utilidades sin dependencias internas.

Exportaciones principales:
    geo          : haversine, distancia_puntos, nodo_mas_cercano_idx
    tipos        : Prioridad, EstadoPedido, TipoVehiculo, CAPACIDADES_VEHICULO
    serializable : Serializable (mixin)
"""

from core.geo          import haversine, distancia_puntos, nodo_mas_cercano_idx
from core.tipos        import Prioridad, EstadoPedido, TipoVehiculo, CAPACIDADES_VEHICULO
from core.serializable import Serializable

__all__ = [
    "haversine",
    "distancia_puntos",
    "nodo_mas_cercano_idx",
    "Prioridad",
    "EstadoPedido",
    "TipoVehiculo",
    "CAPACIDADES_VEHICULO",
    "Serializable",
]
