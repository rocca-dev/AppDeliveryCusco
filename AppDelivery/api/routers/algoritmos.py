"""
Router: /algoritmos
Ejecuta los algoritmos de optimización sobre los datos del sistema.
"""

from fastapi import APIRouter, HTTPException
from api.estado  import app_state
from api.schemas import (GreedyRequest, GreedyResponse,
                         DVRequest, DVResponse,
                         KnapsackRequest, KnapsackResponse,
                         BacktrackingRequest, BacktrackingResponse,
                         RutaOptimaResponse)
from algoritmos.greedy import NearestNeighborGreedy, AsignacionGreedy
from algoritmos.divide_venceras import ejecutar_divide_venceras
from algoritmos.programacion_dinamica import (Mochila01, resultado_mochila_flota,
                                               ruta_optima_dijkstra)
from algoritmos.backtracking import BuscadorRutasBacktracking
from modelos.pedido import EstadoPedido

router = APIRouter(prefix="/algoritmos", tags=["Algoritmos"])


@router.post("/greedy/asignacion", response_model=GreedyResponse)
def greedy_asignacion(req: GreedyRequest):
    if req.resetear_estado:
        app_state.resetear()
    ag = AsignacionGreedy(app_state.grafo)
    resultados = ag.asignar(app_state.pedidos, app_state.repartidores)
    return GreedyResponse(
        total_pedidos  = len(app_state.pedidos),
        total_asignados= sum(len(r.ruta_pedidos) for r in resultados),
        asignaciones   = [r.to_dict() for r in resultados],
    )


@router.post("/divide-venceras", response_model=DVResponse)
def divide_venceras(req: DVRequest):
    res = ejecutar_divide_venceras(
        app_state.pedidos, app_state.repartidores, app_state.grafo,
        umbral=req.umbral_pedidos, max_prof=req.max_profundidad,
    )
    return DVResponse(
        asignaciones        = {k: [p.id_pedido for p in v]
                               for k, v in res.asignaciones.items()},
        zonas_sin_repartidor= [z.nombre for z in res.zonas_sin_rep],
        zonas_generadas     = len(res.arbol_particion.zonas_hoja()),
        total_asignados     = sum(len(v) for v in res.asignaciones.values()),
    )


@router.post("/knapsack/flota", response_model=KnapsackResponse)
def knapsack_flota(req: KnapsackRequest):
    pendientes = [p for p in app_state.pedidos
                  if p.estado == EstadoPedido.PENDIENTE]
    resultados = resultado_mochila_flota(
        pendientes, app_state.repartidores,
        bonus_urgente=req.bonus_urgente,
    )
    return KnapsackResponse(
        resultados        = [r.to_dict() for r in resultados],
        valor_flota_total = sum(r.valor_total for r in resultados),
        total_asignados   = sum(len(r.pedidos_elegidos) for r in resultados),
    )


@router.post("/backtracking", response_model=BacktrackingResponse)
def backtracking(req: BacktrackingRequest):
    buscador = BuscadorRutasBacktracking(app_state.grafo)
    restriccion = None
    if req.nodos_prohibidos:
        prohibidos = set(req.nodos_prohibidos)
        restriccion = lambda nodo: nodo not in prohibidos
    res = buscador.buscar(
        req.origen, req.destino,
        max_paradas=req.max_paradas,
        max_rutas=req.max_rutas,
        restriccion=restriccion,
    )
    return BacktrackingResponse(
        rutas_encontradas=len(res.todas_las_rutas),
        nodos_explorados=res.nodos_explorados,
        podas_aplicadas=res.podas_aplicadas,
        tiempo_ms=res.tiempo_computo_ms,
        ruta_mas_corta=res.ruta_mas_corta.to_dict() if res.ruta_mas_corta else None,
        ruta_mas_rapida=res.ruta_mas_rapida.to_dict() if res.ruta_mas_rapida else None,
        todas_las_rutas=[r.to_dict() for r in res.todas_las_rutas],
    )


@router.get("/ruta-optima/{origen}/{destino}", response_model=RutaOptimaResponse)
def ruta_optima(origen: str, destino: str):
    res = app_state.ruta_pd.ruta_mas_corta(origen, destino)
    return RutaOptimaResponse(
        origen     = res.origen,
        destino    = res.destino,
        camino     = res.camino,
        distancia_m= res.distancia_m,
        tiempo_min = res.tiempo_min,
        desde_cache= res.desde_cache,
    )



@router.post("/resetear")
def resetear_sistema():
    app_state.resetear()
    return {"ok": True, "mensaje": "Sistema reseteado correctamente"}
