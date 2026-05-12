"""
Aplicación FastAPI — Sistema de Gestión de Rutas Óptimas en Cusco
=================================================================
Arranque:
    uvicorn api.main:app --reload --port 8000

Interfaz web:
    http://localhost:8000
Documentación API:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles    import StaticFiles
from fastapi.responses      import FileResponse
from contextlib import asynccontextmanager
import os

from api.estado             import app_state
from api.routers.pedidos    import router as router_pedidos
from api.routers.algoritmos import router as router_algoritmos
from api.routers.mapa       import router as router_mapa

GUI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gui")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando Sistema de Rutas Cusco...")
    app_state.inicializar(aplicar_bloqueos=True)
    print("API lista")
    print("   Interfaz web : http://localhost:8000")
    print("   Swagger docs : http://localhost:8000/docs")
    yield
    print("Cerrando API...")


app = FastAPI(
    title       = "Sistema de Gestión de Rutas Óptimas — Cusco",
    description = "API REST para el sistema de rutas con 5 algoritmos: "
                  "Merge Sort, Greedy, D&V, PD Knapsack, Backtracking.",
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.include_router(router_pedidos)
app.include_router(router_algoritmos)
app.include_router(router_mapa)

if os.path.isdir(GUI_DIR):
    app.mount("/static", StaticFiles(directory=GUI_DIR), name="static")


@app.get("/", include_in_schema=False)
def interfaz():
    return FileResponse(os.path.join(GUI_DIR, "index.html"))


@app.get("/health", tags=["Info"])
def health():
    stats = app_state.ruta_pd.stats_cache() if app_state.ruta_pd else {}
    return {
        "estado"            : "ok",
        "pedidos_total"     : len(app_state.pedidos),
        "pedidos_pendientes": len(app_state.pedidos_pendientes()),
        "repartidores"      : len(app_state.repartidores),
        "nodos_grafo"       : len(app_state.grafo.nodos),
        "cache_rutas"       : stats,
    }


@app.get("/info", tags=["Info"])
def info():
    return {
        "sistema"   : "Rutas Óptimas Cusco — UNSAAC Programación III",
        "version"   : "1.0.0",
        "algoritmos": {
            "ordenacion"  : "Merge Sort O(n log n) + Búsqueda Binaria O(log n) + Hash Map O(1)",
            "greedy"      : "Nearest Neighbor O(n²) + Asignación O(p×r)",
            "divide"      : "Particionado cuaternario O(n log n)",
            "dinamica"    : "Knapsack 0/1 O(n×W) + Dijkstra+memo O((V+E)logV)",
            "backtracking": "DFS con poda O(b^d)",
        },
    }
