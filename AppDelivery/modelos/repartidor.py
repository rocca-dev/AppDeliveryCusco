"""
Modelo: Repartidor
Representa a un repartidor con su capacidad, posición y pedidos asignados.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from modelos.pedido import Pedido


class TipoVehiculo(Enum):
    """Tipo de vehículo del repartidor."""
    MOTO      = "moto"
    BICICLETA = "bicicleta"
    FURGONETA = "furgoneta"
    A_PIE     = "a_pie"


# Capacidades máximas por tipo de vehículo (kg, m3)
CAPACIDADES_VEHICULO: dict[TipoVehiculo, tuple[float, float]] = {
    TipoVehiculo.MOTO      : (30.0,  0.15),
    TipoVehiculo.BICICLETA : (15.0,  0.08),
    TipoVehiculo.FURGONETA : (500.0, 3.00),
    TipoVehiculo.A_PIE     : (10.0,  0.05),
}


@dataclass
class Repartidor:
    """
    Representa a un repartidor del sistema.

    Atributos:
        id_repartidor    : Identificador único (ej. "R01")
        nombre           : Nombre completo
        vehiculo         : Tipo de vehículo
        latitud_actual   : Posición GPS actual
        longitud_actual  : Posición GPS actual
        capacidad_kg     : Capacidad máxima en kg (calculada por vehículo)
        capacidad_m3     : Capacidad máxima en m³
        pedidos_asignados: Lista de pedidos cargados actualmente
        disponible       : Si está libre para nuevas asignaciones
        sector_asignado  : Cuadrante/zona asignada (Divide y Vencerás)
    """
    id_repartidor   : str
    nombre          : str
    vehiculo        : TipoVehiculo       = TipoVehiculo.MOTO
    latitud_actual  : float              = -13.5170   # Plaza de Armas Cusco
    longitud_actual : float              = -71.9785
    capacidad_kg    : float              = field(init=False)
    capacidad_m3    : float              = field(init=False)
    pedidos_asignados: list[Pedido]      = field(default_factory=list)
    disponible      : bool               = True
    sector_asignado : Optional[str]      = None

    def __post_init__(self):
        """Asigna capacidad automáticamente según el vehículo."""
        cap = CAPACIDADES_VEHICULO[self.vehiculo]
        self.capacidad_kg  = cap[0]
        self.capacidad_m3  = cap[1]

    # ------------------------------------------------------------------ #
    #  Propiedades calculadas                                              #
    # ------------------------------------------------------------------ #
    @property
    def peso_cargado(self) -> float:
        """Peso total de pedidos actualmente asignados."""
        return sum(p.peso_kg for p in self.pedidos_asignados)

    @property
    def volumen_cargado(self) -> float:
        """Volumen total de pedidos actualmente asignados."""
        return sum(p.volumen_m3 for p in self.pedidos_asignados)

    @property
    def capacidad_disponible_kg(self) -> float:
        """Kg libres restantes."""
        return self.capacidad_kg - self.peso_cargado

    @property
    def esta_lleno(self) -> bool:
        """True si no puede cargar más pedidos."""
        return self.capacidad_disponible_kg <= 0

    # ------------------------------------------------------------------ #
    #  Métodos                                                             #
    # ------------------------------------------------------------------ #
    def puede_cargar(self, pedido: Pedido) -> bool:
        """Verifica si puede cargar un pedido dado su peso y volumen."""
        return (
            self.peso_cargado   + pedido.peso_kg    <= self.capacidad_kg and
            self.volumen_cargado + pedido.volumen_m3 <= self.capacidad_m3
        )

    def asignar_pedido(self, pedido: Pedido) -> bool:
        """
        Intenta asignar un pedido al repartidor.
        Retorna True si fue exitoso, False si excede capacidad.
        """
        if not self.puede_cargar(pedido):
            return False
        self.pedidos_asignados.append(pedido)
        from modelos.pedido import EstadoPedido
        pedido.estado = EstadoPedido.ASIGNADO
        return True

    def posicion(self) -> tuple[float, float]:
        """Retorna posición actual como (lat, lon)."""
        return (self.latitud_actual, self.longitud_actual)

    def actualizar_posicion(self, lat: float, lon: float):
        """Actualiza la posición GPS del repartidor."""
        self.latitud_actual  = lat
        self.longitud_actual = lon

    def __repr__(self) -> str:
        return (f"Repartidor({self.id_repartidor} | {self.nombre} | "
                f"{self.vehiculo.value} | "
                f"{self.peso_cargado:.1f}/{self.capacidad_kg}kg | "
                f"pedidos={len(self.pedidos_asignados)})")

    def to_dict(self) -> dict:
        return {
            "id_repartidor"    : self.id_repartidor,
            "nombre"           : self.nombre,
            "vehiculo"         : self.vehiculo.value,
            "latitud_actual"   : self.latitud_actual,
            "longitud_actual"  : self.longitud_actual,
            "capacidad_kg"     : self.capacidad_kg,
            "capacidad_m3"     : self.capacidad_m3,
            "peso_cargado"     : self.peso_cargado,
            "disponible"       : self.disponible,
            "sector_asignado"  : self.sector_asignado,
            "pedidos_asignados": [p.id_pedido for p in self.pedidos_asignados],
        }