"""
api/routers/algoritmos.py — Router: /algoritmos
================================================
Endpoints que ejecutan los algoritmos de optimización sobre los datos
del sistema.

CAMBIOS respecto a la versión original
───────────────────────────────────────
  1. Todos los algoritmos reciben app_state.coordinator para garantizar
     asignaciones disjuntas y sin colisiones de nodos de entrega.

  2. El endpoint /ruta-optima/{origen}/{destino} ya no crea una nueva
     instancia de DijkstraMemo — reutiliza app_state.ruta_pd
     (instancia compartida con caché persistente).

  3. Los imports apuntan a los subpaquetes reorganizados (dp/, greedy/).

  4. Nuevo endpoint GET /algoritmos/stats que expone las métricas
     de rendimiento de los cachés.
"""

from fastapi import APIRouter, HTTPException

from api.estado  import app_state
from api.schemas import (GreedyRequest, GreedyResponse,
                         DVRequest, DVResponse,
                         KnapsackRequest, KnapsackResponse,
                         BacktrackingRequest, BacktrackingResponse,
                         AsignacionRequest, AsignacionResponse,
                         RutaOptimaResponse)

from algoritmos.greedy        import AsignacionGreedy
from algoritmos.divide_venceras import ejecutar_divide_venceras
from algoritmos.dp            import (resultado_mochila_flota,
                                       ruta_optima_dijkstra)
from algoritmos.backtracking  import (BuscadorRutasBacktracking,
                                       asignar_pedidos)
from core.tipos               import EstadoPedido, Prioridad

router = APIRouter(prefix="/algoritmos", tags=["Algoritmos"])


# ── Greedy ────────────────────────────────────────────────────────────────────

@router.post("/greedy/asignacion", response_model=GreedyResponse)
def greedy_asignacion(req: GreedyRequest):
    """
    Asigna pedidos a la flota usando el algoritmo Nearest Neighbor Greedy.

    Si resetear_estado=True, limpia asignaciones previas (incluyendo
    el coordinator y el caché de rutas) antes de ejecutar.
    """
    if req.resetear_estado:
        app_state.resetear()

    ag = AsignacionGreedy(app_state.grafo)
    resultados = ag.asignar(
        app_state.pedidos,
        app_state.repartidores,
        coordinator = app_state.coordinator,   # ← evita colisiones
    )
    return GreedyResponse(
        total_pedidos   = len(app_state.pedidos),
        total_asignados = sum(len(r.ruta_pedidos) for r in resultados),
        asignaciones    = [r.to_dict() for r in resultados],
    )


# ── Divide y Vencerás ─────────────────────────────────────────────────────────

@router.post("/divide-venceras", response_model=DVResponse)
def divide_venceras(req: DVRequest):
    """
    Particiona el mapa en cuadrantes y asigna zonas a repartidores.
    """
    res = ejecutar_divide_venceras(
        app_state.pedidos, app_state.repartidores, app_state.grafo,
        umbral=req.umbral_pedidos, max_prof=req.max_profundidad,
    )
    return DVResponse(
        asignaciones         = {k: [p.id_pedido for p in v]
                                for k, v in res.asignaciones.items()},
        zonas_sin_repartidor = [z.nombre for z in res.zonas_sin_rep],
        zonas_generadas      = len(res.arbol_particion.zonas_hoja()),
        total_asignados      = sum(len(v) for v in res.asignaciones.values()),
    )


# ── Knapsack ──────────────────────────────────────────────────────────────────

@router.post("/knapsack/flota", response_model=KnapsackResponse)
def knapsack_flota(req: KnapsackRequest):
    """
    Optimiza la carga de cada repartidor usando Knapsack 0/1 (tabulación 2D).

    El coordinator garantiza que dos repartidores no elijan el mismo pedido
    aunque la petición llegue desde hilos concurrentes.
    """
    pendientes = app_state.pedidos_pendientes()
    resultados = resultado_mochila_flota(
        pendientes,
        app_state.repartidores,
        bonus_urgente = req.bonus_urgente,
        coordinator   = app_state.coordinator,   # ← evita colisiones
    )
    return KnapsackResponse(
        resultados        = [r.to_dict() for r in resultados],
        valor_flota_total = sum(r.valor_total for r in resultados),
        total_asignados   = sum(len(r.pedidos_elegidos) for r in resultados),
    )


# ── Backtracking — Búsqueda de rutas ─────────────────────────────────────────

