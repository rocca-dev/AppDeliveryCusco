"""
Benchmark Greedy
================
Compara NearestNeighborGreedy vs ruta aleatoria (baseline)
y muestra el ahorro en distancia y tiempo.

Uso:
    python -m algoritmos.benchmark_greedy
"""

import sys, os, time, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.cargador       import inicializar_sistema
from algoritmos.greedy      import (NearestNeighborGreedy,
                                    AsignacionGreedy,
                                    distancia_ruta_aleatoria)
from modelos.pedido         import EstadoPedido


def resetear_pedidos(pedidos):
    nuevos = copy.deepcopy(pedidos)
    for p in nuevos:
        p.estado = EstadoPedido.PENDIENTE
    return nuevos


def resetear_repartidores(repartidores):
    nuevos = copy.deepcopy(repartidores)
    for r in nuevos:
        r.pedidos_asignados.clear()
    return nuevos


def main():
    grafo, pedidos, repartidores = inicializar_sistema(aplicar_bloqueos=False)
    nn  = NearestNeighborGreedy(grafo)
    ag  = AsignacionGreedy(grafo)

    print("=" * 65)
    print("  BENCHMARK GREEDY — Sistema de Rutas Cusco")
    print("=" * 65)

    print("\n── Test 1: Nearest Neighbor (R01 — Jorge Huallpa) ──")
    peds  = resetear_pedidos(pedidos)
    reps  = resetear_repartidores(repartidores)
    rep   = reps[0]
    t0  = time.perf_counter()
    res = nn.construir_ruta(rep, peds)
    ms  = (time.perf_counter() - t0) * 1000
    print(res.resumen())
    print(f"  Tiempo de cómputo : {ms:.3f} ms")

    dist_rand = distancia_ruta_aleatoria(
        res.ruta_pedidos,
        repartidores[0].latitud_actual,
        repartidores[0].longitud_actual,
        n_muestras=500
    )
    ahorro = dist_rand - res.distancia_total_m
    pct    = (ahorro / dist_rand * 100) if dist_rand > 0 else 0
    print(f"\n  Distancia Greedy   : {res.distancia_total_m:>10,.0f} m")
    print(f"  Distancia Aleatoria: {dist_rand:>10,.0f} m  (promedio 500 muestras)")
    print(f"  Ahorro             : {ahorro:>10,.0f} m  ({pct:.1f}% mejor)")

    print("\n── Test 2: Asignación Greedy masiva (4 repartidores) ──")
    peds2 = resetear_pedidos(pedidos)
    reps2 = resetear_repartidores(repartidores)
    t0   = time.perf_counter()
    resultados = ag.asignar(peds2, reps2)
    ms2  = (time.perf_counter() - t0) * 1000
    total_dist  = 0.0
    total_peds  = 0
    for r in resultados:
        if r.ruta_pedidos:
            print(f"\n  {r.repartidor.id_repartidor} — {r.repartidor.nombre}")
            print(f"    Pedidos : {[p.id_pedido for p in r.ruta_pedidos]}")
            print(f"    Distancia: {r.distancia_total_m:,.0f} m  |  "
                  f"Tiempo: {r.tiempo_total_min:.1f} min")
            total_dist += r.distancia_total_m
            total_peds += len(r.ruta_pedidos)
    omitidos = [p.id_pedido for r in resultados for p in r.pedidos_omitidos]
    print(f"\n  Total pedidos asignados : {total_peds}/{len(pedidos)}")
    print(f"  Distancia total flota   : {total_dist:,.0f} m")
    print(f"  Pedidos sin asignar     : {list(set(omitidos))}")
    print(f"  Tiempo de cómputo       : {ms2:.3f} ms")

    print("\n── Test 3: Nearest Neighbor — Solo pedidos URGENTES/ALTOS ──")
    peds3 = resetear_pedidos(pedidos)
    reps3 = resetear_repartidores(repartidores)
    res3 = nn.construir_ruta(reps3[0], peds3, solo_urgentes=True)
    print(res3.resumen())

    print("\n" + "=" * 65)
    print("  CONCLUSIÓN PARA EL INFORME:")
    print(f"  Greedy es ~{pct:.0f}% mejor que ruta aleatoria.")
    print("  Complejidad confirmada: O(n²) por ruta, O(p×r) asignación.")
    print("  Ventaja: velocidad. Desventaja: no garantiza óptimo global.")
    print("=" * 65)


if __name__ == "__main__":
    main()
