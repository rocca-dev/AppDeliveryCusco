"""
api/estado.py — Estado Global de la Aplicación (AppState)
==========================================================
Instancia única que mantiene el grafo, pedidos, repartidores,
coordinador y caché de rutas accesible desde todos los routers.

Exportaciones:
    app_state : AppState  — singleton del sistema
"""

from __future__ import annotations

from typing import Optional

from core.geo import stats_cache_haversine
from modelos.cargador import inicializar_sistema
from algoritmos.dp.dijkstra_memo import DijkstraMemo
from algoritmos.busqueda import IndicePedidos
from algoritmos.ordenacion import merge_sort
from dispatcher.coordinator import DeliveryCoordinator


class AppState:
    """
    Estado central del sistema.

    Mantiene las referencias a:
      - grafo              : Grafo vial de Cusco
      - pedidos            : Lista de pedidos activos
      - repartidores       : Lista de repartidores disponibles
      - coordinator        : DeliveryCoordinator (thread-safe, evita colisiones)
      - ruta_pd            : DijkstraMemo compartido (caché LRU de rutas)
      - _indice_pedidos    : IndicePedidos (hash map O(1) por ID/sector)
      - _pedidos_ordenados : Lista ordenada por id_pedido (búsqueda binaria O(log n))
    """

    def __init__(self):
        grafo, pedidos, repartidores = inicializar_sistema()
        self.grafo         = grafo
        self.pedidos       = pedidos
        self.repartidores  = repartidores
        self.coordinator   = DeliveryCoordinator()
        self.ruta_pd       = DijkstraMemo(grafo)
        self._construir_indices()

    def _construir_indices(self):
        """Construye/rebuild los índices de búsqueda."""
        self._indice_pedidos = IndicePedidos(self.pedidos)
        self._pedidos_ordenados = merge_sort(
            self.pedidos, clave=lambda p: p.id_pedido, descendente=False
        )

    def pedidos_pendientes(self):
        """Retorna solo los pedidos con estado PENDIENTE."""
        from modelos.pedido import Pedido as PedidoModel
        return PedidoModel.solo_pendientes(self.pedidos)

    def buscar_por_id(self, id_pedido: str) -> Optional:
        """Búsqueda hash O(1)."""
        return self._indice_pedidos.buscar_por_id(id_pedido)

    def buscar_por_sector(self, sector: str) -> list:
        """Búsqueda hash O(k)."""
        return self._indice_pedidos.buscar_por_sector(sector)

    def buscar_binaria(self, id_pedido: str) -> Optional:
        """Búsqueda binaria O(log n) sobre lista pre-ordenada."""
        from algoritmos.busqueda import busqueda_binaria_id
        return busqueda_binaria_id(self._pedidos_ordenados, id_pedido)

    def resetear(self):
        """
        Reinicia el estado: coordinator, caché de rutas,
        índices y restablece pedidos a PENDIENTE.
        """
        self.coordinator.resetear()
        self.ruta_pd.limpiar_cache()
        from core.tipos import EstadoPedido
        for p in self.pedidos:
            p.estado = EstadoPedido.PENDIENTE
        for r in self.repartidores:
            r.pedidos_asignados.clear()
        self._construir_indices()

    def stats(self) -> dict:
        """Métricas de rendimiento de los cachés del sistema."""
        return {
            "haversine_cache": stats_cache_haversine(),
            "dijkstra_cache" : self.ruta_pd.stats_cache(),
            "coordinator"    : self.coordinator.resumen(),
            "indices"        : {
                "pedidos_indexados": self._indice_pedidos.total(),
                "pedidos_ordenados": len(self._pedidos_ordenados),
            },
        }


# ── Instancia global ──────────────────────────────────────────────────────────
app_state = AppState()
