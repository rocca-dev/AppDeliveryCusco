"""
Esquemas Pydantic para la API REST.
Define los modelos de request/response.
"""

from pydantic import BaseModel
from typing import Optional


# ── Ordenación ──

class OrdenarRequest(BaseModel):
    criterio   : str = "prioridad"
    descendente: bool = True

class OrdenarResponse(BaseModel):
    criterio: str
    total   : int
    pedidos : list[dict]

class BuscarRequest(BaseModel):
    termino: str
    tipo   : str = "id"

class BuscarResponse(BaseModel):
    resultado: list[dict]
    total    : int


# ── Greedy ──

class GreedyRequest(BaseModel):
    resetear_estado: bool = True

class GreedyResponse(BaseModel):
    total_pedidos  : int
    total_asignados: int
    asignaciones   : list[dict]


# ── Divide y Vencerás ──

class DVRequest(BaseModel):
    umbral_pedidos : int = 3
    max_profundidad: int = 3

class DVResponse(BaseModel):
    asignaciones    : dict[str, list[str]]
    zonas_sin_repartidor: list[str]
    zonas_generadas : int
    total_asignados : int


# ── Knapsack ──

class KnapsackRequest(BaseModel):
    bonus_urgente: float = 1.5

class KnapsackResponse(BaseModel):
    resultados       : list[dict]
    valor_flota_total: float
    total_asignados  : int


# ── Backtracking ──

class BacktrackingRequest(BaseModel):
    origen            : str
    destino           : str
    max_paradas       : int = 8
    max_rutas         : int = 30
    nodos_prohibidos  : list[str] = []
    puntos_obligatorios: list[str] = []

class BacktrackingResponse(BaseModel):
    rutas_encontradas : int
    nodos_explorados  : int
    podas_aplicadas   : int
    tiempo_ms         : float
    ruta_mas_corta    : Optional[dict] = None
    ruta_mas_rapida   : Optional[dict] = None
    todas_las_rutas   : list[dict] = []


# ── Mapa ──

class BloquearCalleRequest(BaseModel):
    origen : str
    destino: str

class RutaOptimaResponse(BaseModel):
    origen     : str
    destino    : str
    camino     : list[str]
    distancia_m: float
    tiempo_min : float
    desde_cache: bool = False

# ── Backtracking — Asignación de Pedidos (Variante 2) ──

class AsignacionPedidoSchema(BaseModel):
    """Schema de una asignación individual: pedido → repartidor."""
    id_pedido      : str
    id_repartidor  : str
    motivo_rechazo : str = ""

class AsignacionRequest(BaseModel):
    """
    Request para el endpoint POST /algoritmos/backtracking/asignacion.

    Campos:
        prioridad_min  : Nivel mínimo de prioridad a procesar.
                         "BAJA" | "MEDIA" | "ALTA" | "URGENTE"
        resetear_estado: Si True, descarta asignaciones previas de la sesión.
    """
    prioridad_min   : str  = "BAJA"
    resetear_estado : bool = False

class AsignacionResponse(BaseModel):
    """Response del endpoint de asignación backtracking."""
    total_asignados     : int
    pedidos_sin_asignar : list[str]
    asignaciones        : list[dict]
    nodos_explorados    : int
    podas_aplicadas     : int
    tiempo_ms           : float
    es_optima           : bool

