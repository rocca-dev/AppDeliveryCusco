"""
Modelo: Pedido
Representa un pedido de entrega en el sistema de rutas de Cusco.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class Prioridad(Enum):
    """Niveles de prioridad para los pedidos."""
    BAJA   = 1
    MEDIA  = 2
    ALTA   = 3
    URGENTE = 4


class EstadoPedido(Enum):
    """Estado actual del pedido."""
    PENDIENTE   = "pendiente"
    ASIGNADO    = "asignado"
    EN_RUTA     = "en_ruta"
    ENTREGADO   = "entregado"
    CANCELADO   = "cancelado"


@dataclass
class Pedido:
    """
    Representa un pedido de entrega.

    Atributos:
        id_pedido   : Identificador único (ej. "P001")
        cliente     : Nombre del cliente
        sector      : Zona de Cusco (ej. "San Blas", "Wanchaq")
        latitud     : Coordenada geográfica real
        longitud    : Coordenada geográfica real
        peso_kg     : Peso del paquete en kilogramos
        volumen_m3  : Volumen del paquete en metros cúbicos
        valor       : Valor económico / importancia del pedido (para Knapsack)
        prioridad   : Nivel de urgencia (Enum Prioridad)
        estado      : Estado actual del pedido
        timestamp   : Momento de creación (epoch)
        id_nodo     : Nodo del grafo más cercano al destino
    """
    id_pedido : str
    cliente   : str
    sector    : str
    latitud   : float
    longitud  : float
    peso_kg   : float
    volumen_m3: float
    valor     : float
    prioridad : Prioridad        = Prioridad.MEDIA
    estado    : EstadoPedido     = EstadoPedido.PENDIENTE
    timestamp : float            = field(default_factory=time.time)
    id_nodo   : Optional[str]    = None

    # ------------------------------------------------------------------ #
    #  Comparadores — permiten ordenar pedidos directamente               #
    # ------------------------------------------------------------------ #
    def __lt__(self, other: "Pedido") -> bool:
        """Menor prioridad numérica = menos urgente."""
        return self.prioridad.value < other.prioridad.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pedido):
            return False
        return self.id_pedido == other.id_pedido

    def __repr__(self) -> str:
        return (f"Pedido({self.id_pedido} | {self.cliente} | "
                f"{self.sector} | {self.prioridad.name} | "
                f"{self.peso_kg}kg | S/.{self.valor})")

    # ------------------------------------------------------------------ #
    #  Utilidades                                                          #
    # ------------------------------------------------------------------ #
    def coordenadas(self) -> tuple[float, float]:
        """Retorna (latitud, longitud) como tupla."""
        return (self.latitud, self.longitud)

    def to_dict(self) -> dict:
        """Serializa el pedido a diccionario (para JSON/API)."""
        return {
            "id_pedido" : self.id_pedido,
            "cliente"   : self.cliente,
            "sector"    : self.sector,
            "latitud"   : self.latitud,
            "longitud"  : self.longitud,
            "peso_kg"   : self.peso_kg,
            "volumen_m3": self.volumen_m3,
            "valor"     : self.valor,
            "prioridad" : self.prioridad.name,
            "estado"    : self.estado.value,
            "timestamp" : self.timestamp,
            "id_nodo"   : self.id_nodo,
        }

    @staticmethod
    def from_dict(data: dict) -> "Pedido":
        """Deserializa un diccionario a objeto Pedido."""
        return Pedido(
            id_pedido  = data["id_pedido"],
            cliente    = data["cliente"],
            sector     = data["sector"],
            latitud    = data["latitud"],
            longitud   = data["longitud"],
            peso_kg    = data["peso_kg"],
            volumen_m3 = data["volumen_m3"],
            valor      = data["valor"],
            prioridad  = Prioridad[data.get("prioridad", "MEDIA")],
            estado     = EstadoPedido(data.get("estado", "pendiente")),
            timestamp  = data.get("timestamp", time.time()),
            id_nodo    = data.get("id_nodo"),
        )