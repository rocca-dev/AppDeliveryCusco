"""
Módulo: Búsqueda
Implementa Búsqueda Binaria, Hash Map e índices por sector/ID.

ESTRUCTURAS IMPLEMENTADAS:
  1. Búsqueda Binaria    → O(log n)  sobre lista ordenada por ID
  2. Hash Map (dict)     → O(1) amortizado  por ID o sector
  3. Índice por sector   → O(1) lookup + O(k) iteración (k = pedidos del sector)

¿Por qué no búsqueda lineal O(n)?
  Con 1000 pedidos: lineal = 1000 ops, binaria = 10 ops, hash = 1 op.
  Para sistemas de reparto en tiempo real, O(log n) u O(1) es obligatorio.
"""

from __future__ import annotations
from typing import Optional
from modelos.pedido     import Pedido
from modelos.repartidor import Repartidor


# ─────────────────────────────────────────────────────────────
#  1. BÚSQUEDA BINARIA
# ─────────────────────────────────────────────────────────────

def busqueda_binaria_id(pedidos_ordenados: list[Pedido],
                        id_buscado: str) -> Optional[Pedido]:
    """
    Busca un pedido por ID en una lista ORDENADA alfabéticamente por id_pedido.

    Precondición: la lista debe estar ordenada por id_pedido (usar
                  merge_sort con clave=lambda p: p.id_pedido antes).

    Args:
        pedidos_ordenados : Lista ordenada por id_pedido.
        id_buscado        : ID a encontrar (ej. "P005").

    Returns:
        El Pedido encontrado, o None si no existe.

    Complejidad:
        Temporal O(log n) — divide el espacio de búsqueda a la mitad en cada paso
        Espacial O(1)     — solo variables de índice, sin copias

    Ejemplo con n=10:
        Lineal  buscaría hasta 10 comparaciones.
        Binaria necesita máximo log2(10) ≈ 4 comparaciones.
    """
    izq, der = 0, len(pedidos_ordenados) - 1

    while izq <= der:
        medio = (izq + der) // 2
        id_medio = pedidos_ordenados[medio].id_pedido

        if id_medio == id_buscado:
            return pedidos_ordenados[medio]   # ¡encontrado!
        elif id_medio < id_buscado:
            izq = medio + 1                   # buscar en mitad derecha
        else:
            der = medio - 1                   # buscar en mitad izquierda

    return None                               # no encontrado


def busqueda_binaria_rango_prioridad(pedidos_ord_prioridad: list[Pedido],
                                     valor_prioridad: int) -> list[Pedido]:
    """
    Extrae todos los pedidos con un nivel de prioridad específico.
    Usa dos búsquedas binarias para hallar los extremos del rango.

    Precondición: lista ordenada ASCENDENTE por prioridad.value.

    Returns:
        Sublista de pedidos con esa prioridad exacta.

    Complejidad:
        Temporal O(log n + k)  donde k = pedidos con esa prioridad
        Espacial O(k)
    """
    n = len(pedidos_ord_prioridad)

    # Primer índice con ese valor de prioridad
    inicio = _limite_inferior(pedidos_ord_prioridad, valor_prioridad, n)
    # Último índice + 1
    fin    = _limite_superior(pedidos_ord_prioridad, valor_prioridad, n)

    return pedidos_ord_prioridad[inicio:fin]


def _limite_inferior(lista: list[Pedido], val: int, n: int) -> int:
    """Búsqueda binaria del primer índice con prioridad.value == val."""
    izq, der = 0, n
    while izq < der:
        m = (izq + der) // 2
        if lista[m].prioridad.value < val:
            izq = m + 1
        else:
            der = m
    return izq


def _limite_superior(lista: list[Pedido], val: int, n: int) -> int:
    """Búsqueda binaria del primer índice con prioridad.value > val."""
    izq, der = 0, n
    while izq < der:
        m = (izq + der) // 2
        if lista[m].prioridad.value <= val:
            izq = m + 1
        else:
            der = m
    return izq


# ─────────────────────────────────────────────────────────────
#  2. HASH MAP — Índice por ID
# ─────────────────────────────────────────────────────────────

