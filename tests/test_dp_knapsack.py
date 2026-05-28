"""
tests/test_dp_knapsack.py — Tests de algoritmos/dp/knapsack.py
===============================================================
Verifica:
  - Tabulación 2D (modo por defecto).
  - Memoización top-down (usar_memo=True).
  - Integración con DeliveryCoordinator (sin colisiones).
  - resolver_flota() produce asignaciones disjuntas.
  - ResultadoMochila.to_dict() retorna la estructura correcta.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.pedido          import Pedido
from modelos.repartidor      import Repartidor
from core.tipos              import TipoVehiculo, Prioridad, EstadoPedido
from algoritmos.dp.knapsack  import Mochila01, ResultadoMochila, resultado_mochila
from dispatcher.coordinator  import DeliveryCoordinator


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _pedidos_simples():
    """5 pedidos con pesos y valores conocidos para verificar el óptimo."""
    return [
        Pedido("P1", "Ana",    "Wanchaq",  -13.52, -71.97, peso_kg=2.0,  volumen_m3=0.01, valor=100.0, prioridad=Prioridad.MEDIA),
        Pedido("P2", "Bruno",  "Santiago", -13.53, -71.96, peso_kg=5.0,  volumen_m3=0.02, valor=200.0, prioridad=Prioridad.ALTA),
        Pedido("P3", "Carla",  "San Blas", -13.51, -71.98, peso_kg=3.0,  volumen_m3=0.01, valor=150.0, prioridad=Prioridad.BAJA),
        Pedido("P4", "Diego",  "Centro",   -13.52, -71.98, peso_kg=8.0,  volumen_m3=0.05, valor=300.0, prioridad=Prioridad.URGENTE),
        Pedido("P5", "Elena",  "Wanchaq",  -13.54, -71.95, peso_kg=1.0,  volumen_m3=0.01, valor=80.0,  prioridad=Prioridad.MEDIA),
    ]


def _repartidor_moto():
    return Repartidor("R01", "Jorge", TipoVehiculo.MOTO)    # 30 kg, 0.15 m³


def _repartidor_bici():
    return Repartidor("R04", "Carmen", TipoVehiculo.BICICLETA)  # 15 kg, 0.08 m³


# ── Tests de tabulación ───────────────────────────────────────────────────────

def test_tabular_capacidad_exacta():
    """
    Con cap=7 kg, la solución óptima es P2(5)+P5(1)=6kg valor=280
    o P1(2)+P3(3)=5kg valor=250 … el óptimo es P2+P5(valor=280).
    """
    pedidos = _pedidos_simples()
    m = Mochila01(factor_escala=10, usar_memo=False)
    res = m.resolver(pedidos, capacidad_kg=7.0, capacidad_m3=0.10)
    ids = {p.id_pedido for p in res.pedidos_elegidos}
    # Valor esperado: P2(200)+P5(80)=280 con 6 kg ≤ 7 kg
    assert res.valor_total >= 280.0, f"Valor subóptimo: {res.valor_total}"
    assert res.peso_total  <= 7.0,   f"Excede capacidad: {res.peso_total}"
    print(f"  PASS test_tabular_capacidad_exacta  (val={res.valor_total}, ids={ids})")


def test_tabular_capacidad_cero():
    """Con capacidad 0, no se elige ningún pedido."""
    pedidos = _pedidos_simples()
    m = Mochila01()
    res = m.resolver(pedidos, capacidad_kg=0.0, capacidad_m3=0.10)
    assert len(res.pedidos_elegidos) == 0
    print("  PASS test_tabular_capacidad_cero")


def test_tabular_lista_vacia():
    """Sin pedidos, el resultado debe ser vacío."""
    m = Mochila01()
    res = m.resolver([], capacidad_kg=30.0, capacidad_m3=0.15)
    assert len(res.pedidos_elegidos) == 0
    print("  PASS test_tabular_lista_vacia")


def test_tabular_marcado_asignado():
    """Los pedidos elegidos deben quedar en estado ASIGNADO."""
    pedidos = _pedidos_simples()
    m = Mochila01()
    res = m.resolver(pedidos, capacidad_kg=10.0, capacidad_m3=0.10)
    for p in res.pedidos_elegidos:
        assert p.estado == EstadoPedido.ASIGNADO, \
            f"{p.id_pedido} debería estar ASIGNADO, está {p.estado}"
    print(f"  PASS test_tabular_marcado_asignado  ({len(res.pedidos_elegidos)} pedidos)")


# ── Tests de memoización top-down ─────────────────────────────────────────────

def test_memo_mismo_resultado_que_tabular():
    """
    Memoización y tabulación deben producir el mismo valor óptimo.
    (El conjunto de ítems elegidos puede diferir si hay empates.)
    """
    pedidos_tab  = _pedidos_simples()
    pedidos_memo = _pedidos_simples()   # copias independientes

    tab  = Mochila01(usar_memo=False).resolver(pedidos_tab,  10.0, 0.10)
    memo = Mochila01(usar_memo=True ).resolver(pedidos_memo, 10.0, 0.10)

    assert abs(tab.valor_total - memo.valor_total) < 0.01, \
        f"Divergencia: tabular={tab.valor_total}, memo={memo.valor_total}"
    print(f"  PASS test_memo_mismo_resultado_que_tabular  "
          f"(tab={tab.valor_total}, memo={memo.valor_total})")


# ── Tests de coordinator (sin colisiones) ────────────────────────────────────

def test_coordinator_evita_doble_asignacion():
    """
    Dos mochilas ejecutadas sobre los mismos pedidos con el mismo
    coordinator no deben elegir el mismo pedido.
    """
    pedidos = _pedidos_simples()
    coord   = DeliveryCoordinator()

    m = Mochila01()
    res1 = m.resolver(pedidos, 10.0, 0.10, coordinator=coord, id_rep="R01")
    res2 = m.resolver(pedidos, 10.0, 0.10, coordinator=coord, id_rep="R02")

    ids1 = {p.id_pedido for p in res1.pedidos_elegidos}
    ids2 = {p.id_pedido for p in res2.pedidos_elegidos}
    interseccion = ids1 & ids2
    assert len(interseccion) == 0, \
        f"Pedidos duplicados entre R01 y R02: {interseccion}"
    print(f"  PASS test_coordinator_evita_doble_asignacion  "
          f"(R01={ids1}, R02={ids2})")


# ── Tests de resolver_flota ───────────────────────────────────────────────────

def test_resolver_flota_disjunto():
    """
    resolver_flota() debe producir asignaciones disjuntas entre repartidores.
    """
    pedidos      = _pedidos_simples()
    repartidores = [_repartidor_moto(), _repartidor_bici()]
    coord        = DeliveryCoordinator()

    m   = Mochila01()
    res = m.resolver_flota(pedidos, repartidores, coordinator=coord)

    todos_ids = []
    for r in res:
        todos_ids.extend(p.id_pedido for p in r.pedidos_elegidos)

    assert len(todos_ids) == len(set(todos_ids)), \
        f"Pedidos duplicados entre repartidores: {todos_ids}"
    print(f"  PASS test_resolver_flota_disjunto  "
          f"(total asignados={len(todos_ids)})")


# ── Tests de serialización ────────────────────────────────────────────────────

def test_resultado_to_dict_estructura():
    """to_dict() debe incluir todas las claves esperadas."""
    pedidos = _pedidos_simples()
    m  = Mochila01()
    res = m.resolver(pedidos, 10.0, 0.10)
    d  = res.to_dict()
    for key in ("pedidos_elegidos", "peso_total", "volumen_total",
                "valor_total", "capacidad_usada_pct", "num_pedidos"):
        assert key in d, f"Clave faltante en to_dict(): {key}"
    assert isinstance(d["pedidos_elegidos"], list)
    print(f"  PASS test_resultado_to_dict_estructura  (keys={list(d.keys())})")


# ── Función de conveniencia ───────────────────────────────────────────────────

def test_resultado_mochila_conveniente():
    """resultado_mochila() debe funcionar igual que Mochila01().resolver()."""
    pedidos = _pedidos_simples()
    res     = resultado_mochila(pedidos, 10.0, 0.10)
    assert isinstance(res, ResultadoMochila)
    assert res.peso_total <= 10.0
    print("  PASS test_resultado_mochila_conveniente")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== tests/test_dp_knapsack.py ===")
    test_tabular_capacidad_exacta()
    test_tabular_capacidad_cero()
    test_tabular_lista_vacia()
    test_tabular_marcado_asignado()
    test_memo_mismo_resultado_que_tabular()
    test_coordinator_evita_doble_asignacion()
    test_resolver_flota_disjunto()
    test_resultado_to_dict_estructura()
    test_resultado_mochila_conveniente()
    print("\nTodos los tests de dp/knapsack.py pasaron.\n")
