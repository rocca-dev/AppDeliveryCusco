"""
Benchmark Backtracking
======================
Mide el rendimiento del algoritmo de búsqueda exhaustiva con podas
en diferentes pares de nodos del mapa de Cusco.

Uso:
    python -m algoritmos.benchmark_backtracking
"""

import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.cargador             import inicializar_sistema
from algoritmos.backtracking      import (BuscadorRutasBacktracking,
                                          buscar_rutas)


def main():
    grafo, pedidos, repartidores = inicializar_sistema(aplicar_bloqueos=True)

    print("=" * 65)
    print("  BENCHMARK BACKTRACKING — Búsqueda Exhaustiva con Podas")
    print("=" * 65)

    casos = [
        ("plaza_armas",    "san_blas"),
        ("plaza_armas",    "wanchaq_centro"),
        ("san_blas",       "santiago"),
        ("plaza_armas",    "sacsayhuaman"),
        ("plaza_armas",    "san_sebastian"),
        ("wanchaq_centro", "santiago"),
    ]

    buscador = BuscadorRutasBacktracking(grafo)

    for orig, dest in casos:
        t0 = time.perf_counter()
        res = buscador.buscar(orig, dest, max_paradas=8, max_rutas=30)
        ms = (time.perf_counter() - t0) * 1000
        mas_corta = (f"{res.ruta_mas_corta.distancia_m:.0f}m"
                     if res.ruta_mas_corta else "SIN RUTA")
        print(f"\n  {orig} → {dest}")
        print(f"    Rutas: {len(res.todas_las_rutas):>3}  "
              f"Explorados: {res.nodos_explorados:>4}  "
              f"Podas: {res.podas_aplicadas:>3}  "
              f"Mejor: {mas_corta:>12}  "
              f"Tiempo: {ms:.4f}ms")

    print("\n" + "=" * 65)
    print("  Backtracking con podas es viable para el mapa de Cusco")
    print("  (V=20 nodos, factor de ramificación b≈3, profundidad d≤8)")
    print("=" * 65)


if __name__ == "__main__":
    main()
