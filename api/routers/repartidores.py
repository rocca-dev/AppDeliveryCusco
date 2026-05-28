"""
api/routers/repartidores.py — Router: /repartidores
====================================================
Endpoints para consultar repartidores y sus rutas asignadas.
"""

from fastapi import APIRouter, HTTPException

from api.estado import app_state

router = APIRouter(prefix="/repartidores", tags=["Repartidores"])


@router.get("/")
def listar_repartidores():
    """Retorna todos los repartidores con su estado actual."""
    return [r.to_dict() for r in app_state.repartidores]


@router.get("/{id_repartidor}")
def obtener_repartidor(id_repartidor: str):
    """Retorna un repartidor específico por su ID."""
    for r in app_state.repartidores:
        if r.id_repartidor == id_repartidor:
            return r.to_dict()
    raise HTTPException(404, f"Repartidor '{id_repartidor}' no encontrado")


@router.get("/{id_repartidor}/ruta")
def ruta_repartidor(id_repartidor: str):
    """
    Retorna la ruta completa del repartidor: desde su posición actual
    hasta cada pedido asignado, calculada con Dijkstra.
    """
    rep = None
    for r in app_state.repartidores:
        if r.id_repartidor == id_repartidor:
            rep = r
            break
    if not rep:
        raise HTTPException(404, f"Repartidor '{id_repartidor}' no encontrado")

    from algoritmos.dp.dijkstra_memo import ruta_optima_dijkstra

    segmentos = []
    nodo_actual = None

    # Encontrar nodo más cercano a la posición actual del repartidor
    from core.geo import nodo_mas_cercano_idx
    nodos_lista = sorted(app_state.grafo.nodos.values(), key=lambda n: n.id_nodo)
    candidatos = [(n.latitud, n.longitud) for n in nodos_lista]
    idx = nodo_mas_cercano_idx(rep.latitud_actual, rep.longitud_actual, candidatos)
    nodo_actual = nodos_lista[idx].id_nodo

    for pedido in rep.pedidos_asignados:
        destino = pedido.id_nodo
        try:
            res = ruta_optima_dijkstra(app_state.ruta_pd, nodo_actual, destino)
            segmentos.append({
                "origen": nodo_actual,
                "destino": destino,
                "camino": res.camino,
                "distancia_m": res.distancia_m,
                "tiempo_min": res.tiempo_min,
                "id_pedido": pedido.id_pedido,
            })
            nodo_actual = destino
        except ValueError:
            continue

    return {
        "id_repartidor": rep.id_repartidor,
        "nombre": rep.nombre,
        "vehiculo": rep.vehiculo.value,
        "posicion": {"lat": rep.latitud_actual, "lon": rep.longitud_actual},
        "nodo_inicio": nodo_actual,
        "segmentos": segmentos,
        "distancia_total_m": sum(s["distancia_m"] for s in segmentos),
        "tiempo_total_min": sum(s["tiempo_min"] for s in segmentos),
        "pedidos_asignados": [p.id_pedido for p in rep.pedidos_asignados],
    }
