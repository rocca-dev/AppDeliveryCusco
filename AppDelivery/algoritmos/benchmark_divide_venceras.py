"""
Benchmark Divide y Vencerás
===========================
Mide el tiempo de particionado y asignación de zonas en el mapa de Cusco.

Uso:
    python -m algoritmos.benchmark_divide_venceras
"""

import sys, os, time, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.cargador             import inicializar_sistema
from algoritmos.divide_venceras   import (ParticionadorCuadrantes,
                                          AsignadorZonas,
                                          ejecutar_divide_venceras)
from modelos.pedido               import EstadoPedido


def main():
    grafo, pedidos, repartidores = inicializar_sistema(aplicar_bloqueos=False)

    print("=" * 65)
    print("  BENCHMARK DIVIDE Y VENCERÁS")
    print("=" * 65)

    for umbral in [2, 3, 5]:
        for prof in [2, 3]:
            t0 = time.perf_counter()
            res = ejecutar_divide_venceras(
                pedidos, repartidores, grafo,
                umbral=umbral, max_prof=prof
            )
            ms = (time.perf_counter() - t0) * 1000
            hojas = len(res.arbol_particion.zonas_hoja())
            print(f"  umbral={umbral} prof={prof} → "
                  f"{hojas} zonas hoja, "
                  f"{sum(len(v) for v in res.asignaciones.values())} pedidos, "
                  f"{ms:.3f} ms")

    print(f"\n  Total repartidores: {len(repartidores)}")
    print(f"  Total pedidos     : {len(pedidos)}")
    print("=" * 65)


if __name__ == "__main__":
    main()
