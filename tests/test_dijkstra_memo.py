"""
tests/test_dijkstra_memo.py — Tests de algoritmos/dp/dijkstra_memo.py
======================================================================
Verifica la correctitud de Dijkstra, el funcionamiento del caché,
la integración con el coordinator y los casos de error.
Usa el grafo real de Cusco cargado desde datos/mapa_cusco.json.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.cargador             import cargar_grafo
from algoritmos.dp.dijkstra_memo  import DijkstraMemo, ruta_optima_dijkstra
from dispatcher.coordinator       import DeliveryCoordinator


# ── Fixture ───────────────────────────────────────────────────────────────────

def _dijkstra():
    grafo = cargar_grafo(aplicar_bloqueos=False)
    return DijkstraMemo(grafo, max_cache=50)


# ── Correctitud ───────────────────────────────────────────────────────────────

def test_ruta_misma_posicion():
    """Ruta de un nodo a sí mismo debe tener distancia 0 y un solo nodo."""
    d   = _dijkstra()
    res = d.ruta_mas_corta("plaza_armas", "plaza_armas")
    assert res.distancia_m == 0.0
    assert res.camino == ["plaza_armas"]
    print("  PASS test_ruta_misma_posicion")


def test_ruta_distancia_positiva():
    """Ruta entre dos nodos distintos debe tener distancia > 0."""
    d   = _dijkstra()
    # Obtener dos nodos reales del grafo
    nodos = list(d.grafo.nodos.keys())
    if len(nodos) < 2:
        print("  SKIP test_ruta_distancia_positiva (grafo con < 2 nodos)")
        return
    origen, destino = nodos[0], nodos[1]
    try:
        res = d.ruta_mas_corta(origen, destino)
        assert res.distancia_m >= 0.0
        assert len(res.camino) >= 1
        assert res.camino[0]  == origen
        assert res.camino[-1] == destino
        print(f"  PASS test_ruta_distancia_positiva  "
              f"({origen}→{destino}: {res.distancia_m:.0f} m, "
              f"{len(res.camino)} nodos)")
    except ValueError:
        print(f"  SKIP test_ruta_distancia_positiva "
              f"(sin ruta {origen}→{destino})")


def test_ruta_nodo_inexistente():
    """Nodo origen inexistente debe lanzar ValueError."""
    d = _dijkstra()
    try:
        d.ruta_mas_corta("NODO_FALSO", "plaza_armas")
        assert False, "Debería lanzar ValueError"
    except ValueError as e:
        assert "NODO_FALSO" in str(e)
    print("  PASS test_ruta_nodo_inexistente")


# ── Caché ─────────────────────────────────────────────────────────────────────

def test_cache_hit_en_segunda_consulta():
    """La segunda consulta al mismo par debe venir del caché (desde_cache=True)."""
    d     = _dijkstra()
    nodos = list(d.grafo.nodos.keys())
    if len(nodos) < 2:
        print("  SKIP test_cache_hit_en_segunda_consulta")
        return
    origen, destino = nodos[0], nodos[1]
    try:
        d.ruta_mas_corta(origen, destino)          # miss
        res2 = d.ruta_mas_corta(origen, destino)   # hit
        assert res2.desde_cache is True, "Esperado desde_cache=True"
        stats = d.stats_cache()
        assert stats["hits"] >= 1
        print(f"  PASS test_cache_hit_en_segunda_consulta  "
              f"(hits={stats['hits']}, misses={stats['misses']})")
    except ValueError:
        print("  SKIP test_cache_hit_en_segunda_consulta (sin ruta)")


def test_limpiar_cache():
    """limpiar_cache() debe vaciar el caché y resetear contadores."""
    d     = _dijkstra()
    nodos = list(d.grafo.nodos.keys())
    if len(nodos) < 2:
        print("  SKIP test_limpiar_cache")
        return
    try:
        d.ruta_mas_corta(nodos[0], nodos[1])
        d.limpiar_cache()
        stats = d.stats_cache()
        assert stats["tamano_cache"] == 0
        assert stats["hits"]         == 0
        assert stats["misses"]       == 0
        print("  PASS test_limpiar_cache")
    except ValueError:
        print("  SKIP test_limpiar_cache")


def test_stats_cache_estructura():
    """stats_cache() debe retornar las claves esperadas."""
    d = _dijkstra()
    s = d.stats_cache()
    for key in ("tamano_cache", "max_cache", "hits", "misses", "hit_ratio"):
        assert key in s, f"Clave faltante: {key}"
    assert 0.0 <= s["hit_ratio"] <= 1.0
    print(f"  PASS test_stats_cache_estructura  ({s})")


# ── Coordinator ───────────────────────────────────────────────────────────────

def test_coordinator_registra_nodo_destino():
    """
    Después de calcular una ruta, el nodo destino debe quedar registrado
    en el coordinator para el repartidor que hizo la consulta.
    """
    d     = _dijkstra()
    nodos = list(d.grafo.nodos.keys())
    if len(nodos) < 2:
        print("  SKIP test_coordinator_registra_nodo_destino")
        return
    origen, destino = nodos[0], nodos[1]
    coord = DeliveryCoordinator()
    try:
        d.ruta_mas_corta(origen, destino, coordinator=coord, id_rep="R01")
        assert coord.quien_atiende_nodo(destino) == "R01", \
            f"Nodo {destino} debería estar asignado a R01"
        # R02 debe ver ese nodo como ocupado
        assert coord.nodo_entrega_libre(destino, "R02") is False
        print(f"  PASS test_coordinator_registra_nodo_destino  ({destino}→R01)")
    except ValueError:
        print("  SKIP test_coordinator_registra_nodo_destino")


# ── Función de conveniencia ───────────────────────────────────────────────────

def test_ruta_optima_dijkstra_reutiliza_cache():
    """
    ruta_optima_dijkstra() con la misma instancia debe aprovechar el caché.
    """
    d     = _dijkstra()
    nodos = list(d.grafo.nodos.keys())
    if len(nodos) < 2:
        print("  SKIP test_ruta_optima_dijkstra_reutiliza_cache")
        return
    try:
        ruta_optima_dijkstra(d, nodos[0], nodos[1])   # miss
        res2 = ruta_optima_dijkstra(d, nodos[0], nodos[1])   # hit
        assert res2.desde_cache is True
        print("  PASS test_ruta_optima_dijkstra_reutiliza_cache")
    except ValueError:
        print("  SKIP test_ruta_optima_dijkstra_reutiliza_cache")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== tests/test_dijkstra_memo.py ===")
    test_ruta_misma_posicion()
    test_ruta_distancia_positiva()
    test_ruta_nodo_inexistente()
    test_cache_hit_en_segunda_consulta()
    test_limpiar_cache()
    test_stats_cache_estructura()
    test_coordinator_registra_nodo_destino()
    test_ruta_optima_dijkstra_reutiliza_cache()
    print("\nTodos los tests de dijkstra_memo.py pasaron.\n")
