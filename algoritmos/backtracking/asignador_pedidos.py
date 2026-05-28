"""
algoritmos/backtracking/asignador_pedidos.py — Asignación de Pedidos (Backtracking)
=====================================================================================
Asigna pedidos a repartidores mediante búsqueda exhaustiva con poda,
garantizando que se respetan todas las restricciones de capacidad.

Variante 2 del Backtracking: AsignacionPedidosBacktracking.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from modelos.pedido     import Pedido
    from modelos.repartidor import Repartidor
    from modelos.grafo      import Grafo


# ─────────────────────────────────────────────────────────────────────────────
#  Resultados
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AsignacionPedido:
    """
    Una asignación individual: pedido → repartidor.

    Atributos:
        id_pedido     : ID del pedido asignado.
        id_repartidor : ID del repartidor que lo recibe.
        motivo_rechazo: Razón si el pedido no pudo asignarse.
    """
    id_pedido     : str
    id_repartidor : str
    motivo_rechazo: str = ""


@dataclass
class ResultadoAsignacion:
    """
    Resultado completo de la asignación por backtracking.

    Atributos:
        asignaciones      : Lista de AsignacionPedido exitosas.
        pedidos_sin_asignar: IDs de pedidos que no se pudieron asignar.
        nodos_explorados  : Nodos visitados durante la búsqueda.
        podas_aplicadas   : Podas realizadas.
        tiempo_computo_ms : Tiempo de ejecución en ms.
        es_optima         : True si la solución es óptima (exploración completa).
    """
    asignaciones      : list[AsignacionPedido] = field(default_factory=list)
    pedidos_sin_asignar : list[str] = field(default_factory=list)
    nodos_explorados  : int = 0
    podas_aplicadas   : int = 0
    tiempo_computo_ms : float = 0.0
    es_optima         : bool = False


# ─────────────────────────────────────────────────────────────────────────────
#  Asignador principal
# ─────────────────────────────────────────────────────────────────────────────

class AsignadorPedidosBacktracking:
    """
    Asigna pedidos a repartidores usando backtracking con poda.

    Estrategia:
      - Explora todas las combinaciones de asignación pedido→repartidor.
      - Poda cuando un repartidor excede su capacidad.
      - Poda cuando un pedido no cabe en ningún repartidor restante.
      - Busca maximizar el valor total de pedidos asignados.

    Complejidad: O(r^p) en el peor caso, donde r = repartidores,
    p = pedidos. La poda por capacidad reduce el espacio significativamente.
    """

    def __init__(self, grafo: "Grafo"):
        self.grafo = grafo

    def asignar(
        self,
        pedidos      : list["Pedido"],
        repartidores : list["Repartidor"],
        prioridad_min = None,
    ) -> ResultadoAsignacion:
        """
        Asigna pedidos a repartidores maximizando el valor total.

        Args:
            pedidos      : Lista de pedidos pendientes.
            repartidores : Lista de repartidores disponibles.
            prioridad_min: Prioridad mínima (filtro opcional).

        Returns:
            ResultadoAsignacion con las asignaciones.
        """
        from core.tipos import Prioridad, EstadoPedido

        inicio = time.perf_counter()
        resultado = ResultadoAsignacion()

        if not pedidos or not repartidores:
            return resultado

        # Filtrar por prioridad
        if prioridad_min:
            pendientes = [
                p for p in pedidos
                if p.estado == EstadoPedido.PENDIENTE
                and p.prioridad.value >= prioridad_min.value
            ]
        else:
            pendientes = [p for p in pedidos if p.estado == EstadoPedido.PENDIENTE]

        if not pendientes:
            return resultado

        # Ordenar por valor descendente (heurística)
        pendientes.sort(key=lambda p: p.valor, reverse=True)

        mejor_asignacion: dict[str, str] = {}
        mejor_valor = 0.0
        asignacion_actual: dict[str, str] = {}
        carga_actual: dict[str, float] = {r.id_repartidor: 0.0 for r in repartidores}

        def backtrack(idx: int, valor_parcial: float):
            nonlocal mejor_valor, mejor_asignacion

            if idx >= len(pendientes):
                if valor_parcial > mejor_valor:
                    mejor_valor = valor_parcial
                    mejor_asignacion = dict(asignacion_actual)
                    resultado.es_optima = True
                return

            resultado.nodos_explorados += 1
            pedido = pendientes[idx]

            # Poda: si aunque asignáramos todos los pedidos restantes
            # no superamos el mejor valor, podar
            valor_restante = sum(p.valor for p in pendientes[idx:])
            if valor_parcial + valor_restante <= mejor_valor:
                resultado.podas_aplicadas += 1
                return

            asignado = False
            for rep in repartidores:
                if rep.puede_cargar(pedido):
                    # Asignar
                    rep.pedidos_asignados.append(pedido)
                    asignacion_actual[pedido.id_pedido] = rep.id_repartidor
                    carga_actual[rep.id_repartidor] += pedido.peso_kg
                    pedido.estado = EstadoPedido.ASIGNADO

                    backtrack(idx + 1, valor_parcial + pedido.valor)

                    # Deshacer
                    rep.pedidos_asignados.remove(pedido)
                    del asignacion_actual[pedido.id_pedido]
                    carga_actual[rep.id_repartidor] -= pedido.peso_kg
                    pedido.estado = EstadoPedido.PENDIENTE
                    asignado = True

            # También explorar no asignar este pedido
            backtrack(idx + 1, valor_parcial)

            if not asignado:
                resultado.podas_aplicadas += 1

        backtrack(0, 0.0)

        # Construir resultado
        for id_pedido, id_rep in mejor_asignacion.items():
            resultado.asignaciones.append(AsignacionPedido(
                id_pedido=id_pedido, id_repartidor=id_rep
            ))

        asignados_ids = {a.id_pedido for a in resultado.asignaciones}
        resultado.pedidos_sin_asignar = [
            p.id_pedido for p in pendientes if p.id_pedido not in asignados_ids
        ]

        resultado.tiempo_computo_ms = (time.perf_counter() - inicio) * 1000
        return resultado


# ─────────────────────────────────────────────────────────────────────────────
#  Función de conveniencia
# ─────────────────────────────────────────────────────────────────────────────

def asignar_pedidos(
    pedidos      : list["Pedido"],
    repartidores : list["Repartidor"],
    prioridad_min=None,
    grafo        : Optional["Grafo"] = None,
) -> ResultadoAsignacion:
    """
    Función de conveniencia que crea un AsignadorPedidosBacktracking
    y ejecuta la asignación.

    Args:
        pedidos      : Lista de pedidos pendientes.
        repartidores : Lista de repartidores disponibles.
        prioridad_min: Prioridad mínima (filtro opcional).
        grafo        : Grafo del mapa (opcional).

    Returns:
        ResultadoAsignacion con las asignaciones.
    """
    asignador = AsignadorPedidosBacktracking(grafo)
    return asignador.asignar(pedidos, repartidores, prioridad_min)
