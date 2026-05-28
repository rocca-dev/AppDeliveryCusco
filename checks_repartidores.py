"""Quick integration check for repartidores endpoints."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

r1 = client.get("/repartidores/")
assert r1.status_code == 200
data = r1.json()
assert len(data) >= 4

r2 = client.get("/repartidores/R01")
assert r2.status_code == 200
assert r2.json()["nombre"] == "Jorge Huallpa"

r3 = client.get("/repartidores/R01/ruta")
assert r3.status_code == 200
r3d = r3.json()

print(f"GET /repartidores/: OK — {len(data)} repartidores")
print(f"GET /repartidores/R01: OK — {r2.json()['nombre']}")
print(f"GET /repartidores/R01/ruta: OK — pedidos={r3d['pedidos_asignados']}, segmentos={len(r3d['segmentos'])}")
print("All checks PASS")
