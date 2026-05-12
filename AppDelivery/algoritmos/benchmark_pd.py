"""
Benchmark Programación Dinámica
===============================
Mide el rendimiento de Knapsack 0/1 y Dijkstra con memoización.

Uso:
    python -m algoritmos.benchmark_pd
"""

import sys, os, time, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.cargador             import inicializar_sistema
from algoritmos.programacion_dinamica import (Mochila01, DijkstraMemo,
                                              resultado_mochila_flota)
from modelos.pedido               import EstadoPedido


def main():
    grafo, pedidos, repartidores = inicializar_sistema(aplicar_bloqueos=True)

    print("=" * 65)
    print("  BENCHMARK PROGRAMACIÓN DINÁMICA")
    print("=" * 65)

    print("\n── Knapsack 0/1 (por repartidor) ──")
    mochila = Mochila01()
    for rep in repartidores:
        t0 = time.perf_counter()
        res = mochila.resolver(
            pedidos, rep.capacidad_kg, rep.capacidad_m3, bonus_urgente=1.5
        )
        ms = (time.perf_counter() - t0) * 1000
        print(f"  {rep.id_repartidor} ({rep.nombre}) "
              f"→ {len(res.pedidos_elegidos)} pedidos, "
              f"S/.{res.valor_total:.2f} valor, "
              f"{res.capacidad_usada_pct:.0f}% capacidad, "
              f"{ms:.3f} ms")

    print("\n── Knapsack Flota (todos los repartidores) ──")
    peds2 = copy.deepcopy(pedidos)
    for p in peds2:
        p.estado = EstadoPedido.PENDIENTE
    t0 = time.perf_counter()
    resultados = resultado_mochila_flota(peds2, repartidores, bonus_urgente=1.5)
    ms = (time.perf_counter() - t0) * 1000
    total_valor = sum(r.valor_total for r in resultados)
    total_peds  = sum(len(r.pedidos_elegidos) for r in resultados)
    print(f"  Flota: {total_peds} pedidos, S/.{total_valor:.2f} valor, {ms:.3f} ms")

    print("\n── Dijkstra con memoización ──")
    dj = DijkstraMemo(grafo)
    pares = [
        ("plaza_armas", "san_blas"),
        ("san_blas", "wanchaq_centro"),
        ("plaza_armas", "santiago"),
        ("plaza_armas", "san_sebastian"),
        ("santiago", "huancaro"),
        ("plaza_armas", "wanchaq_centro"),
        ("plaza_armas", "santiago"),
    ]
    for i, (orig, dest) in enumerate(pares):
        t0 = time.perf_counter()
        res = dj.ruta_mas_corta(orig, dest, usar_cache=True)
        ms = (time.perf_counter() - t0) * 1000
        cache_info = "(CACHE)" if res.desde_cache else "(nuevo)"
        print(f"  {i+1}. {orig} → {dest}: "
              f"{res.distancia_m:.0f}m, "
              f"{res.tiempo_min:.1f}min, "
              f"{ms:.4f}ms {cache_info}")

    print(f"\n  Cache stats: {dj.stats_cache()}")
    print("=" * 65)


if __name__ == "__main__":
    main()
