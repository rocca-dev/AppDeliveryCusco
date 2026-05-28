"""
dispatcher/coordinator.py — Coordinador de Asignaciones
=========================================================
Registro central thread-safe que evita que dos repartidores reclamen
el mismo pedido o compartan nodos de entrega conflictivos.

PROBLEMA QUE RESUELVE
──────────────────────
El código original tenía una race condition: si dos llamadas al
endpoint /algoritmos/greedy/asignacion se ejecutaban simultáneamente
(o si se llamaban algoritmos distintos en paralelo), ambas leían la
misma lista app_state.pedidos y podían asignar el mismo pedido P_x
a dos repartidores distintos antes de que cualquiera marcara
P_x.estado = ASIGNADO.

Flujo con el coordinador:
  1. Algoritmo solicita reservar_pedido(P_x, R_01)
  2. Coordinator adquiere lock → P_x aún libre → lo marca → devuelve True
  3. Otro hilo solicita reservar_pedido(P_x, R_02)
  4. Coordinator adquiere lock → P_x ya tomado → devuelve False → no asigna

DETECCIÓN DE SOLAPAMIENTO DE RUTAS
────────────────────────────────────
  marcar_nodo_en_ruta(nodo, id_rep) registra qué repartidor pasará
  por ese nodo del grafo.  consultar_nodo_en_ruta() permite al
  PlanificadorRutasPD detectar solapamientos antes de confirmar la ruta.

  Nota: el solapamiento de NODOS DE TRÁNSITO (calles) es inevitable en
  un grafo urbano; lo que se detecta son los NODOS DE ENTREGA (puntos
  donde el repartidor se detiene) para evitar dobles entregas.

Thread-safety
─────────────
  Un único threading.Lock protege todas las estructuras internas.
  Las operaciones son O(1) y de duración mínima → contención baja.

Análisis Big-O
──────────────
  reservar_pedido    : O(1) amortizado
  liberar_pedido     : O(1)
  marcar_nodo_en_ruta: O(1)
  consultar_nodo     : O(1)
  resetear           : O(p + n)  donde p=pedidos, n=nodos registrados
"""

from __future__ import annotations

import threading
from typing import Optional


