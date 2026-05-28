"""
modelos/pedido.py — Modelo de Dominio: Pedido
==============================================
Representa un pedido de entrega en el sistema de rutas de Cusco.

CAMBIOS respecto a la versión original
───────────────────────────────────────
  1. Prioridad y EstadoPedido ahora se importan desde core.tipos
     (eliminada la duplicación de definición).

  2. Método de clase solo_pendientes() centraliza el filtrado que
     antes se repetía en greedy.py, programacion_dinamica.py,
     backtracking.py y en el router de la API.

  3. Re-exporta Prioridad y EstadoPedido por compatibilidad con
     código que ya los importa desde este módulo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing      import Optional
import time

# Importar tipos desde el núcleo centralizado
from core.tipos import Prioridad, EstadoPedido   # noqa: F401  (re-export)


# ─────────────────────────────────────────────────────────────────────────────
#  Modelo principal
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Pedido:
    """
    Representa un pedido de entrega.

    Atributos
    ──────────
    id_pedido   : Identificador único  (ej. "P001")
    cliente     : Nombre del cliente
    sector      : Zona de Cusco  (ej. "San Blas", "Wanchaq")
    latitud     : Coordenada GPS real del destino
    longitud    : Coordenada GPS real del destino
    peso_kg     : Peso del paquete en kilogramos
    volumen_m3  : Volumen del paquete en metros cúbicos
    valor       : Valor económico / importancia (usado en Knapsack)
    prioridad   : Nivel de urgencia  (Prioridad enum de core.tipos)
    estado      : Estado actual  (EstadoPedido enum de core.tipos)
    timestamp   : Momento de creación  (epoch Unix)
    id_nodo     : ID del nodo del grafo más cercano al destino
    """
    id_pedido  : str
    cliente    : str
    sector     : str
    latitud    : float
    longitud   : float
    peso_kg    : float
    volumen_m3 : float
    valor      : float
    prioridad  : Prioridad    = Prioridad.MEDIA
    estado     : EstadoPedido = EstadoPedido.PENDIENTE
    timestamp  : float        = field(default_factory=time.time)
    id_nodo    : Optional[str] = None

    # ── Comparadores ──────────────────────────────────────────────────────────
    def __lt__(self, other: "Pedido") -> bool:
        """Menor prioridad numérica = menos urgente (permite sort directo)."""
        return self.prioridad.value < other.prioridad.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pedido):
            return NotImplemented
        return self.id_pedido == other.id_pedido

    def __hash__(self) -> int:
        return hash(self.id_pedido)

    # ── Utilidades de instancia ───────────────────────────────────────────────
    def coordenadas(self) -> tuple[float, float]:
        """Retorna (latitud, longitud) como tupla."""
        return (self.latitud, self.longitud)

    def es_urgente(self) -> bool:
        """True si la prioridad es URGENTE o ALTA."""
        return self.prioridad in (Prioridad.URGENTE, Prioridad.ALTA)

    # ── Serialización ─────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        """Serializa el pedido a diccionario (para JSON/API)."""
        return {
            "id_pedido"  : self.id_pedido,
            "cliente"    : self.cliente,
            "sector"     : self.sector,
            "latitud"    : self.latitud,
            "longitud"   : self.longitud,
            "peso_kg"    : self.peso_kg,
            "volumen_m3" : self.volumen_m3,
            "valor"      : self.valor,
            "prioridad"  : self.prioridad.name,
            "estado"     : self.estado.value,
            "timestamp"  : self.timestamp,
            "id_nodo"    : self.id_nodo,
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

    def __repr__(self) -> str:
        return (f"Pedido({self.id_pedido} | {self.cliente} | "
                f"{self.sector} | {self.prioridad.name} | "
                f"{self.peso_kg}kg | S/.{self.valor})")

    # ── Métodos de clase — filtrado centralizado ──────────────────────────────
    @classmethod
    def solo_pendientes(cls, pedidos: list["Pedido"]) -> list["Pedido"]:
        """
        Filtra y retorna solo los pedidos con estado PENDIENTE.

        REEMPLAZA el patrón repetido:
            [p for p in pedidos if p.estado == EstadoPedido.PENDIENTE]
        que aparecía en greedy.py, programacion_dinamica.py,
        backtracking.py y en el router de la API.

        Complejidad: O(n)

        Args:
            pedidos : Lista completa de pedidos.

        Returns:
            Nueva lista con solo los pedidos pendientes.
        """
        return [p for p in pedidos if p.estado == EstadoPedido.PENDIENTE]

    @classmethod
    def por_prioridad_minima(
        cls,
        pedidos      : list["Pedido"],
        prioridad_min: Prioridad,
    ) -> list["Pedido"]:
        """
        Filtra pedidos pendientes cuya prioridad es >= prioridad_min.

        Usado por el Backtracking para descartar pedidos de baja
        prioridad antes de la exploración.

        Complejidad: O(n)

        Args:
            pedidos       : Lista completa.
            prioridad_min : Umbral mínimo (inclusivo).

        Returns:
            Lista filtrada y ordenada por prioridad descendente.
        """
        candidatos = [
            p for p in pedidos
            if p.estado == EstadoPedido.PENDIENTE
            and p.prioridad.value >= prioridad_min.value
        ]
        return sorted(candidatos, key=lambda p: p.prioridad.value, reverse=True)
