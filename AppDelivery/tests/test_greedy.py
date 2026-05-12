import sys, os, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.pedido   import Pedido, Prioridad, EstadoPedido
from modelos.grafo    import Grafo, Nodo, Arista
from modelos.repartidor import Repartidor, TipoVehiculo
from algoritmos.greedy import NearestNeighborGreedy, AsignacionGreedy


def _crear_grafo_basico():
    g = Grafo()
    g.agregar_nodo(Nodo("n1", "Nodo 1", -13.517, -71.9785, "Centro", True))
    g.agregar_nodo(Nodo("n2", "Nodo 2", -13.5145, -71.976, "San Blas", False))
    g.agregar_nodo(Nodo("n3", "Nodo 3", -13.528, -71.968, "Wanchaq", False))
    g.agregar_arista(Arista("n1", "n2", 380, 5))
    g.agregar_arista(Arista("n2", "n1", 380, 5))
    g.agregar_arista(Arista("n1", "n3", 1100, 14))
    g.agregar_arista(Arista("n3", "n1", 1100, 14))
    return g


def _crear_pedidos():
    return [
        Pedido("P001", "Cliente A", "San Blas", -13.5145, -71.976,
               2.5, 0.01, 45.0, Prioridad.ALTA),
        Pedido("P002", "Cliente B", "Wanchaq", -13.528, -71.968,
               5.0, 0.02, 80.0, Prioridad.URGENTE),
    ]


def test_nearest_neighbor_construir_ruta():
    g = _crear_grafo_basico()
    peds = _crear_pedidos()
    rep = Repartidor("R01", "Test", TipoVehiculo.MOTO, -13.517, -71.9785)

    nn = NearestNeighborGreedy(g)
    res = nn.construir_ruta(rep, peds)

    assert len(res.ruta_pedidos) > 0
    assert res.distancia_total_m > 0
    assert res.tiempo_total_min > 0


def test_nearest_neighbor_solo_urgentes():
    g = _crear_grafo_basico()
    peds = _crear_pedidos()
    rep = Repartidor("R01", "Test", TipoVehiculo.MOTO, -13.517, -71.9785)

    nn = NearestNeighborGreedy(g)
    res = nn.construir_ruta(rep, peds, solo_urgentes=True)

    for p in res.ruta_pedidos:
        assert p.prioridad in (Prioridad.URGENTE, Prioridad.ALTA)


def test_asignacion_greedy():
    g = _crear_grafo_basico()
    peds = _crear_pedidos()
    reps = [
        Repartidor("R01", "Test1", TipoVehiculo.MOTO, -13.517, -71.9785),
        Repartidor("R02", "Test2", TipoVehiculo.MOTO, -13.528, -71.968),
    ]

    ag = AsignacionGreedy(g)
    resultados = ag.asignar(peds, reps)

    assert len(resultados) == 2
    total_asignados = sum(len(r.ruta_pedidos) for r in resultados)
    assert total_asignados > 0


def test_resultado_to_dict():
    g = _crear_grafo_basico()
    peds = _crear_pedidos()
    rep = Repartidor("R01", "Test", TipoVehiculo.MOTO, -13.517, -71.9785)

    nn = NearestNeighborGreedy(g)
    res = nn.construir_ruta(rep, peds)
    d = res.to_dict()

    assert d["repartidor"] == "R01"
    assert "distancia_total_m" in d
    assert "ruta_pedidos" in d