class DeliveryCoordinator:
    """
    Registro central de pedidos y nodos de entrega reservados.

    Se mantiene una instancia global en app_state y se inyecta
    en AsignacionGreedy, Mochila01.resolver_flota() y
    PlanificadorRutasPD para que todos los algoritmos compartan
    el mismo estado de reservas.

    Uso básico:
        coordinator = DeliveryCoordinator()

        # Al inicio de cada asignación
        if coordinator.reservar_pedido("P001", "R01"):
            # procesar pedido P001 para R01
            ...
            coordinator.marcar_nodo_en_ruta("san_blas", "R01")
        else:
            # P001 ya fue tomado por otro repartidor
            ...

        # Al resetear el sistema
        coordinator.resetear()
    """

    def __init__(self):
        self._lock             = threading.Lock()
        # id_pedido → id_repartidor que lo reservó
        self._pedidos_tomados  : dict[str, str] = {}
        # id_nodo → id_repartidor que lo tiene en su ruta de entrega
        self._nodos_en_ruta    : dict[str, str] = {}

    # ── Gestión de pedidos ────────────────────────────────────────────────────

    def reservar_pedido(self, id_pedido: str, id_rep: str) -> bool:
        """
        Intenta reservar un pedido para un repartidor de forma atómica.

        Si el pedido ya está reservado por otro repartidor, retorna False
        sin modificar el estado.  Si el mismo repartidor ya lo reservó
        (idempotencia), retorna True.

        Args:
            id_pedido : ID del pedido a reservar.
            id_rep    : ID del repartidor que lo solicita.

        Returns:
            True si la reserva fue exitosa, False si ya estaba tomado.
        """
        with self._lock:
            actual = self._pedidos_tomados.get(id_pedido)
            if actual is None:
                # Pedido libre → reservar
                self._pedidos_tomados[id_pedido] = id_rep
                return True
            # Idempotente: el mismo repartidor ya lo tenía
            return actual == id_rep

    def liberar_pedido(self, id_pedido: str):
        """
        Libera la reserva de un pedido (p. ej. al cancelar o resetear).

        Operación idempotente: si el pedido no estaba reservado, no hace nada.

        Args:
            id_pedido : ID del pedido a liberar.
        """
        with self._lock:
            self._pedidos_tomados.pop(id_pedido, None)

    def quien_tiene_pedido(self, id_pedido: str) -> Optional[str]:
        """
        Retorna el id_repartidor que tiene reservado el pedido, o None.

        Args:
            id_pedido : ID del pedido a consultar.

        Returns:
            id_repartidor o None si el pedido está libre.
        """
        with self._lock:
            return self._pedidos_tomados.get(id_pedido)

    def pedido_esta_libre(self, id_pedido: str) -> bool:
        """
        Verifica si un pedido no tiene ninguna reserva activa.

        Args:
            id_pedido : ID del pedido.

        Returns:
            True si está libre, False si está reservado.
        """
        with self._lock:
            return id_pedido not in self._pedidos_tomados

    # ── Gestión de nodos de entrega ───────────────────────────────────────────

    def marcar_nodo_en_ruta(self, id_nodo: str, id_rep: str):
        """
        Registra que un repartidor tiene programada una entrega en este nodo.

        Solo debe llamarse para nodos de ENTREGA (id_nodo del pedido),
        no para nodos de tránsito.  Permite al planificador detectar
        si dos repartidores irían al mismo destino de entrega.

        Si el nodo ya estaba marcado por otro repartidor, el nuevo
        repartidor sobreescribe (el llamador debe haber verificado
        con nodo_entrega_libre() antes de marcar).

        Args:
            id_nodo : ID del nodo de entrega.
            id_rep  : ID del repartidor que lo atenderá.
        """
        with self._lock:
            self._nodos_en_ruta[id_nodo] = id_rep

    def nodo_entrega_libre(self, id_nodo: str, id_rep: str) -> bool:
        """
        Verifica si un nodo de entrega está disponible para el repartidor dado.

        Un nodo está disponible si:
          a) No tiene ningún repartidor asignado, O
          b) El repartidor asignado es el mismo que pregunta (idempotente).

        Args:
            id_nodo : ID del nodo a verificar.
            id_rep  : ID del repartidor que quiere atender ese nodo.

        Returns:
            True si puede ir ahí, False si otro repartidor ya lo tiene.
        """
        with self._lock:
            ocupado_por = self._nodos_en_ruta.get(id_nodo)
            return ocupado_por is None or ocupado_por == id_rep

    def quien_atiende_nodo(self, id_nodo: str) -> Optional[str]:
        """
        Retorna el id_repartidor asignado a un nodo de entrega, o None.

        Args:
            id_nodo : ID del nodo a consultar.

        Returns:
            id_repartidor o None si el nodo está libre.
        """
        with self._lock:
            return self._nodos_en_ruta.get(id_nodo)

    # ── Diagnóstico ───────────────────────────────────────────────────────────

    def resumen(self) -> dict:
        """
        Retorna un snapshot del estado actual del coordinador.

        Útil para el endpoint /health de la API para monitorear
        cuántos pedidos y nodos están actualmente reservados.

        Returns:
            dict con contadores y listas de IDs reservados.
        """
        with self._lock:
            return {
                "pedidos_reservados" : len(self._pedidos_tomados),
                "nodos_en_ruta"      : len(self._nodos_en_ruta),
                "detalle_pedidos"    : dict(self._pedidos_tomados),
                "detalle_nodos"      : dict(self._nodos_en_ruta),
            }

    # ── Reset ─────────────────────────────────────────────────────────────────

    def resetear(self):
        """
        Limpia todas las reservas activas.

        Debe llamarse cuando app_state.resetear() se invoca, para
        que los algoritmos puedan asignar desde cero.

        Complejidad: O(p + n) donde p = pedidos reservados, n = nodos.
        """
        with self._lock:
            self._pedidos_tomados.clear()
            self._nodos_en_ruta.clear()
