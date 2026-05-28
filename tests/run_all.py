"""
tests/run_all.py — Ejecutor Completo de Tests
==============================================
Corre todos los tests del proyecto en secuencia e imprime un resumen.

Uso:
    cd AppDelivery_v2
    python tests/run_all.py
"""

import sys, os, time, traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar todos los módulos de test
import tests.test_core_geo      as t_geo
import tests.test_coordinator   as t_coord
import tests.test_dp_knapsack   as t_ks
import tests.test_dijkstra_memo as t_dijk
import tests.test_greedy        as t_greedy

from core.geo import haversine


SUITES = [
    ("core/geo.py", [
        t_geo.test_haversine_misma_posicion,
        t_geo.test_haversine_plaza_a_san_blas,
        t_geo.test_haversine_simetria,
        t_geo.test_haversine_cache_hit,
        t_geo.test_distancia_puntos_delegacion,
        t_geo.test_nodo_mas_cercano_idx_basico,
        t_geo.test_nodo_mas_cercano_idx_vacio,
        t_geo.test_stats_cache_haversine_estructura,
    ]),
    ("dispatcher/coordinator.py", [
        t_coord.test_reservar_pedido_libre,
        t_coord.test_reservar_pedido_ya_tomado,
        t_coord.test_reservar_mismo_repartidor_idempotente,
        t_coord.test_liberar_pedido,
        t_coord.test_liberar_pedido_no_existente,
        t_coord.test_quien_tiene_pedido,
        t_coord.test_nodo_libre_inicialmente,
        t_coord.test_nodo_marcado_por_otro,
        t_coord.test_nodo_marcado_mismo_repartidor,
        t_coord.test_quien_atiende_nodo,
        t_coord.test_resetear_limpia_todo,
        t_coord.test_resumen_estructura,
        t_coord.test_concurrencia_sin_duplicados,
        t_coord.test_concurrencia_pedidos_distintos,
    ]),
    ("algoritmos/dp/knapsack.py", [
        t_ks.test_tabular_capacidad_exacta,
        t_ks.test_tabular_capacidad_cero,
        t_ks.test_tabular_lista_vacia,
        t_ks.test_tabular_marcado_asignado,
        t_ks.test_memo_mismo_resultado_que_tabular,
        t_ks.test_coordinator_evita_doble_asignacion,
        t_ks.test_resolver_flota_disjunto,
        t_ks.test_resultado_to_dict_estructura,
        t_ks.test_resultado_mochila_conveniente,
    ]),
    ("algoritmos/dp/dijkstra_memo.py", [
        t_dijk.test_ruta_misma_posicion,
        t_dijk.test_ruta_distancia_positiva,
        t_dijk.test_ruta_nodo_inexistente,
        t_dijk.test_cache_hit_en_segunda_consulta,
        t_dijk.test_limpiar_cache,
        t_dijk.test_stats_cache_estructura,
        t_dijk.test_coordinator_registra_nodo_destino,
        t_dijk.test_ruta_optima_dijkstra_reutiliza_cache,
    ]),
    ("algoritmos/greedy/", [
        t_greedy.test_nn_ruta_no_vacia,
        t_greedy.test_nn_respeta_capacidad,
        t_greedy.test_nn_pedidos_asignados_marcados,
        t_greedy.test_nn_con_coordinator_sin_duplicados,
        t_greedy.test_nn_sin_pedidos,
        t_greedy.test_asignacion_greedy_disjunta,
        t_greedy.test_asignacion_to_dict,
        t_greedy.test_distancia_ruta_aleatoria,
    ]),
]


def run_all():
    total_ok   = 0
    total_fail = 0
    t_inicio   = time.perf_counter()

    print("\n" + "═" * 60)
    print("  AppDelivery v2 — Suite de Tests")
    print("═" * 60)

    for suite_nombre, tests in SUITES:
        print(f"\n── {suite_nombre}")
        haversine.cache_clear()   # caché limpio por suite
        for fn in tests:
            try:
                fn()
                total_ok += 1
            except Exception as e:
                total_fail += 1
                print(f"  FAIL {fn.__name__}")
                traceback.print_exc(limit=3)

    elapsed = time.perf_counter() - t_inicio
    print("\n" + "═" * 60)
    print(f"  Resultado: {total_ok} PASS  |  {total_fail} FAIL")
    print(f"  Tiempo   : {elapsed:.3f} s")
    print("═" * 60 + "\n")

    return total_fail == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
