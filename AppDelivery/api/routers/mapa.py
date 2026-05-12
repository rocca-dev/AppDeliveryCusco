"""
Router: /mapa
Proporciona datos del grafo (nodos y aristas) para el frontend
y permite bloquear/desbloquear calles en tiempo real.
"""

from fastapi import APIRouter, HTTPException
from api.estado   import app_state
from api.schemas  import BloquearCalleRequest

router = APIRouter(prefix="/mapa", tags=["Mapa"])


@router.get("/grafo")
def obtener_grafo():
    return app_state.grafo.to_dict()


@router.get("/nodos")
def obtener_nodos():
    return [n.to_dict() for n in app_state.grafo.nodos.values()]


@router.get("/aristas")
def obtener_aristas():
    aristas = []
    for lista in app_state.grafo.aristas.values():
        for a in lista:
            aristas.append(a.to_dict())
    return aristas


@router.get("/sectores")
def obtener_sectores():
    return {"sectores": app_state.grafo.sectores()}


@router.post("/bloquear")
def bloquear_calle(req: BloquearCalleRequest):
    """Bloquea una calle en el grafo en tiempo real."""
    if req.origen not in app_state.grafo.nodos:
        raise HTTPException(404, f"Nodo origen '{req.origen}' no existe")
    if req.destino not in app_state.grafo.nodos:
        raise HTTPException(404, f"Nodo destino '{req.destino}' no existe")
    app_state.grafo.bloquear_calle(req.origen, req.destino)
    # Invalidar caché de rutas que pueden haber usado esta arista
    if app_state.ruta_pd:
        app_state.ruta_pd.limpiar_cache()
    return {"ok": True, "accion": "bloquear",
            "origen": req.origen, "destino": req.destino}


@router.post("/desbloquear")
def desbloquear_calle(req: BloquearCalleRequest):
    """Desbloquea una calle previamente cerrada."""
    if req.origen not in app_state.grafo.nodos:
        raise HTTPException(404, f"Nodo origen '{req.origen}' no existe")
    if req.destino not in app_state.grafo.nodos:
        raise HTTPException(404, f"Nodo destino '{req.destino}' no existe")
    app_state.grafo.desbloquear_calle(req.origen, req.destino)
    if app_state.ruta_pd:
        app_state.ruta_pd.limpiar_cache()
    return {"ok": True, "accion": "desbloquear",
            "origen": req.origen, "destino": req.destino}
