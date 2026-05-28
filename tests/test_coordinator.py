"""
tests/test_coordinator.py — Tests de dispatcher/coordinator.py
===============================================================
Verifica el comportamiento thread-safe del DeliveryCoordinator:
reservas atómicas, idempotencia, detección de conflictos de nodos
y funcionamiento bajo concurrencia real (threads).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import threading
from dispatcher.coordinator import DeliveryCoordinator


# ── Reservas de pedidos ───────────────────────────────────────────────────────

def test_reservar_pedido_libre():
    """Un pedido libre puede ser reservado → True."""
    c = DeliveryCoordinator()
    assert c.reservar_pedido("P001", "R01") is True
    print("  PASS test_reservar_pedido_libre")


def test_reservar_pedido_ya_tomado():
    """Un pedido ya reservado por otro repartidor → False."""
    c = DeliveryCoordinator()
    c.reservar_pedido("P001", "R01")
    assert c.reservar_pedido("P001", "R02") is False
    print("  PASS test_reservar_pedido_ya_tomado")


def test_reservar_mismo_repartidor_idempotente():
    """El mismo repartidor puede reservar su propio pedido varias veces → True."""
    c = DeliveryCoordinator()
    c.reservar_pedido("P001", "R01")
    assert c.reservar_pedido("P001", "R01") is True
    print("  PASS test_reservar_mismo_repartidor_idempotente")


def test_liberar_pedido():
    """Liberar un pedido lo deja disponible para otro repartidor."""
    c = DeliveryCoordinator()
    c.reservar_pedido("P001", "R01")
    c.liberar_pedido("P001")
    assert c.pedido_esta_libre("P001") is True
    # Ahora R02 puede tomarlo
    assert c.reservar_pedido("P001", "R02") is True
    print("  PASS test_liberar_pedido")


def test_liberar_pedido_no_existente():
    """Liberar un pedido que no existe no lanza excepción."""
    c = DeliveryCoordinator()
    c.liberar_pedido("P999")   # no debe explotar
    print("  PASS test_liberar_pedido_no_existente")


def test_quien_tiene_pedido():
    """quien_tiene_pedido() retorna el id correcto o None."""
    c = DeliveryCoordinator()
    assert c.quien_tiene_pedido("P001") is None
    c.reservar_pedido("P001", "R01")
    assert c.quien_tiene_pedido("P001") == "R01"
    print("  PASS test_quien_tiene_pedido")


# ── Nodos de entrega ──────────────────────────────────────────────────────────

def test_nodo_libre_inicialmente():
    """Un nodo recién creado debe estar libre."""
    c = DeliveryCoordinator()
    assert c.nodo_entrega_libre("plaza_armas", "R01") is True
    print("  PASS test_nodo_libre_inicialmente")


def test_nodo_marcado_por_otro():
    """Si R01 marcó el nodo, R02 debe verlo como ocupado."""
    c = DeliveryCoordinator()
    c.marcar_nodo_en_ruta("hospital_regional", "R01")
    assert c.nodo_entrega_libre("hospital_regional", "R02") is False
    print("  PASS test_nodo_marcado_por_otro")


def test_nodo_marcado_mismo_repartidor():
    """El mismo repartidor ve su propio nodo como libre (idempotente)."""
    c = DeliveryCoordinator()
    c.marcar_nodo_en_ruta("hospital_regional", "R01")
    assert c.nodo_entrega_libre("hospital_regional", "R01") is True
    print("  PASS test_nodo_marcado_mismo_repartidor")


def test_quien_atiende_nodo():
    """quien_atiende_nodo() retorna el repartidor correcto."""
    c = DeliveryCoordinator()
    assert c.quien_atiende_nodo("san_blas") is None
    c.marcar_nodo_en_ruta("san_blas", "R04")
    assert c.quien_atiende_nodo("san_blas") == "R04"
    print("  PASS test_quien_atiende_nodo")


# ── Resetear ──────────────────────────────────────────────────────────────────

def test_resetear_limpia_todo():
    """resetear() elimina todas las reservas y nodos marcados."""
    c = DeliveryCoordinator()
    c.reservar_pedido("P001", "R01")
    c.reservar_pedido("P002", "R02")
    c.marcar_nodo_en_ruta("plaza_armas", "R01")
    c.resetear()
    assert c.pedido_esta_libre("P001") is True
    assert c.pedido_esta_libre("P002") is True
    assert c.nodo_entrega_libre("plaza_armas", "R99") is True
    print("  PASS test_resetear_limpia_todo")


# ── Diagnóstico ───────────────────────────────────────────────────────────────

def test_resumen_estructura():
    """resumen() debe incluir las claves esperadas."""
    c = DeliveryCoordinator()
    c.reservar_pedido("P001", "R01")
    c.marcar_nodo_en_ruta("san_blas", "R04")
    r = c.resumen()
    for key in ("pedidos_reservados", "nodos_en_ruta",
                "detalle_pedidos", "detalle_nodos"):
        assert key in r, f"Clave faltante: {key}"
    assert r["pedidos_reservados"] == 1
    assert r["nodos_en_ruta"]      == 1
    print(f"  PASS test_resumen_estructura  (resumen={r})")


# ── Concurrencia real ─────────────────────────────────────────────────────────

def test_concurrencia_sin_duplicados():
    """
    100 threads intentan reservar el mismo pedido simultáneamente.
    Solo UNO debe conseguirlo.
    """
    c       = DeliveryCoordinator()
    exitos  = []
    lock    = threading.Lock()

    def intentar_reservar(id_rep: str):
        ok = c.reservar_pedido("P_UNICO", id_rep)
        if ok:
            with lock:
                exitos.append(id_rep)

    threads = [threading.Thread(target=intentar_reservar, args=(f"R{i:03d}",))
               for i in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(exitos) == 1, \
        f"Se esperaba 1 ganador, obtuvimos {len(exitos)}: {exitos}"
    print(f"  PASS test_concurrencia_sin_duplicados  "
          f"(ganador={exitos[0]}, competidores=100)")


def test_concurrencia_pedidos_distintos():
    """
    50 threads reservan pedidos distintos simultáneamente.
    Todos deben conseguirlo sin interferencias.
    """
    c      = DeliveryCoordinator()
    exitos = []
    lock   = threading.Lock()

    def reservar(i: int):
        ok = c.reservar_pedido(f"P{i:03d}", f"R{i:03d}")
        if ok:
            with lock:
                exitos.append(i)

    threads = [threading.Thread(target=reservar, args=(i,)) for i in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(exitos) == 50, \
        f"Se esperaban 50 éxitos, obtuvimos {len(exitos)}"
    print(f"  PASS test_concurrencia_pedidos_distintos  (50/50 reservas)")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== tests/test_coordinator.py ===")
    test_reservar_pedido_libre()
    test_reservar_pedido_ya_tomado()
    test_reservar_mismo_repartidor_idempotente()
    test_liberar_pedido()
    test_liberar_pedido_no_existente()
    test_quien_tiene_pedido()
    test_nodo_libre_inicialmente()
    test_nodo_marcado_por_otro()
    test_nodo_marcado_mismo_repartidor()
    test_quien_atiende_nodo()
    test_resetear_limpia_todo()
    test_resumen_estructura()
    test_concurrencia_sin_duplicados()
    test_concurrencia_pedidos_distintos()
    print("\nTodos los tests de coordinator.py pasaron.\n")
