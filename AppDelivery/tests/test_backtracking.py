import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.grafo    import Grafo, Nodo, Arista
from modelos.pedido   import Pedido, Prioridad, EstadoPedido
from modelos.repartidor import Repartidor, TipoVehiculo
from algoritmos.backtracking import (
    BuscadorRutasBacktracking, BuscadorConPuntosObligatorios,
    buscar_rutas, RutaEncontrada, ResultadoBacktracking,
)


def _crear_grafo():
    g = Grafo()
    for n in [
        Nodo("A", "Nodo A", -13.517, -71.9785, "Centro", True),
        Nodo("B", "Nodo B", -13.5145, -71.976, "San Blas", False),
        Nodo("C", "Nodo C", -13.528, -71.968, "Wanchaq", False),
        Nodo("D", "Nodo D", -13.524, -71.992, "Santiago", False),
        Nodo("E", "Nodo E", -13.532, -71.955, "San Seb", False),
    ]:
        g.agregar_nodo(n)
    aristas = [
        ("A", "B", 380, 5), ("B", "A", 380, 5),
        ("A", "C", 1100, 14), ("C", "A", 1100, 14),
        ("B", "D", 1200, 15), ("D", "B", 1200, 15),
        ("C", "D", 550, 7), ("D", "C", 550, 7),
        ("C", "E", 950, 12), ("E", "C", 950, 12),
        ("A", "D", 1500, 18), ("D", "A", 1500, 18),
    ]
    for o, d, dist, t in aristas:
        g.agregar_arista(Arista(o, d, dist, t))
    return g


def test_backtracking_ruta_directa():
    g = _crear_grafo()
    res = buscar_rutas(g, "A", "B")
    assert len(res.todas_las_rutas) >= 1
    assert res.ruta_mas_corta is not None
    assert res.ruta_mas_corta.camino[0] == "A"
    assert res.ruta_mas_corta.camino[-1] == "B"


def test_backtracking_ruta_inexistente():
    g = _crear_grafo()
    g2 = Grafo()
    g2.agregar_nodo(Nodo("X", "X", 0, 0, "X"))
    g2.agregar_nodo(Nodo("Y", "Y", 0, 0, "Y"))
    try:
        res = buscar_rutas(g2, "X", "Y")
        assert len(res.todas_las_rutas) == 0
    except ValueError:
        pass


def test_backtracking_con_podas():
    g = _crear_grafo()
    res = buscar_rutas(g, "A", "D", max_paradas=4, max_rutas=5)
    assert len(res.todas_las_rutas) <= 5
    assert res.podas_aplicadas >= 0
    assert res.nodos_explorados > 0


def test_backtracking_nodo_inexistente():
    g = _crear_grafo()
    try:
        buscar_rutas(g, "A", "NO_EXISTE")
        assert False, "Debió lanzar ValueError"
    except ValueError:
        pass


def test_buscador_puntos_obligatorios():
    g = _crear_grafo()
    buscador = BuscadorConPuntosObligatorios(g)
    res = buscador.buscar("A", "E", puntos_obligatorios=["C"])
    assert res["viable"] is True
    assert "C" in res["ruta_completa"]


def test_ruta_encontrada_to_dict():
    r = RutaEncontrada(camino=["A", "B"], distancia_m=500,
                       tiempo_min=10, num_paradas=1)
    d = r.to_dict()
    assert d["camino"] == ["A", "B"]
    assert d["distancia_m"] == 500
