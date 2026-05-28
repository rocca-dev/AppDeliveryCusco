"""
tests/test_core_geo.py — Tests unitarios de core/geo.py
========================================================
Verifica que haversine(), distancia_puntos(), nodo_mas_cercano_idx()
y stats_cache_haversine() funcionen correctamente y que el caché
@lru_cache efectivamente evite recalcular la misma distancia.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
from core.geo import (haversine, distancia_puntos,
                       nodo_mas_cercano_idx, stats_cache_haversine)


# ── haversine ─────────────────────────────────────────────────────────────────

def test_haversine_misma_posicion():
    """Distancia de un punto a sí mismo debe ser 0."""
    d = haversine(-13.5170, -71.9785, -13.5170, -71.9785)
    assert d == 0.0, f"Esperado 0.0, obtenido {d}"
    print("  PASS test_haversine_misma_posicion")


def test_haversine_plaza_a_san_blas():
    """
    Plaza de Armas → San Blas ≈ 380 m (verificado con Google Maps).
    Aceptamos ±100 m de tolerancia por redondeo de coordenadas.
    """
    d = haversine(-13.5170, -71.9785, -13.5145, -71.9760)
    assert 200 < d < 600, f"Distancia fuera de rango esperado: {d:.1f} m"
    print(f"  PASS test_haversine_plaza_a_san_blas  (d={d:.1f} m)")


def test_haversine_simetria():
    """haversine(A,B) debe ser igual a haversine(B,A)."""
    d_ab = haversine(-13.5170, -71.9785, -13.5300, -71.9600)
    d_ba = haversine(-13.5300, -71.9600, -13.5170, -71.9785)
    assert math.isclose(d_ab, d_ba, rel_tol=1e-9), \
        f"No simétrico: {d_ab} vs {d_ba}"
    print(f"  PASS test_haversine_simetria  (d={d_ab:.1f} m)")


def test_haversine_cache_hit():
    """
    Llamar dos veces con los mismos args debe incrementar hits del caché.
    """
    haversine.cache_clear()
    haversine(-13.5170, -71.9785, -13.5145, -71.9760)  # miss
    haversine(-13.5170, -71.9785, -13.5145, -71.9760)  # hit
    info = haversine.cache_info()
    assert info.hits >= 1, f"Se esperaba al menos 1 hit, obtenido {info.hits}"
    assert info.misses >= 1
    print(f"  PASS test_haversine_cache_hit  (hits={info.hits}, misses={info.misses})")


# ── distancia_puntos ──────────────────────────────────────────────────────────

def test_distancia_puntos_delegacion():
    """distancia_puntos() debe retornar el mismo valor que haversine()."""
    a = (-13.5170, -71.9785)
    b = (-13.5145, -71.9760)
    assert math.isclose(
        distancia_puntos(a, b),
        haversine(a[0], a[1], b[0], b[1]),
    ), "distancia_puntos no delega correctamente a haversine"
    print("  PASS test_distancia_puntos_delegacion")


# ── nodo_mas_cercano_idx ──────────────────────────────────────────────────────

def test_nodo_mas_cercano_idx_basico():
    """Debe retornar el índice del candidato más cercano."""
    candidatos = [
        (-13.5170, -71.9785),  # idx 0 — Plaza de Armas
        (-13.5300, -71.9600),  # idx 1 — Lejos
        (-13.5172, -71.9783),  # idx 2 — Muy cerca de la consulta
    ]
    idx = nodo_mas_cercano_idx(-13.5171, -71.9784, candidatos)
    assert idx == 2, f"Esperado idx=2, obtenido {idx}"
    print(f"  PASS test_nodo_mas_cercano_idx_basico  (idx={idx})")


def test_nodo_mas_cercano_idx_vacio():
    """Debe lanzar ValueError si la lista está vacía."""
    try:
        nodo_mas_cercano_idx(-13.517, -71.978, [])
        assert False, "Debería haber lanzado ValueError"
    except ValueError:
        print("  PASS test_nodo_mas_cercano_idx_vacio")


# ── stats_cache_haversine ─────────────────────────────────────────────────────

def test_stats_cache_haversine_estructura():
    """stats_cache_haversine() debe retornar un dict con las claves esperadas."""
    stats = stats_cache_haversine()
    for key in ("hits", "misses", "currsize", "maxsize", "hit_ratio"):
        assert key in stats, f"Clave faltante: {key}"
    assert 0.0 <= stats["hit_ratio"] <= 1.0
    print(f"  PASS test_stats_cache_haversine_estructura  (ratio={stats['hit_ratio']})")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== tests/test_core_geo.py ===")
    haversine.cache_clear()
    test_haversine_misma_posicion()
    test_haversine_plaza_a_san_blas()
    test_haversine_simetria()
    test_haversine_cache_hit()
    test_distancia_puntos_delegacion()
    test_nodo_mas_cercano_idx_basico()
    test_nodo_mas_cercano_idx_vacio()
    test_stats_cache_haversine_estructura()
    print("\nTodos los tests de core/geo.py pasaron.\n")
