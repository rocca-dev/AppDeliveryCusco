"""
core/tipos.py — Tipos y Enumeraciones Compartidos
===================================================
Define todos los Enums del sistema en un solo lugar para evitar
importaciones circulares y duplicación de definiciones.

ANTES del refactor cada modelo definía sus propios Enums:
  - modelos/pedido.py      → Prioridad, EstadoPedido
  - modelos/repartidor.py  → TipoVehiculo, CAPACIDADES_VEHICULO

AHORA todos los módulos importan desde aquí.  Los modelos re-exportan
los tipos por compatibilidad con código legado.

Análisis de dependencias
─────────────────────────
  core.tipos   ←  modelos.pedido
  core.tipos   ←  modelos.repartidor
  core.tipos   ←  algoritmos.* (directamente, sin pasar por modelos)
  core.tipos   ←  dispatcher.*

  core.tipos NO importa nada del proyecto → sin riesgo de ciclos.
"""

from __future__ import annotations

from enum import Enum


# ─────────────────────────────────────────────────────────────────────────────
#  Pedido
# ─────────────────────────────────────────────────────────────────────────────

class Prioridad(Enum):
    """
    Niveles de urgencia de un pedido, ordenados de menor a mayor.

    El valor numérico se usa para comparaciones directas:
        Prioridad.URGENTE > Prioridad.ALTA > Prioridad.MEDIA > Prioridad.BAJA
    y como ponderador en el Knapsack (bonus por prioridad alta).
    """
    BAJA    = 1
    MEDIA   = 2
    ALTA    = 3
    URGENTE = 4


class EstadoPedido(Enum):
    """
    Ciclo de vida de un pedido dentro del sistema.

    Transiciones válidas:
        PENDIENTE → ASIGNADO → EN_RUTA → ENTREGADO
        Cualquier estado → CANCELADO
    """
    PENDIENTE  = "pendiente"
    ASIGNADO   = "asignado"
    EN_RUTA    = "en_ruta"
    ENTREGADO  = "entregado"
    CANCELADO  = "cancelado"


# ─────────────────────────────────────────────────────────────────────────────
#  Repartidor
# ─────────────────────────────────────────────────────────────────────────────

class TipoVehiculo(Enum):
    """
    Tipo de vehículo de un repartidor.
    Determina la capacidad máxima de carga (ver CAPACIDADES_VEHICULO).
    """
    MOTO      = "moto"
    BICICLETA = "bicicleta"
    FURGONETA = "furgoneta"
    A_PIE     = "a_pie"


# Capacidades máximas por tipo de vehículo: (kg_max, m3_max)
# Tabla centralizada para que repartidor.py no repita esta información.
CAPACIDADES_VEHICULO: dict[TipoVehiculo, tuple[float, float]] = {
    TipoVehiculo.MOTO      : (30.0,  0.15),
    TipoVehiculo.BICICLETA : (15.0,  0.08),
    TipoVehiculo.FURGONETA : (500.0, 3.00),
    TipoVehiculo.A_PIE     : (10.0,  0.05),
}
