"""
Módulo: Backtracking (Búsqueda Exhaustiva)
==========================================
Encuentra TODAS las rutas posibles entre dos nodos del mapa de Cusco
respetando calles bloqueadas, y selecciona la más corta/rápida.

ESTRATEGIA
──────────
  DFS (búsqueda en profundidad) con retroceso:
    - Explora cada camino posible desde el origen.
    - Si llega a un nodo sin salida o ya visitado → RETROCEDE.
    - Si llega al destino → guarda la ruta encontrada.
    - Al finalizar → compara todas las rutas y retorna la mejor.

  Podas implementadas (reducen drásticamente el espacio de búsqueda):
    1. Poda por visitados    — no revisitar nodos (evita ciclos).
    2. Poda por costo        — si el costo acumulado ya supera al mejor
                               encontrado, abandonar esa rama.
    3. Poda por profundidad  — límite máximo de nodos en la ruta
                               (evita rutas absurdamente largas).

ANÁLISIS Big-O
──────────────
  Sin podas (fuerza bruta):
      O(V!)  — peor caso, todas las permutaciones de nodos.
      Con V=20 nodos: 20! = 2.4 × 10¹⁸ — imposible.

  Con podas (backtracking real):
      En la práctica O(b^d) donde:
        b = factor de ramificación promedio (vecinos por nodo ≈ 3)
        d = profundidad máxima de la ruta
      Con b=3, d=6: 3^6 = 729 operaciones — muy manejable.

  Espacio: O(d) — pila de recursión de profundidad d.

¿CUÁNDO USAR BACKTRACKING Y NO DIJKSTRA?
─────────────────────────────────────────
  Dijkstra: óptimo en tiempo O((V+E)logV), pero NO puede manejar
            restricciones complejas como "evitar ciertas calles
            Y pasar obligatoriamente por ciertos puntos".

  Backtracking: más lento en el peor caso, pero FLEXIBLE:
    - Puede imponer CUALQUIER restricción (calles cerradas,
      zonas prohibidas, puntos obligatorios, límite de paradas).
    - Encuentra TODAS las rutas válidas, no solo la más corta.
    - Permite analizar alternativas cuando la ruta principal
      está bloqueada.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Callable
import time

from modelos.grafo import Grafo


# ─────────────────────────────────────────────────────────────
#  Resultado de una búsqueda backtracking
# ─────────────────────────────────────────────────────────────

@dataclass
class RutaEncontrada:
    """Representa una ruta válida encontrada por backtracking."""
    camino      : list[str]    # secuencia de id_nodo
    distancia_m : float
    tiempo_min  : float
    num_paradas : int

    def __lt__(self, other: "RutaEncontrada") -> bool:
        return self.distancia_m < other.distancia_m

    def resumen(self) -> str:
        nombres = " → ".join(self.camino)
        return (f"  Ruta     : {nombres}\n"
                f"  Distancia: {self.distancia_m:,.0f} m "
                f"({self.distancia_m/1000:.2f} km)\n"
                f"  Tiempo   : {self.tiempo_min:.1f} min\n"
                f"  Paradas  : {self.num_paradas}")

    def to_dict(self) -> dict:
        return {
            "camino"      : self.camino,
            "distancia_m" : round(self.distancia_m, 2),
            "tiempo_min"  : round(self.tiempo_min,  2),
            "num_paradas" : self.num_paradas,
        }


@dataclass
class ResultadoBacktracking:
    """Resultado completo de una búsqueda exhaustiva."""
    origen            : str
    destino           : str
    todas_las_rutas   : list[RutaEncontrada] = field(default_factory=list)
    ruta_mas_corta    : Optional[RutaEncontrada] = None
    ruta_mas_rapida   : Optional[RutaEncontrada] = None
    nodos_explorados  : int   = 0
    podas_aplicadas   : int   = 0
    tiempo_computo_ms : float = 0.0

    def resumen(self) -> str:
        lineas = [
            f"Origen  : {self.origen}",
            f"Destino : {self.destino}",
            f"Rutas encontradas  : {len(self.todas_las_rutas)}",
            f"Nodos explorados   : {self.nodos_explorados}",
            f"Podas aplicadas    : {self.podas_aplicadas}",
            f"Tiempo de cómputo  : {self.tiempo_computo_ms:.4f} ms",
        ]
        if self.ruta_mas_corta:
            lineas.append("\nRuta MÁS CORTA (distancia):")
            lineas.append(self.ruta_mas_corta.resumen())
        if (self.ruta_mas_rapida and
                self.ruta_mas_rapida != self.ruta_mas_corta):
            lineas.append("\nRuta MÁS RÁPIDA (tiempo):")
            lineas.append(self.ruta_mas_rapida.resumen())
        return "\n".join(lineas)

    def to_dict(self) -> dict:
        return {
            "origen"           : self.origen,
            "destino"          : self.destino,
            "total_rutas"      : len(self.todas_las_rutas),
            "nodos_explorados" : self.nodos_explorados,
            "podas_aplicadas"  : self.podas_aplicadas,
            "tiempo_ms"        : round(self.tiempo_computo_ms, 4),
            "ruta_mas_corta"   : (self.ruta_mas_corta.to_dict()
                                  if self.ruta_mas_corta else None),
            "ruta_mas_rapida"  : (self.ruta_mas_rapida.to_dict()
                                  if self.ruta_mas_rapida else None),
            "todas_las_rutas"  : [r.to_dict()
                                  for r in self.todas_las_rutas],
        }


# ─────────────────────────────────────────────────────────────
#  Motor de Backtracking principal
# ─────────────────────────────────────────────────────────────

class BuscadorRutasBacktracking:
    """
    Búsqueda exhaustiva DFS con poda para encontrar todas las rutas
    válidas entre dos nodos del mapa de Cusco.

    Podas implementadas:
      1. Visitados        — no revisitar nodos en la misma ruta.
      2. Costo acumulado  — si dist_actual ≥ mejor_dist → podar.
      3. Profundidad máx  — si paradas > max_paradas → podar.
      4. Restricciones    — función externa (p.ej. evitar ciertas zonas).
    """

    def __init__(self, grafo: Grafo):
        self.grafo = grafo

    def buscar(self,
               origen          : str,
               destino         : str,
               max_paradas     : int = 8,
               max_rutas       : int = 50,
               restriccion     : Optional[Callable[[str], bool]] = None,
               ) -> ResultadoBacktracking:
        """
        Encuentra todas las rutas de `origen` a `destino`.

        Args:
            origen       : id_nodo de inicio.
            destino      : id_nodo de llegada.
            max_paradas  : Límite de nodos por ruta (poda profundidad).
            max_rutas    : Máximo de rutas a guardar (evita explosión).
            restriccion  : Función f(id_nodo) → True si el nodo está
                           PERMITIDO. None = todos permitidos.

        Returns:
            ResultadoBacktracking con todas las rutas y la mejor.

        Algoritmo:
            backtrack(nodo_actual, camino, dist_acum, tiempo_acum):
              if nodo_actual == destino:
                  guardar_ruta(camino, dist_acum, tiempo_acum)
                  return
              for vecino in vecinos_libres(nodo_actual):
                  ── PODAS ──
                  if vecino in visitados           : continue  (poda 1)
                  if dist_acum ≥ mejor_dist        : continue  (poda 2)
                  if len(camino) ≥ max_paradas     : continue  (poda 3)
                  if restriccion y no permitido    : continue  (poda 4)
                  ── AVANZAR ──
                  visitados.add(vecino)
                  backtrack(vecino, camino + [vecino], ...)
                  ── RETROCEDER ──
                  visitados.remove(vecino)
        """
        t0 = time.perf_counter()

        resultado = ResultadoBacktracking(origen=origen, destino=destino)

        # Validar que origen y destino existen
        if origen not in self.grafo.nodos:
            raise ValueError(f"Nodo origen '{origen}' no existe en el grafo.")
        if destino not in self.grafo.nodos:
            raise ValueError(f"Nodo destino '{destino}' no existe en el grafo.")

        # Estado mutable compartido con la recursión
        estado = {
            "mejor_dist"     : float("inf"),
            "nodos_explorados": 0,
            "podas"          : 0,
        }

        visitados: set[str] = {origen}

        # ── Función recursiva de backtracking ────────────────
        def backtrack(nodo_actual : str,
                      camino      : list[str],
                      dist_acum   : float,
                      tiempo_acum : float):

            estado["nodos_explorados"] += 1

            # ── CASO BASE: llegamos al destino ───────────────
            if nodo_actual == destino:
                ruta = RutaEncontrada(
                    camino      = list(camino),
                    distancia_m = dist_acum,
                    tiempo_min  = tiempo_acum,
                    num_paradas = len(camino) - 1,
                )
                resultado.todas_las_rutas.append(ruta)

                # Actualizar mejor distancia para poda futura
                if dist_acum < estado["mejor_dist"]:
                    estado["mejor_dist"] = dist_acum
                return

            # ── PODA 3: profundidad máxima ────────────────────
            if len(camino) >= max_paradas:
                estado["podas"] += 1
                return

            # ── PODA: límite de rutas encontradas ─────────────
            if len(resultado.todas_las_rutas) >= max_rutas:
                return

            # ── EXPLORAR vecinos ──────────────────────────────
            for arista in self.grafo.vecinos(nodo_actual, solo_libres=True):
                vecino = arista.destino

                # PODA 1: no revisitar nodos
                if vecino in visitados:
                    estado["podas"] += 1
                    continue

                # PODA 2: costo acumulado ya supera al mejor
                nueva_dist = dist_acum + arista.distancia_m
                if nueva_dist >= estado["mejor_dist"]:
                    estado["podas"] += 1
                    continue

                # PODA 4: restricción externa (zonas prohibidas)
                if restriccion is not None and not restriccion(vecino):
                    estado["podas"] += 1
                    continue

                # ── AVANZAR ──────────────────────────────────
                visitados.add(vecino)
                camino.append(vecino)

                backtrack(
                    vecino,
                    camino,
                    dist_acum   + arista.distancia_m,
                    tiempo_acum + arista.tiempo_min,
                )

                # ── RETROCEDER (backtrack) ────────────────────
                camino.pop()
                visitados.remove(vecino)

        # Iniciar búsqueda
        backtrack(origen, [origen], 0.0, 0.0)

        # ── Ordenar rutas por distancia ───────────────────────
        resultado.todas_las_rutas.sort(key=lambda r: r.distancia_m)

        # Seleccionar mejores rutas
        if resultado.todas_las_rutas:
            resultado.ruta_mas_corta  = resultado.todas_las_rutas[0]
            resultado.ruta_mas_rapida = min(
                resultado.todas_las_rutas,
                key=lambda r: r.tiempo_min
            )

        resultado.nodos_explorados  = estado["nodos_explorados"]
        resultado.podas_aplicadas   = estado["podas"]
        resultado.tiempo_computo_ms = (time.perf_counter() - t0) * 1000

        return resultado


# ─────────────────────────────────────────────────────────────
#  Extensión: Backtracking con puntos obligatorios
# ─────────────────────────────────────────────────────────────

class BuscadorConPuntosObligatorios:
    """
    Variante que exige pasar por ciertos nodos intermedios.
    Divide el problema en subproblemas: origen→p1→p2→...→destino.
    Usa backtracking en cada segmento.

    Caso de uso: "Ir de San Blas a Wanchaq, pasando obligatoriamente
                  por la Plaza de Armas para recoger un paquete."

    Complejidad: O(k × b^d)
      k = número de segmentos (puntos_obligatorios + 1)
      b = factor de ramificación, d = profundidad por segmento
    """

    def __init__(self, grafo: Grafo):
        self.buscador = BuscadorRutasBacktracking(grafo)

    def buscar(self,
               origen             : str,
               destino            : str,
               puntos_obligatorios: list[str],
               max_paradas        : int = 6,
               ) -> dict:
        """
        Construye la ruta pasando por cada punto obligatorio.

        Returns:
            dict con segmentos, ruta_completa y métricas totales.
        """
        secuencia  = [origen] + puntos_obligatorios + [destino]
        segmentos  = []
        ruta_total = [origen]
        dist_total = 0.0
        tiempo_total = 0.0
        viable     = True

        for i in range(len(secuencia) - 1):
            orig_seg = secuencia[i]
            dest_seg = secuencia[i + 1]

            res = self.buscador.buscar(
                orig_seg, dest_seg,
                max_paradas=max_paradas,
                max_rutas=10,
            )

            if not res.ruta_mas_corta:
                viable = False
                segmentos.append({
                    "origen" : orig_seg,
                    "destino": dest_seg,
                    "estado" : "SIN RUTA",
                })
                break

            r = res.ruta_mas_corta
            # Agregar nodos del segmento (sin repetir el nodo de unión)
            ruta_total.extend(r.camino[1:])
            dist_total   += r.distancia_m
            tiempo_total += r.tiempo_min
            segmentos.append({
                "origen"     : orig_seg,
                "destino"    : dest_seg,
                "camino"     : r.camino,
                "distancia_m": round(r.distancia_m, 2),
                "tiempo_min" : round(r.tiempo_min,  2),
                "estado"     : "OK",
            })

        return {
            "viable"         : viable,
            "ruta_completa"  : ruta_total,
            "distancia_total": round(dist_total,   2),
            "tiempo_total"   : round(tiempo_total, 2),
            "segmentos"      : segmentos,
        }


# ─────────────────────────────────────────────────────────────
#  Función de conveniencia para la API
# ─────────────────────────────────────────────────────────────

def buscar_rutas(grafo        : Grafo,
                 origen       : str,
                 destino      : str,
                 max_paradas  : int = 8,
                 max_rutas    : int = 20,
                 restriccion  : Optional[Callable[[str], bool]] = None,
                 ) -> ResultadoBacktracking:
    """
    Interfaz simplificada para buscar rutas con backtracking.
    Usada directamente por la API FastAPI.
    """
    buscador = BuscadorRutasBacktracking(grafo)
    return buscador.buscar(origen, destino,
                           max_paradas, max_rutas, restriccion)