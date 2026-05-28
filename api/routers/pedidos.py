"""
api/routers/pedidos.py — Router: /pedidos
==========================================
Endpoints para listar, ordenar y buscar pedidos del sistema.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from api.estado import app_state
from api.schemas import OrdenarRequest, OrdenarResponse, BuscarRequest, BuscarResponse

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.get("/")
def listar_pedidos():
    """Retorna la lista completa de pedidos en formato dict."""
    return [p.to_dict() for p in app_state.pedidos]


@router.get("/pendientes")
def pedidos_pendientes():
    """Retorna solo los pedidos con estado pendiente."""
    return [p.to_dict() for p in app_state.pedidos_pendientes()]


@router.post("/ordenar/resultado", response_model=OrdenarResponse)
def ordenar_pedidos(req: OrdenarRequest):
    """
    Ordena los pedidos usando Merge Sort según el criterio indicado.

    Criterios: prioridad, valor, peso, sector, combinado.
    """
    from algoritmos.ordenacion import (
        ordenar_por_prioridad, ordenar_por_valor, ordenar_por_peso,
        ordenar_por_sector, ordenar_combinado,
    )

    pendientes = app_state.pedidos_pendientes()

    criterio_map = {
        "prioridad" : ordenar_por_prioridad,
        "valor"     : ordenar_por_valor,
        "peso"      : ordenar_por_peso,
        "sector"    : ordenar_por_sector,
        "combinado" : ordenar_combinado,
    }

    orden_fn = criterio_map.get(req.criterio)
    if not orden_fn:
        raise HTTPException(400, f"Criterio inválido: {req.criterio}. "
                                 f"Usar: prioridad, valor, peso, sector, combinado")

    if req.criterio in ("prioridad", "valor", "peso", "combinado"):
        ordenados = orden_fn(pendientes, descendente=req.descendente)
    else:
        ordenados = orden_fn(pendientes)

    return OrdenarResponse(
        criterio=req.criterio,
        total=len(ordenados),
        pedidos=[p.to_dict() for p in ordenados],
    )


@router.post("/buscar/resultado", response_model=BuscarResponse)
def buscar_pedido(req: BuscarRequest):
    """
    Busca pedidos por ID (búsqueda binaria) o por sector (hash map).

    Args:
        termino: ID del pedido (ej. "P003") o nombre del sector.
        tipo: "id" para búsqueda binaria, "sector" para hash lookup.
    """
    if req.tipo == "id":
        # Usa AppState._pedidos_ordenados pre-cacheado
        pedido = app_state.buscar_binaria(req.termino)
        resultados = [pedido.to_dict()] if pedido else []

    elif req.tipo == "sector":
        encontrados = app_state.buscar_por_sector(req.termino)
        resultados = [p.to_dict() for p in encontrados]

    else:
        raise HTTPException(400, f"Tipo de búsqueda inválido: {req.tipo}. Usar: id, sector")

    return BuscarResponse(resultado=resultados, total=len(resultados))


@router.get("/{id_pedido}")
def obtener_pedido(id_pedido: str):
    """Retorna un pedido específico por su ID."""
    pedido = app_state.buscar_por_id(id_pedido)
    if not pedido:
        raise HTTPException(404, f"Pedido '{id_pedido}' no encontrado")
    return pedido.to_dict()