@router.post("/backtracking", response_model=BacktrackingResponse)
def backtracking(req: BacktrackingRequest):
    """
    Búsqueda exhaustiva de rutas entre dos nodos con poda (Variante 1).
    """
    buscador    = BuscadorRutasBacktracking(app_state.grafo)
    if req.nodos_prohibidos:
        for nodo in req.nodos_prohibidos:
            if nodo not in app_state.grafo.nodos:
                raise HTTPException(400,
                    f"Nodo prohibido '{nodo}' no existe en el grafo. "
                    f"Válidos: {list(app_state.grafo.nodos.keys())[:10]}...")
        prohibidos  = set(req.nodos_prohibidos)
        restriccion = lambda nodo: nodo not in prohibidos
    else:
        restriccion = None

    res = buscador.buscar(
        req.origen, req.destino,
        max_paradas = req.max_paradas,
        max_rutas   = req.max_rutas,
        restriccion = restriccion,
    )
    return BacktrackingResponse(
        rutas_encontradas = len(res.todas_las_rutas),
        nodos_explorados  = res.nodos_explorados,
        podas_aplicadas   = res.podas_aplicadas,
        tiempo_ms         = res.tiempo_computo_ms,
        ruta_mas_corta    = res.ruta_mas_corta.to_dict()  if res.ruta_mas_corta  else None,
        ruta_mas_rapida   = res.ruta_mas_rapida.to_dict() if res.ruta_mas_rapida else None,
        todas_las_rutas   = [r.to_dict() for r in res.todas_las_rutas],
    )


# ── Backtracking — Asignación de pedidos ─────────────────────────────────────

@router.post("/backtracking/asignacion", response_model=AsignacionResponse)
def backtracking_asignacion(req: AsignacionRequest):
    """
    Asignación óptima de pedidos a repartidores con backtracking (Variante 2).
    Garantiza asignaciones que respetan todas las restricciones de capacidad
    y zona.
    """
    if req.resetear_estado:
        app_state.resetear()

    prioridad_min = Prioridad[req.prioridad_min]
    res = asignar_pedidos(
        app_state.pedidos,
        app_state.repartidores,
        prioridad_min = prioridad_min,
        grafo         = app_state.grafo,
    )
    return AsignacionResponse(
        total_asignados     = len(res.asignaciones),
        pedidos_sin_asignar = res.pedidos_sin_asignar,
        asignaciones        = [a.__dict__ for a in res.asignaciones],
        nodos_explorados    = res.nodos_explorados,
        podas_aplicadas     = res.podas_aplicadas,
        tiempo_ms           = res.tiempo_computo_ms,
        es_optima           = res.es_optima,
    )


# ── Ruta óptima (Dijkstra con caché compartido) ───────────────────────────────

@router.get("/ruta-optima/{origen}/{destino}", response_model=RutaOptimaResponse)
def ruta_optima(origen: str, destino: str):
    """
    Ruta más corta entre dos nodos usando Dijkstra con memoización.

    Reutiliza la instancia compartida app_state.ruta_pd para
    aprovechar el caché acumulado durante la sesión.
    """
    try:
        # CORRECCIÓN: pasa la instancia compartida, no crea una nueva
        res = ruta_optima_dijkstra(app_state.ruta_pd, origen, destino)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RutaOptimaResponse(
        origen      = res.origen,
        destino     = res.destino,
        camino      = res.camino,
        distancia_m = res.distancia_m,
        tiempo_min  = res.tiempo_min,
        desde_cache = res.desde_cache,
    )


# ── Estadísticas de rendimiento ───────────────────────────────────────────────

@router.get("/stats", tags=["Diagnóstico"])
def stats_algoritmos():
    """
    Métricas de rendimiento de los cachés del sistema.

    Incluye:
      - Hit ratio del caché de haversine (core.geo).
      - Hit ratio del caché de rutas Dijkstra.
      - Estado del coordinator (pedidos y nodos reservados).
    """
    return app_state.stats()


# ── Reset del sistema ─────────────────────────────────────────────────────────

@router.post("/resetear", tags=["Diagnóstico"])
def resetear_sistema():
    """
    Reinicia el estado del sistema.

    Limpia:
      - Reservas del DeliveryCoordinator.
      - Caché de rutas Dijkstra.
      - Estado de pedidos (todos a PENDIENTE).
      - Pedidos asignados de repartidores.
    """
    app_state.resetear()
    return {"ok": True, "mensaje": "Sistema reseteado correctamente"}
