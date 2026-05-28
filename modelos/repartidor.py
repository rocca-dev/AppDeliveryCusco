"""
modelos/repartidor.py — Modelo de Dominio: Repartidor
=======================================================
Representa a un repartidor con su vehículo, posición GPS y
lista de pedidos asignados.

CAMBIOS respecto a la versión original
───────────────────────────────────────
  1. TipoVehiculo y CAPACIDADES_VEHICULO ahora se importan desde
     core.tipos (eliminada la duplicación de la tabla de capacidades).

  2. Re-exporta TipoVehiculo por compatibilidad con código legado
     que lo importa desde este módulo.

  3. Mejora de __hash__ para permitir uso en sets y como clave de dict
     (necesario para el DeliveryCoordinator).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing      import Optional, TYPE_CHECKING

# Importar tipos centralizados
from core.tipos import TipoVehiculo, CAPACIDADES_VEHICULO, EstadoPedido   # noqa: F401

if TYPE_CHECKING:
    from modelos.pedido import Pedido


@dataclass
class Repartidor:
    """
    Representa a un repartidor del sistema.

    Atributos
    ──────────
    id_repartidor    : Identificador único  (ej. "R01")
    nombre           : Nombre completo
    vehiculo         : Tipo de vehículo  (TipoVehiculo enum)
    latitud_actual   : Posición GPS actual
    longitud_actual  : Posición GPS actual
    capacidad_kg     : Capacidad máxima en kg (derivada del vehículo)
    capacidad_m3     : Capacidad máxima en m³ (derivada del vehículo)
    pedidos_asignados: Lista de pedidos cargados actualmente
    disponible       : True si está libre para nuevas asignaciones
    sector_asignado  : Cuadrante/zona asignada (Divide y Vencerás)
    """
    id_repartidor    : str
    nombre           : str
    vehiculo         : TipoVehiculo      = TipoVehiculo.MOTO
    latitud_actual   : float             = -13.5170   # Plaza de Armas Cusco
    longitud_actual  : float             = -71.9785
    # capacidad_kg y capacidad_m3 se calculan en __post_init__
    capacidad_kg     : float             = field(init=False)
    capacidad_m3     : float             = field(init=False)
    pedidos_asignados: list              = field(default_factory=list)
    disponible       : bool              = True
    sector_asignado  : Optional[str]     = None

    def __post_init__(self):
        """Asigna capacidades automáticamente según el tipo de vehículo."""
        cap = CAPACIDADES_VEHICULO[self.vehiculo]
        self.capacidad_kg = cap[0]
        self.capacidad_m3 = cap[1]

    def __hash__(self) -> int:
        """Permite usar Repartidor como clave de dict o en sets."""
        return hash(self.id_repartidor)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Repartidor):
            return NotImplemented
        return self.id_repartidor == other.id_repartidor

    # ── Propiedades calculadas ────────────────────────────────────────────────
    @property
    def peso_cargado(self) -> float:
        """Peso total de pedidos actualmente asignados. O(k)"""
        return sum(p.peso_kg for p in self.pedidos_asignados)

    @property
    def volumen_cargado(self) -> float:
        """Volumen total de pedidos actualmente asignados. O(k)"""
        return sum(p.volumen_m3 for p in self.pedidos_asignados)

    @property
    def capacidad_disponible_kg(self) -> float:
        """Kilogramos libres restantes."""
        return self.capacidad_kg - self.peso_cargado

    @property
    def esta_lleno(self) -> bool:
        """True si no puede cargar más pedidos."""
        return self.capacidad_disponible_kg <= 0

    # ── Métodos de comportamiento ─────────────────────────────────────────────
    def puede_cargar(self, pedido: "Pedido") -> bool:
        """
        Verifica si puede cargar un pedido respetando peso y volumen.

        Complejidad: O(k) donde k = len(pedidos_asignados) (por las
        propiedades peso_cargado y volumen_cargado).
        """
        return (
            self.peso_cargado    + pedido.peso_kg    <= self.capacidad_kg and
            self.volumen_cargado + pedido.volumen_m3 <= self.capacidad_m3
        )

    def asignar_pedido(self, pedido: "Pedido") -> bool:
        """
        Intenta asignar un pedido al repartidor.

        Returns:
            True si fue exitoso, False si excede capacidad.
        """
        if not self.puede_cargar(pedido):
            return False
        self.pedidos_asignados.append(pedido)
        pedido.estado = EstadoPedido.ASIGNADO
        return True

    def posicion(self) -> tuple[float, float]:
        """Retorna posición actual como (lat, lon)."""
        return (self.latitud_actual, self.longitud_actual)

    def actualizar_posicion(self, lat: float, lon: float):
        """Actualiza la posición GPS del repartidor."""
        self.latitud_actual  = lat
        self.longitud_actual = lon

    # ── Serialización ─────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "id_repartidor"    : self.id_repartidor,
            "nombre"           : self.nombre,
            "vehiculo"         : self.vehiculo.value,
            "latitud_actual"   : self.latitud_actual,
            "longitud_actual"  : self.longitud_actual,
            "capacidad_kg"     : self.capacidad_kg,
            "capacidad_m3"     : self.capacidad_m3,
            "peso_cargado"     : round(self.peso_cargado, 2),
            "disponible"       : self.disponible,
            "sector_asignado"  : self.sector_asignado,
            "pedidos_asignados": [p.id_pedido for p in self.pedidos_asignados],
        }

    def __repr__(self) -> str:
        return (f"Repartidor({self.id_repartidor} | {self.nombre} | "
                f"{self.vehiculo.value} | "
                f"{self.peso_cargado:.1f}/{self.capacidad_kg}kg | "
                f"pedidos={len(self.pedidos_asignados)})")
