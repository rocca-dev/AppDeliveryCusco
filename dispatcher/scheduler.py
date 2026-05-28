"""
dispatcher/scheduler.py — Planificador de Entregas
====================================================
Orquesta el flujo completo de asignación y planificación de rutas.

Flujo:
  1. Knapsack: optimizar carga de cada repartidor.
  2. Dijkstra: generar rutas óptimas para cada repartidor.
  3. Registrar asignaciones en el DeliveryCoordinator.

Integración:
  - Usa el DeliveryCoordinator para evitar colisiones entre repartidores.
  - Reutiliza el caché de DijkstraMemo para consultas repetidas.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from modelos.pedido     import Pedido
    from modelos.repartidor import Repartidor
    from modelos.grafo      import Grafo
    from dispatcher.coordinator import DeliveryCoordinator


class Scheduler:
    """
    Planificador de entregas que orquesta el flujo completo.

    Compone:
      - Knapsack (Mochila01) para asignación óptima de carga.
      - DijkstraMemo para rutas óptimas entre entregas.
      - DeliveryCoordinator para reservas atómicas.

    Uso:
        scheduler = Scheduler(coordinator)
        resultado = scheduler.ejecutar(pedidos, repartidores, grafo)

    Complejidad:
        O(r × (k × W + m × (V+E) log V))
        donde r = repartidores, k = candidatos por repartidor,
        W = capacidad entera, m = pedidos elegidos, V, E = grafo.
    """

    def __init__(self, coordinator: "DeliveryCoordinator"):
        self.coordinator = coordinator

    def ejecutar(
        self,
        pedidos      : list["Pedido"],
        repartidores : list["Repartidor"],
        grafo        : "Grafo",
        bonus_urgente: float = 1.5,
    ) -> dict:
        """
        Ejecuta el pipeline completo: Knapsack → Dijkstra → registro.

        Args:
            pedidos      : Lista de pedidos del sistema.
            repartidores : Lista de repartidores disponibles.
            grafo        : Grafo del mapa de Cusco.
            bonus_urgente: Bonus para pedidos URGENTES en Knapsack.

        Returns:
            dict con el resumen de la planificación:
                - planes: lista de rutas planificadas
                - estadisticas: métricas globales
        """
        from algoritmos.dp.knapsack import Mochila01
        from algoritmos.dp.dijkstra_memo import DijkstraMemo
        from algoritmos.dp.planificador import PlanificadorRutasPD
        from core.tipos import EstadoPedido

        # Instanciar algoritmos
        mochila = Mochila01()
        dijkstra = DijkstraMemo(grafo)
        planificador = PlanificadorRutasPD(mochila, dijkstra)

        # Planificar rutas
        planes = planificador.planificar(
            pedidos, repartidores, grafo,
            coordinator=self.coordinator,
            bonus_urgente=bonus_urgente,
        )

        # Registrar en coordinator
        for plan in planes:
            if plan.camino:
                for i, nodo in enumerate(plan.camino):
                    self.coordinator.marcar_nodo_en_ruta(
                        nodo, plan.repartidor.id_repartidor
                    )

        # Estadísticas
        total_asignados = sum(len(p.pedidos) for p in planes)
        total_distancia = sum(p.distancia_total_m for p in planes)
        total_tiempo    = sum(p.tiempo_total_min for p in planes)

        return {
            "planes": [
                {
                    "repartidor"       : p.repartidor.id_repartidor,
                    "pedidos"          : [ped.id_pedido for ped in p.pedidos],
                    "camino"           : p.camino,
                    "distancia_total_m": round(p.distancia_total_m, 2),
                    "tiempo_total_min" : round(p.tiempo_total_min, 2),
                }
                for p in planes
            ],
            "estadisticas": {
                "total_pedidos"       : len(pedidos),
                "total_asignados"     : total_asignados,
                "total_sin_asignar"   : len(pedidos) - total_asignados,
                "distancia_flota_m"   : round(total_distancia, 2),
                "tiempo_flota_min"    : round(total_tiempo, 2),
                "repartidores_usados" : sum(1 for p in planes if p.pedidos),
            },
        }