class IndicePedidos:
    """
    Índice hash que permite búsqueda O(1) de pedidos por ID,
    y O(k) por sector (k = cantidad de pedidos en ese sector).

    Internamente usa dos diccionarios Python (tablas hash):
      - _por_id     : { id_pedido → Pedido }
      - _por_sector : { sector    → [Pedido, ...] }

    Complejidad de construcción : O(n)
    Complejidad de búsqueda     : O(1) por ID, O(k) por sector
    Complejidad espacial        : O(n)
    """

    def __init__(self, pedidos: list[Pedido]):
        self._por_id    : dict[str, Pedido]        = {}
        self._por_sector: dict[str, list[Pedido]]  = {}
        self._construir(pedidos)

    def _construir(self, pedidos: list[Pedido]):
        """Construye ambos índices en O(n)."""
        for p in pedidos:
            # Índice por ID
            self._por_id[p.id_pedido] = p

            # Índice por sector
            if p.sector not in self._por_sector:
                self._por_sector[p.sector] = []
            self._por_sector[p.sector].append(p)

    # ── Búsquedas ─────────────────────────────────────────────

    def buscar_por_id(self, id_pedido: str) -> Optional[Pedido]:
        """
        Retorna el pedido con ese ID o None.
        O(1) — acceso directo a tabla hash.
        """
        return self._por_id.get(id_pedido)

    def buscar_por_sector(self, sector: str) -> list[Pedido]:
        """
        Retorna todos los pedidos de un sector.
        O(1) acceso + O(k) copia donde k = pedidos del sector.
        """
        return self._por_sector.get(sector, [])

    def sectores_disponibles(self) -> list[str]:
        """Lista de sectores con al menos un pedido. O(s) donde s = sectores."""
        return list(self._por_sector.keys())

    def existe(self, id_pedido: str) -> bool:
        """O(1)"""
        return id_pedido in self._por_id

    # ── Mantenimiento del índice ───────────────────────────────

    def agregar(self, pedido: Pedido):
        """Agrega un pedido al índice. O(1) amortizado."""
        self._por_id[pedido.id_pedido] = pedido
        if pedido.sector not in self._por_sector:
            self._por_sector[pedido.sector] = []
        self._por_sector[pedido.sector].append(pedido)

    def eliminar(self, id_pedido: str) -> bool:
        """
        Elimina un pedido del índice por ID.
        O(1) en _por_id, O(k) en _por_sector para encontrar y remover.
        """
        pedido = self._por_id.pop(id_pedido, None)
        if pedido is None:
            return False
        sector_lista = self._por_sector.get(pedido.sector, [])
        if pedido in sector_lista:
            sector_lista.remove(pedido)
        return True

    def total(self) -> int:
        """Cantidad de pedidos indexados. O(1)"""
        return len(self._por_id)

    def __repr__(self) -> str:
        return (f"IndicePedidos(total={self.total()}, "
                f"sectores={len(self._por_sector)})")


# ─────────────────────────────────────────────────────────────
#  3. ÍNDICE DE REPARTIDORES
# ─────────────────────────────────────────────────────────────

class IndiceRepartidores:
    """
    Índice hash para búsqueda O(1) de repartidores por ID o sector.

    Complejidad de construcción : O(r) donde r = número de repartidores
    Complejidad de búsqueda     : O(1)
    """

    def __init__(self, repartidores: list[Repartidor]):
        self._por_id    : dict[str, Repartidor]       = {}
        self._por_sector: dict[str, list[Repartidor]] = {}
        for r in repartidores:
            self._por_id[r.id_repartidor] = r
            sector = r.sector_asignado or "sin_sector"
            if sector not in self._por_sector:
                self._por_sector[sector] = []
            self._por_sector[sector].append(r)

    def buscar_por_id(self, id_rep: str) -> Optional[Repartidor]:
        """O(1)"""
        return self._por_id.get(id_rep)

    def buscar_por_sector(self, sector: str) -> list[Repartidor]:
        """O(1) acceso"""
        return self._por_sector.get(sector, [])

    def disponibles(self) -> list[Repartidor]:
        """Filtra repartidores disponibles. O(r)"""
        return [r for r in self._por_id.values() if r.disponible]

    def __repr__(self) -> str:
        return f"IndiceRepartidores(total={len(self._por_id)})"