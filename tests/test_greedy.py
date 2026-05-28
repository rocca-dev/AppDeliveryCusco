"""
tests/test_greedy.py — Tests de algoritmos/greedy/
===================================================
Verifica NearestNeighborGreedy y AsignacionGreedy con y sin coordinator.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.pedido             import Pedido
from modelos.repartidor         import Repartidor
from modelos.cargador           import cargar_grafo
from core.tipos                 import TipoVehiculo, Prioridad, EstadoPedido
from algoritmos.greedy          import (NearestNeighborGreedy,
                                         AsignacionGreedy,
                                         distancia_ruta_aleatoria)
from dispatcher.coordinator     import DeliveryCoordinator


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _pedidos():
    return [
        Pedido("P1","Ana",   "Wanchaq",  -13.525,-71.970, 2.0, 0.01, 100.0, Prioridad.MEDIA),
        Pedido("P2","Bruno", "Santiago", -13.535,-71.962, 5.0, 0.02, 200.0, Prioridad.ALTA),
        Pedido("P3","Carla", "San Blas", -13.514,-71.979, 3.0, 0.01, 150.0, Prioridad.BAJA),
        Pedido("P4","Diego", "Centro",   -13.517,-71.978, 8.0, 0.05, 300.0, Prioridad.URGENTE),
        Pedido("P5","Elena", "Wanchaq",  -13.540,-71.950, 1.0, 0.01,  80.0, Prioridad.MEDIA),
    ]

def _grafo():
    return cargar_grafo(aplicar_bloqueos=False)

def _repartidor(id_="R01", vehiculo=TipoVehiculo.MOTO):
    return Repartidor(id_, "Test", vehiculo,
                      latitud_actual=-13.5170, longitud_actual=-71.9785)


# ── NearestNeighborGreedy ─────────────────────────────────────────────────────

def test_nn_ruta_no_vacia():
    """Con pedidos disponibles, la ruta no debe estar vacía."""
    g    = _grafo()
    nn   = NearestNeighborGreedy(g)
    rep  = _repartidor()
    peds = _pedidos()
    res  = nn.construir_ruta(rep, peds)
    assert len(res.ruta_pedidos) > 0, "Se esperaba al menos 1 pedido en la ruta"
    print(f"  PASS test_nn_ruta_no_vacia  ({len(res.ruta_pedidos)} pedidos)")


def test_nn_respeta_capacidad():
    """El peso total asignado no debe superar la capacidad del repartidor."""
    g    = _grafo()
    nn   = NearestNeighborGreedy(g)
    rep  = _repartidor("R04", TipoVehiculo.BICICLETA)   # 15 kg
    peds = _pedidos()
    res  = nn.construir_ruta(rep, peds)
    assert res.distancia_total_m >= 0
    total_kg = sum(p.peso_kg for p in res.ruta_pedidos)
    assert total_kg <= rep.capacidad_kg, \
        f"Sobrepeso: {total_kg} > {rep.capacidad_kg}"
    print(f"  PASS test_nn_respeta_capacidad  "
          f"({total_kg:.1f}/{rep.capacidad_kg} kg)")


def test_nn_pedidos_asignados_marcados():
    """Los pedidos en la ruta deben quedar con estado ASIGNADO."""
    g    = _grafo()
    nn   = NearestNeighborGreedy(g)
    rep  = _repartidor()
    peds = _pedidos()
    nn.construir_ruta(rep, peds)
    for p in peds:
        if p in rep.pedidos_asignados:
            assert p.estado == EstadoPedido.ASIGNADO, \
                f"{p.id_pedido} debería ser ASIGNADO"
    print("  PASS test_nn_pedidos_asignados_marcados")


def test_nn_con_coordinator_sin_duplicados():
    """
    Dos repartidores ejecutando NearestNeighbor con el mismo coordinator
    no deben obtener el mismo pedido.
    """
    g     = _grafo()
    nn    = NearestNeighborGreedy(g)
    coord = DeliveryCoordinator()
    peds  = _pedidos()
    rep1  = _repartidor("R01")
    rep2  = _repartidor("R02")

    res1 = nn.construir_ruta(rep1, peds, coordinator=coord)
    res2 = nn.construir_ruta(rep2, peds, coordinator=coord)

    ids1 = {p.id_pedido for p in res1.ruta_pedidos}
    ids2 = {p.id_pedido for p in res2.ruta_pedidos}
    assert len(ids1 & ids2) == 0, \
        f"Pedidos duplicados: {ids1 & ids2}"
    print(f"  PASS test_nn_con_coordinator_sin_duplicados  "
          f"(R01={ids1}, R02={ids2})")


def test_nn_sin_pedidos():
    """Con lista vacía de pedidos, la ruta debe estar vacía."""
    g   = _grafo()
    nn  = NearestNeighborGreedy(g)
    rep = _repartidor()
    res = nn.construir_ruta(rep, [])
    assert res.ruta_pedidos == []
    print("  PASS test_nn_sin_pedidos")


# ── AsignacionGreedy ──────────────────────────────────────────────────────────

def test_asignacion_greedy_disjunta():
    """AsignacionGreedy con coordinator debe producir asignaciones disjuntas."""
    g     = _grafo()
    ag    = AsignacionGreedy(g)
    coord = DeliveryCoordinator()
    peds  = _pedidos()
    reps  = [_repartidor("R01"), _repartidor("R02", TipoVehiculo.FURGONETA)]

    resultados = ag.asignar(peds, reps, coordinator=coord)
    todos_ids  = []
    for r in resultados:
        todos_ids.extend(p.id_pedido for p in r.ruta_pedidos)

    assert len(todos_ids) == len(set(todos_ids)), \
        f"Duplicados: {todos_ids}"
    print(f"  PASS test_asignacion_greedy_disjunta  "
          f"(total={len(todos_ids)} pedidos)")


def test_asignacion_to_dict():
    """to_dict() de ResultadoGreedy debe incluir las claves esperadas."""
    g    = _grafo()
    ag   = AsignacionGreedy(g)
    peds = _pedidos()
    reps = [_repartidor()]
    res  = ag.asignar(peds, reps)[0]
    d    = res.to_dict()
    for key in ("repartidor", "nombre", "ruta_pedidos",
                "distancia_total_m", "pedidos_omitidos"):
        assert key in d, f"Clave faltante: {key}"
    print(f"  PASS test_asignacion_to_dict  (keys={list(d.keys())})")


# ── Baseline aleatorio ────────────────────────────────────────────────────────

def test_distancia_ruta_aleatoria():
    """distancia_ruta_aleatoria() debe retornar un float > 0 con múltiples pedidos."""
    peds = _pedidos()
    d    = distancia_ruta_aleatoria(peds, -13.5170, -71.9785, n_muestras=100)
    assert d > 0.0, f"Distancia promedio esperada > 0, obtenida {d}"
    print(f"  PASS test_distancia_ruta_aleatoria  (d_prom={d:.0f} m)")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== tests/test_greedy.py ===")
    test_nn_ruta_no_vacia()
    test_nn_respeta_capacidad()
    test_nn_pedidos_asignados_marcados()
    test_nn_con_coordinator_sin_duplicados()
    test_nn_sin_pedidos()
    test_asignacion_greedy_disjunta()
    test_asignacion_to_dict()
    test_distancia_ruta_aleatoria()
    print("\nTodos los tests de greedy pasaron.\n")
