"""
api/main.py — Aplicación FastAPI principal
===========================================
Punto de entrada del servidor REST.
Sirve el frontend estático y los endpoints de la API.
"""

import os
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from api.routers import algoritmos, mapa, pedidos, repartidores
from api.estado import app_state
from core.geo import stats_cache_haversine

app = FastAPI(title="AppDelivery — Rutas Óptimas Cusco", version="2.0.0")

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Frontend estático ────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUI_DIR = os.path.join(BASE, "gui")

if os.path.isdir(GUI_DIR):
    app.mount("/gui", StaticFiles(directory=GUI_DIR, html=True), name="gui")


@app.get("/")
def index():
    """Sirve el frontend principal."""
    index_path = os.path.join(GUI_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        {"detail": "Frontend no encontrado. Ejecuta el servidor desde AppDelivery_v2/"},
        status_code=404,
    )


# ── Routers API ──────────────────────────────────────────────────────────────
app.include_router(algoritmos.router)
app.include_router(mapa.router)
app.include_router(pedidos.router)
app.include_router(repartidores.router)


# ── Health / Info ────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check del sistema con métricas en vivo."""
    return {
        "status"           : "ok",
        "pedidos_total"    : len(app_state.pedidos),
        "pedidos_pendientes": len(app_state.pedidos_pendientes()),
        "repartidores"     : len(app_state.repartidores),
        "nodos_grafo"      : len(app_state.grafo.nodos),
        "aristas_grafo"    : sum(len(v) for v in app_state.grafo.aristas.values()),
        "coordinator"      : app_state.coordinator.resumen(),
        "haversine_cache"  : stats_cache_haversine(),
        "dijkstra_cache"   : app_state.ruta_pd.stats_cache(),
    }


@app.get("/info")
def info():
    """Información de arquitectura del sistema."""
    return {
        "app"      : "Sistema de Rutas Óptimas — Cusco",
        "version"  : "2.0.0",
        "endpoints": [
            "/health",
            "/info",
            "/pedidos/",
            "/pedidos/ordenar/resultado",
            "/pedidos/buscar/resultado",
            "/mapa/grafo",
            "/mapa/nodos",
            "/mapa/aristas",
            "/mapa/sectores",
            "/mapa/bloquear",
            "/mapa/desbloquear",
            "/algoritmos/greedy/asignacion",
            "/algoritmos/divide-venceras",
            "/algoritmos/knapsack/flota",
            "/algoritmos/backtracking",
            "/algoritmos/backtracking/asignacion",
            "/algoritmos/ruta-optima/{origen}/{destino}",
            "/algoritmos/stats",
            "/algoritmos/resetear",
            "/repartidores/",
            "/repartidores/{id}",
            "/repartidores/{id}/ruta",
        ],
        "algoritmos": {
            "greedy"        : "Nearest Neighbor + Asignación Greedy",
            "divide_venceras": "Particionamiento espacial en cuadrantes",
            "knapsack"      : "Mochila 0/1 con PD (tabulación 2D)",
            "dijkstra"      : "Ruta más corta con memoización LRU",
            "backtracking"  : "Búsqueda exhaustiva de rutas con poda",
        },
    }
