"""
tests/test_repartidores_api.py — Tests para endpoints de /repartidores
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_listar_repartidores():
    resp = client.get("/repartidores/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    ids = [r["id_repartidor"] for r in data]
    assert "R01" in ids
    assert "R02" in ids
    assert "R03" in ids
    assert "R04" in ids


def test_repartidor_to_dict_structure():
    resp = client.get("/repartidores/")
    data = resp.json()
    r = data[0]
    for key in ("id_repartidor", "nombre", "vehiculo", "latitud_actual",
                 "longitud_actual", "capacidad_kg", "disponible",
                 "peso_cargado", "pedidos_asignados"):
        assert key in r, f"Falta clave '{key}' en repartidor.to_dict()"


def test_obtener_repartidor_por_id():
    resp = client.get("/repartidores/R01")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_repartidor"] == "R01"
    assert data["nombre"] == "Jorge Huallpa"
    assert data["vehiculo"] == "moto"


def test_obtener_repartidor_inexistente():
    resp = client.get("/repartidores/INVALIDO")
    assert resp.status_code == 404


def test_ruta_repartidor_sin_pedidos():
    # R04 (Carmen) debería empezar sin pedidos
    resp = client.get("/repartidores/R04/ruta")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_repartidor"] == "R04"
    assert data["segmentos"] == []


def test_ruta_repartidor_con_pedidos():
    # R01 empieza sin pedidos, así que asignamos uno manualmente
    from api.estado import app_state
    app_state.resetear()

    # Asignar un pedido a R01 manualmente
    pedido = app_state.pedidos[0]
    rep = app_state.repartidores[0]
    rep.asignar_pedido(pedido)

    resp = client.get(f"/repartidores/{rep.id_repartidor}/ruta")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_repartidor"] == rep.id_repartidor
    assert len(data["segmentos"]) >= 1
    assert "camino" in data["segmentos"][0]
    assert data["segmentos"][0]["id_pedido"] == pedido.id_pedido
    assert data["distancia_total_m"] > 0

    # Cleanup
    pedido.estado = "PENDIENTE"
    rep.pedidos_asignados.clear()


def test_ruta_repartidor_estructura():
    from api.estado import app_state
    app_state.resetear()

    pedido = app_state.pedidos[0]
    rep = app_state.repartidores[0]
    rep.asignar_pedido(pedido)

    resp = client.get(f"/repartidores/{rep.id_repartidor}/ruta")
    data = resp.json()
    for key in ("id_repartidor", "nombre", "vehiculo", "posicion",
                 "nodo_inicio", "segmentos", "distancia_total_m",
                 "tiempo_total_min", "pedidos_asignados"):
        assert key in data, f"Falta clave '{key}' en ruta response"

    # Cleanup
    pedido.estado = "PENDIENTE"
    rep.pedidos_asignados.clear()
