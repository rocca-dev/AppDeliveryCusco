"""
core/geo.py — Utilidades Geométricas Centralizadas
====================================================
Fuente ÚNICA de verdad para todos los cálculos geoespaciales del sistema.

ANTES del refactor, la fórmula de Haversine estaba duplicada en:
  - modelos/grafo.py         (Grafo._haversine)
  - algoritmos/greedy.py     (cálculo inline en el loop)
  - algoritmos/divide_venceras.py (distancia entre centros de zona)

AHORA todos los módulos importan desde aquí, eliminando la redundancia
y aprovechando @functools.lru_cache para evitar recalcular la misma
distancia entre los mismos pares de coordenadas (muy frecuente durante
la construcción de rutas).

MEMOIZACIÓN APLICADA
─────────────────────
  haversine() → @lru_cache(maxsize=4096)
    Clave  : (lat1, lon1, lat2, lon2)  — floats son hashables
    Beneficio: en el Greedy se llama O(n²) veces por repartidor; con
               caché, los pares ya calculados son O(1) en vez de O(1)
               pero con 7 operaciones trigonométricas cada una.
    Tamaño : 4096 entradas × ~200 bytes ≈ 800 KB — razonable.

  NOTA sobre precisión: los floats de coordenadas GPS (6 decimales)
  son deterministas; dos llamadas con los mismos valores producen
  exactamente la misma clave de caché.

Análisis Big-O
──────────────
  haversine            : O(1)  — operaciones aritméticas fijas
  distancia_puntos     : O(1)  — delegación directa
  nodo_mas_cercano_idx : O(n)  — itera la lista de candidatos
"""

from __future__ import annotations

import math
import functools
from typing import Sequence


# ─────────────────────────────────────────────────────────────────────────────
#  Constante global
# ─────────────────────────────────────────────────────────────────────────────
_RADIO_TIERRA_M: float = 6_371_000.0   # radio medio de la Tierra en metros


# ─────────────────────────────────────────────────────────────────────────────
#  Función principal — memoizada
# ─────────────────────────────────────────────────────────────────────────────
@functools.lru_cache(maxsize=4096)
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Distancia real entre dos puntos GPS usando la fórmula de Haversine.

    Retorna la distancia en **metros** a lo largo de la superficie esférica
    de la Tierra.  Es la métrica geoespacial estándar para distancias
    inferiores a ~1000 km donde la curvatura importa pero la elipsoide no.

    Complejidad: O(1) — primer llamada; O(1) con caché en llamadas repetidas.

    Args:
        lat1, lon1 : Coordenadas del punto de origen en grados decimales.
        lat2, lon2 : Coordenadas del punto de destino en grados decimales.

    Returns:
        Distancia en metros (float ≥ 0).

    Ejemplos:
        >>> haversine(-13.5170, -71.9785, -13.5145, -71.9760)   # Plaza → San Blas
        ~380.0 m
    """
    phi1   = math.radians(lat1)
    phi2   = math.radians(lat2)
    dphi   = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)

    return _RADIO_TIERRA_M * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


# ─────────────────────────────────────────────────────────────────────────────
#  Alias conveniente para pares de tuplas
# ─────────────────────────────────────────────────────────────────────────────
def distancia_puntos(
    origen : tuple[float, float],
    destino: tuple[float, float],
) -> float:
    """
    Delegación a haversine() que acepta tuplas (lat, lon).

    Útil cuando el llamador ya tiene las coordenadas como tuplas,
    para evitar el desempaquetado manual.

    Args:
        origen  : (latitud, longitud) del punto de origen.
        destino : (latitud, longitud) del punto de destino.

    Returns:
        Distancia en metros.
    """
    return haversine(origen[0], origen[1], destino[0], destino[1])


# ─────────────────────────────────────────────────────────────────────────────
#  Búsqueda del punto más cercano en una colección
# ─────────────────────────────────────────────────────────────────────────────
def nodo_mas_cercano_idx(
    lat        : float,
    lon        : float,
    candidatos : Sequence[tuple[float, float]],
) -> int:
    """
    Índice del candidato más cercano a (lat, lon) en la secuencia dada.

    Itera la secuencia completa → O(n).  Para n pequeño (grafo de Cusco
    con ~20 nodos) esto es negligible; para n grande se puede cambiar
    por un k-d tree sin modificar la interfaz.

    Args:
        lat, lon   : Coordenadas del punto de consulta.
        candidatos : Secuencia de tuplas (lat, lon).

    Returns:
        Índice del candidato más cercano (int).

    Raises:
        ValueError : Si la secuencia está vacía.
    """
    if not candidatos:
        raise ValueError("La secuencia de candidatos no puede estar vacía.")

    mejor_idx  = 0
    mejor_dist = float("inf")

    for i, (c_lat, c_lon) in enumerate(candidatos):
        d = haversine(lat, lon, c_lat, c_lon)
        if d < mejor_dist:
            mejor_dist = d
            mejor_idx  = i

    return mejor_idx


# ─────────────────────────────────────────────────────────────────────────────
#  Utilidad de diagnóstico de caché
# ─────────────────────────────────────────────────────────────────────────────
def stats_cache_haversine() -> dict:
    """
    Retorna las estadísticas de uso del caché de haversine().

    Útil para el endpoint /health de la API para monitorear la
    efectividad de la memoización en producción.

    Returns:
        dict con hits, misses, currsize y maxsize.
    """
    info = haversine.cache_info()
    return {
        "hits"    : info.hits,
        "misses"  : info.misses,
        "currsize": info.currsize,
        "maxsize" : info.maxsize,
        "hit_ratio": round(
            info.hits / max(info.hits + info.misses, 1), 3
        ),
    }
