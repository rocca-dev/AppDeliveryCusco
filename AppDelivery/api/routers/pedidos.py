"""
Router: /pedidos
Gestiona la consulta, ordenación y búsqueda de pedidos.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from api.estado  import app_state
from api.schemas import (OrdenarRequest, OrdenarResponse,
                         BuscarRequest, BuscarResponse)
from algoritmos.ordenacion import (ordenar_por_prioridad, ordenar_por_peso,
                                   ordenar_por_valor, ordenar_por_distancia,
                                   ordenar_por_sector, ordenar_combinado)
from algoritmos.busqueda import busqueda_binaria_id, IndicePedidos

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.get("/")
def listar_pedidos():
    return [p.to_dict() for p in app_state.pedidos]


@router.get("/{id_pedido}")
def obtener_pedido(id_pedido: str):
    for p in app_state.pedidos:
        if p.id_pedido == id_pedido:
            return p.to_dict()
    raise HTTPException(404, f"Pedido '{id_pedido}' no encontrado")


@router.post("/ordenar/resultado", response_model=OrdenarResponse)
def ordenar_pedidos(req: OrdenarRequest):
    """
    Ordena pedidos por criterio. Para 'distancia' use el endpoint dedicado.
    Criterios: prioridad | peso | valor | sector | combinado
    """
    criterios = {
        "prioridad": lambda p: ordenar_por_prioridad(p, req.descendente),
        "peso"     : lambda p: ordenar_por_peso(p, req.descendente),
        "valor"    : lambda p: ordenar_por_valor(p, req.descendente),
        "sector"   : lambda p: ordenar_por_sector(p),
        "combinado": lambda p: ordenar_combinado(p),
    }
    fn = criterios.get(req.criterio)
    if not fn:
        raise HTTPException(400,
            f"Criterio '{req.criterio}' no válido. "
            f"Válidos: {list(criterios.keys())} (para distancia: GET /pedidos/ordenar/distancia)")
    ordenados = fn(app_state.pedidos)
    return OrdenarResponse(
        criterio=req.criterio,
        total=len(ordenados),
        pedidos=[p.to_dict() for p in ordenados],
    )


@router.get("/ordenar/distancia", response_model=OrdenarResponse)
def ordenar_por_distancia_desde(
    lat: float = Query(..., description="Latitud del punto de origen"),
    lon: float = Query(..., description="Longitud del punto de origen"),
):
    """
    Ordena pedidos por distancia haversine desde un punto GPS dado.
    Útil para planificar rutas desde la posición actual del repartidor.
    """
    ordenados = ordenar_por_distancia(app_state.pedidos, lat, lon)
    return OrdenarResponse(
        criterio="distancia",
        total=len(ordenados),
        pedidos=[p.to_dict() for p in ordenados],
    )


@router.post("/buscar/resultado", response_model=BuscarResponse)
def buscar_pedidos(req: BuscarRequest):
    if req.tipo == "id":
        por_id = sorted(app_state.pedidos, key=lambda p: p.id_pedido)
        p = busqueda_binaria_id(por_id, req.termino)
        resultado = [p.to_dict()] if p else []
    elif req.tipo == "sector":
        indice = IndicePedidos(app_state.pedidos)
        resultado = [p.to_dict() for p in indice.buscar_por_sector(req.termino)]
    else:
        raise HTTPException(400, f"Tipo '{req.tipo}' no válido. Válidos: id | sector")
    return BuscarResponse(resultado=resultado, total=len(resultado))
