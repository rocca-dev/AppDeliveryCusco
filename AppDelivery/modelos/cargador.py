"""
Cargador de datos del sistema.
Inicializa el grafo, pedidos y repartidores desde archivos JSON.
"""

import json
import os
from modelos.grafo      import Grafo, Nodo, Arista
from modelos.pedido     import Pedido
from modelos.repartidor import Repartidor, TipoVehiculo

# Ruta base de los datos
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE_DIR, "..", "datos")


def ruta(nombre_archivo: str) -> str:
    return os.path.join(DATOS_DIR, nombre_archivo)


# ────────────────────────────────────────────────────────────────────────────
#  Grafo
# ────────────────────────────────────────────────────────────────────────────
def cargar_grafo(aplicar_bloqueos: bool = True) -> Grafo:
    """
    Carga el grafo del mapa de Cusco desde mapa_cusco.json.
    Si aplicar_bloqueos=True, marca las calles bloqueadas activas.
    """
    grafo = Grafo.cargar_json(ruta("mapa_cusco.json"))

    if aplicar_bloqueos:
        try:
            with open(ruta("calles_bloqueadas.json"), encoding="utf-8") as f:
                bloqueos = json.load(f)
            for b in bloqueos:
                grafo.bloquear_calle(b["origen"], b["destino"])
        except FileNotFoundError:
            pass  # Sin bloqueos activos

    return grafo


# ────────────────────────────────────────────────────────────────────────────
#  Pedidos
# ────────────────────────────────────────────────────────────────────────────
def cargar_pedidos() -> list[Pedido]:
    """Carga la lista de pedidos desde pedidos.json."""
    with open(ruta("pedidos.json"), encoding="utf-8") as f:
        data = json.load(f)
    return [Pedido.from_dict(d) for d in data]


def guardar_pedidos(pedidos: list[Pedido]):
    """Persiste la lista de pedidos en pedidos.json."""
    with open(ruta("pedidos.json"), "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in pedidos], f,
                  ensure_ascii=False, indent=2)


# ────────────────────────────────────────────────────────────────────────────
#  Repartidores
# ────────────────────────────────────────────────────────────────────────────
def cargar_repartidores() -> list[Repartidor]:
    """Carga la lista de repartidores desde repartidores.json."""
    with open(ruta("repartidores.json"), encoding="utf-8") as f:
        data = json.load(f)
    repartidores = []
    for d in data:
        r = Repartidor(
            id_repartidor    = d["id_repartidor"],
            nombre           = d["nombre"],
            vehiculo         = TipoVehiculo(d["vehiculo"]),
            latitud_actual   = d["latitud_actual"],
            longitud_actual  = d["longitud_actual"],
            disponible       = d.get("disponible", True),
            sector_asignado  = d.get("sector_asignado"),
        )
        repartidores.append(r)
    return repartidores


# ────────────────────────────────────────────────────────────────────────────
#  Inicialización completa del sistema
# ────────────────────────────────────────────────────────────────────────────
def inicializar_sistema(aplicar_bloqueos: bool = True) -> tuple:
    """
    Carga y retorna (grafo, pedidos, repartidores) listos para usar.
    Asigna automáticamente id_nodo a cada pedido según coordenadas.
    """
    grafo       = cargar_grafo(aplicar_bloqueos)
    pedidos     = cargar_pedidos()
    repartidores = cargar_repartidores()

    # Asignar nodo más cercano a cada pedido si no lo tiene
    for p in pedidos:
        if not p.id_nodo:
            p.id_nodo = grafo.nodo_mas_cercano(p.latitud, p.longitud)

    return grafo, pedidos, repartidores