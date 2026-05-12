"""
Estado global de la aplicación.
Mantiene las instancias compartidas de grafo, pedidos y repartidores.
"""

from typing import Optional
from modelos.grafo      import Grafo
from modelos.pedido     import Pedido, EstadoPedido
from modelos.repartidor import Repartidor
from modelos.cargador   import inicializar_sistema
from algoritmos.programacion_dinamica import DijkstraMemo


class AppState:
    def __init__(self):
        self.grafo: Optional[Grafo] = None
        self.pedidos: list[Pedido] = []
        self.repartidores: list[Repartidor] = []
        self.ruta_pd: Optional[DijkstraMemo] = None

    def inicializar(self, aplicar_bloqueos: bool = True):
        self.grafo, self.pedidos, self.repartidores = \
            inicializar_sistema(aplicar_bloqueos)
        self.ruta_pd = DijkstraMemo(self.grafo)

    def pedidos_pendientes(self) -> list[Pedido]:
        return [p for p in self.pedidos if p.estado == EstadoPedido.PENDIENTE]

    def pedidos_asignados(self) -> list[Pedido]:
        return [p for p in self.pedidos if p.estado == EstadoPedido.ASIGNADO]

    def resetear(self):
        for p in self.pedidos:
            p.estado = EstadoPedido.PENDIENTE
        for r in self.repartidores:
            r.pedidos_asignados.clear()
        if self.ruta_pd:
            self.ruta_pd.limpiar_cache()


app_state = AppState()
