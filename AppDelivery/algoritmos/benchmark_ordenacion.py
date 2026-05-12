"""
Benchmark: compara el tiempo real de cada función de ordenación
y lo muestra en consola con tabla de resultados.

Uso:
    python3 -m algoritmos.benchmark_ordenacion
    (desde la raíz del proyecto)
"""

import sys, os, time, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.pedido import Pedido, Prioridad, EstadoPedido
from algoritmos.ordenacion import (
    ordenar_por_prioridad, ordenar_por_peso,
    ordenar_por_valor, ordenar_combinado,
    ordenar_por_distancia, ordenar_por_sector,
)
from algoritmos.busqueda import IndicePedidos, busqueda_binaria_id



# ── Generador de pedidos sintéticos ──────────────────────────
SECTORES   = ["San Blas", "Wanchaq", "Santiago",
              "Centro Histórico", "San Sebastián", "San Cristóbal"]
PRIORIDADES = list(Prioridad)


def generar_pedidos(n: int) -> list[Pedido]:
    pedidos = []
    for i in range(n):
        p = Pedido(
            id_pedido  = f"P{i:04d}",
            cliente    = f"Cliente_{i}",
            sector     = random.choice(SECTORES),
            latitud    = -13.51 + random.uniform(-0.03, 0.03),
            longitud   = -71.97 + random.uniform(-0.03, 0.03),
            peso_kg    = round(random.uniform(0.5, 25.0), 2),
            volumen_m3 = round(random.uniform(0.001, 0.1), 4),
            valor      = round(random.uniform(10.0, 300.0), 2),
            prioridad  = random.choice(PRIORIDADES),
        )
        pedidos.append(p)
    return pedidos


def medir(fn, *args) -> tuple[any, float]:
    """Ejecuta fn(*args) y retorna (resultado, tiempo_ms)."""
    t0     = time.perf_counter()
    result = fn(*args)
    t1     = time.perf_counter()
    return result, (t1 - t0) * 1000


# ── Benchmark principal ───────────────────────────────────────
def ejecutar_benchmark():
    print("=" * 62)
    print("  BENCHMARK — Ordenación y Búsqueda")
    print("=" * 62)

    for n in [100, 500, 1_000, 5_000]:
        pedidos = generar_pedidos(n)
        print(f"\n── n = {n} pedidos ──")

        # Ordenaciones
        funciones = [
            ("Prioridad (desc)",   lambda p: ordenar_por_prioridad(p)),
            ("Peso (asc)",         lambda p: ordenar_por_peso(p)),
            ("Valor (desc)",       lambda p: ordenar_por_valor(p)),
            ("Combinado",          lambda p: ordenar_combinado(p)),
            ("Sector",             lambda p: ordenar_por_sector(p)),
            ("Distancia Plaza",    lambda p: ordenar_por_distancia(
                                        p, -13.5170, -71.9785)),
        ]

        for nombre, fn in funciones:
            _, ms = medir(fn, pedidos[:])  # copia fresca
            print(f"  {nombre:<25} {ms:7.3f} ms")

        # Búsqueda binaria
        por_id    = sorted(pedidos, key=lambda p: p.id_pedido)
        id_target = por_id[n // 2].id_pedido
        _, ms_bin = medir(busqueda_binaria_id, por_id, id_target)
        print(f"  {'Búsqueda binaria':<25} {ms_bin:7.4f} ms  → target={id_target}")

        # Hash Map
        indice   = IndicePedidos(pedidos)
        _, ms_h  = medir(indice.buscar_por_id, id_target)
        print(f"  {'Hash Map (por ID)':<25} {ms_h:7.4f} ms  → O(1)")

    print("\n" + "=" * 62)
    print("  Todos los ordenamientos son O(n log n).")
    print("  Búsqueda binaria O(log n), Hash Map O(1) amortizado.")
    print("=" * 62)

ejecutar_benchmark()