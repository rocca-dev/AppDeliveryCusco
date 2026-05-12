import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.pedido   import Pedido, Prioridad, EstadoPedido
from modelos.grafo    import Grafo, Nodo, Arista
from modelos.repartidor import Repartidor, TipoVehiculo
from algoritmos.programacion_dinamica import (
    Mochila01, resultado_mochila, resultado_mochila_flota,
    DijkstraMemo, PlanificadorRutasPD,
)


def _crear_pedidos():
    return [
        Pedido("P001", "A", "San Blas", -13.5145, -71.976,
               2.5, 0.01, 45.0, Prioridad.ALTA),
        Pedido("P002", "B", "Wanchaq", -13.528, -71.968,
               5.0, 0.02, 80.0, Prioridad.URGENTE),
        Pedido("P003", "C", "Santiago", -13.524, -71.992,
               8.0, 0.04, 120.0, Prioridad.MEDIA),
        Pedido("P004", "D", "San Seb", -13.532, -71.955,
               1.5, 0.005, 35.0, Prioridad.BAJA),
    ]


def _crear_grafo_con_ruta():
    g = Grafo()
    g.agregar_nodo(Nodo("n1", "N1", -13.517, -71.9785, "Centro", True))
    g.agregar_nodo(Nodo("n2", "N2", -13.5145, -71.976, "San Blas", False))
    g.agregar_arista(Arista("n1", "n2", 380, 5))
    g.agregar_arista(Arista("n2", "n1", 380, 5))
    return g


def test_mochila_01_basico():
    peds = _crear_pedidos()
    mochila = Mochila01()
    res = mochila.resolver(peds, capacidad_kg=10.0, capacidad_m3=0.05)
    assert len(res.pedidos_elegidos) > 0
    assert res.peso_total <= 10.0
    assert res.valor_total > 0


def test_mochila_01_capacidad_cero():
    peds = _crear_pedidos()
    res = resultado_mochila(peds, capacidad_kg=0, capacidad_m3=0)
    assert len(res.pedidos_elegidos) == 0


def test_mochila_01_bonus_urgente():
    peds = _crear_pedidos()
    res_sin = resultado_mochila(peds, 10.0, 0.05, bonus_urgente=1.0)
    res_con = resultado_mochila(peds, 10.0, 0.05, bonus_urgente=2.0)
    pedidos_sin = {p.id_pedido for p in res_sin.pedidos_elegidos}
    pedidos_con = {p.id_pedido for p in res_con.pedidos_elegidos}
    urgs = {p.id_pedido for p in peds if p.prioridad == Prioridad.URGENTE}
    if urgs:
        assert urgs.issubset(pedidos_con)


def test_mochila_flota():
    peds = _crear_pedidos()
    reps = [
        Repartidor("R01", "T1", TipoVehiculo.MOTO, -13.517, -71.9785),
        Repartidor("R02", "T2", TipoVehiculo.FURGONETA, -13.528, -71.968),
    ]
    resultados = resultado_mochila_flota(peds, reps, bonus_urgente=1.5)
    assert len(resultados) == 2
    total = sum(len(r.pedidos_elegidos) for r in resultados)
    assert total > 0


def test_dijkstra_ruta_mas_corta():
    g = _crear_grafo_con_ruta()
    dj = DijkstraMemo(g)
    res = dj.ruta_mas_corta("n1", "n2")
    assert res.camino == ["n1", "n2"]
    assert res.distancia_m == 380.0
    assert res.tiempo_min == 5.0


def test_dijkstra_mismo_nodo():
    g = _crear_grafo_con_ruta()
    dj = DijkstraMemo(g)
    res = dj.ruta_mas_corta("n1", "n1")
    assert res.camino == ["n1"]


def test_dijkstra_cache():
    g = _crear_grafo_con_ruta()
    dj = DijkstraMemo(g)
    r1 = dj.ruta_mas_corta("n1", "n2", usar_cache=True)
    r2 = dj.ruta_mas_corta("n1", "n2", usar_cache=True)
    assert r2.desde_cache is True
    assert dj.stats_cache()["hits"] == 1
