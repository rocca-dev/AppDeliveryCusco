"""
algoritmos/backtracking/buscador_rutas.py — Búsqueda de Rutas con Backtracking
================================================================================
Explora exhaustivamente todas las rutas posibles entre dos nodos del grafo,
aplicando poda para descartar ramas no prometedoras.

Variante 1: BuscadorRutasBacktracking — rutas entre origen y destino.
Variante 2: BuscadorConPuntosObligatorios — rutas que pasan por puntos específicos.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from modelos.grafo import Grafo


# ─────────────────────────────────────────────────────────────────────────────
#  Resultados
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RutaEncontrada:
    """
    Una ruta encontrada por el backtracking.

    Atributos:
        camino      : Lista ordenada de id_nodo desde origen hasta destino.
        distancia_m : Distancia total en metros.
        tiempo_min  : Tiempo total estimado en minutos.
        num_paradas : Número de paradas intermedias.
    """
    camino      : list[str]
    distancia_m : float = 0.0
    tiempo_min  : float = 0.0
    num_paradas : int   = 0

    def to_dict(self) -> dict:
        return {
            "camino"      : self.camino,
            "distancia_m" : round(self.distancia_m, 2),
            "tiempo_min"  : round(self.tiempo_min, 2),
            "num_paradas" : self.num_paradas,
        }


@dataclass
class ResultadoBacktracking:
    """
    Resultado completo de la búsqueda backtracking.

    Atributos:
        todas_las_rutas  : Lista de todas las rutas encontradas.
        nodos_explorados : Cantidad total de nodos visitados.
        podas_aplicadas  : Cantidad de podas realizadas.
        tiempo_computo_ms: Tiempo de ejecución en milisegundos.
        ruta_mas_corta   : Ruta con menor distancia (None si no hay rutas).
        ruta_mas_rapida  : Ruta con menor tiempo (None si no hay rutas).
    """
    todas_las_rutas  : list[RutaEncontrada] = field(default_factory=list)
    nodos_explorados : int = 0
    podas_aplicadas  : int = 0
    tiempo_computo_ms: float = 0.0
    ruta_mas_corta   : Optional[RutaEncontrada] = None
    ruta_mas_rapida  : Optional[RutaEncontrada] = None


# ─────────────────────────────────────────────────────────────────────────────
#  Buscador principal
# ─────────────────────────────────────────────────────────────────────────────

class BuscadorRutasBacktracking:
    """
    Búsqueda exhaustiva de rutas entre dos nodos con poda.

    Implementa backtracking clásico:
      - Explora recursivamente todos los vecinos de cada nodo.
      - Poda rutas que exceden max_paradas.
      - Poda rutas que ya visitaron un nodo (evita ciclos).
      - Aplica restricción opcional (nodos prohibidos).

    Complejidad: O(b^d) en el peor caso, donde b = factor de ramificación
    y d = profundidad máxima. La poda reduce significativamente en la práctica.
    """

    def __init__(self, grafo: "Grafo"):
        self.grafo = grafo

    def buscar(
        self,
        origen     : str,
        destino    : str,
        max_paradas: int = 8,
        max_rutas  : int = 30,
        restriccion: Optional[Callable[[str], bool]] = None,
    ) -> ResultadoBacktracking:
        """
        Encuentra todas las rutas de origen a destino con poda.

        Args:
            origen      : Nodo de inicio.
            destino     : Nodo de llegada.
            max_paradas : Máximo de paradas intermedias.
            max_rutas   : Máximo de rutas a encontrar.
            restriccion : Función que retorna False para nodos prohibidos.

        Returns:
            ResultadoBacktracking con las rutas y estadísticas.
        """
        inicio = time.perf_counter()
        resultado = ResultadoBacktracking()

        if origen not in self.grafo.nodos:
            raise ValueError(f"Nodo origen '{origen}' no existe en el grafo.")
        if destino not in self.grafo.nodos:
            raise ValueError(f"Nodo destino '{destino}' no existe en el grafo.")

        camino_actual: list[str] = [origen]

        def backtrack(nodo: str, profundidad: int):
            if len(resultado.todas_las_rutas) >= max_rutas:
                return

            if profundidad > max_paradas:
                resultado.podas_aplicadas += 1
                return

            resultado.nodos_explorados += 1

            for arista in self.grafo.vecinos(nodo, solo_libres=True):
                vecino = arista.destino

                # Poda: nodo ya visitado (evita ciclos)
                if vecino in camino_actual:
                    resultado.podas_aplicadas += 1
                    continue

                # Poda: restricción de nodos prohibidos
                if restriccion and not restriccion(vecino):
                    resultado.podas_aplicadas += 1
                    continue

                camino_actual.append(vecino)

                if vecino == destino:
                    # Ruta completa encontrada
                    distancia = sum(
                        a.distancia_m
                        for i in range(len(camino_actual) - 1)
                        for a in self.grafo.vecinos(camino_actual[i], solo_libres=True)
                        if a.destino == camino_actual[i + 1]
                    )
                    tiempo = sum(
                        a.tiempo_min
                        for i in range(len(camino_actual) - 1)
                        for a in self.grafo.vecinos(camino_actual[i], solo_libres=True)
                        if a.destino == camino_actual[i + 1]
                    )
                    ruta = RutaEncontrada(
                        camino=list(camino_actual),
                        distancia_m=distancia,
                        tiempo_min=tiempo,
                        num_paradas=profundidad,
                    )
                    resultado.todas_las_rutas.append(ruta)
                else:
                    backtrack(vecino, profundidad + 1)

                camino_actual.pop()

        backtrack(origen, 0)

        # Calcular mejores rutas
        if resultado.todas_las_rutas:
            resultado.ruta_mas_corta = min(
                resultado.todas_las_rutas, key=lambda r: r.distancia_m
            )
            resultado.ruta_mas_rapida = min(
                resultado.todas_las_rutas, key=lambda r: r.tiempo_min
            )

        resultado.tiempo_computo_ms = (time.perf_counter() - inicio) * 1000
        return resultado


# ─────────────────────────────────────────────────────────────────────────────
#  Variante 2: con puntos obligatorios
# ─────────────────────────────────────────────────────────────────────────────

class BuscadorConPuntosObligatorios(BuscadorRutasBacktracking):
    """
    Extensión del BuscadorRutasBacktracking que obliga a la ruta
    a pasar por una lista de nodos intermedios específicos.

    Estrategia: busca rutas entre cada par consecutivo de puntos
    obligatorios (incluyendo origen y destino) y las concatena.

    Complejidad: O(m × b^d) donde m = número de segmentos entre puntos.
    """

    def buscar_con_puntos(
        self,
        origen            : str,
        destino           : str,
        puntos_obligatorios: list[str],
        max_paradas       : int = 8,
        max_rutas         : int = 30,
    ) -> ResultadoBacktracking:
        """
        Busca ruta que pasa por todos los puntos obligatorios.

        Los puntos se ordenan geográficamente y se concatenan
        las rutas entre cada segmento.

        Args:
            origen             : Nodo de inicio.
            destino            : Nodo final.
            puntos_obligatorios: Lista de nodos que deben visitarse.
            max_paradas        : Máximo de paradas por segmento.
            max_rutas          : Máximo de rutas a explorar.

        Returns:
            ResultadoBacktracking con la ruta completa combinada.
        """
        puntos = [origen] + puntos_obligatorios + [destino]
        rutas_segmentos = []

        for i in range(len(puntos) - 1):
            res = self.buscar(
                puntos[i], puntos[i + 1],
                max_paradas=max_paradas,
                max_rutas=max_rutas,
            )
            if not res.todas_las_rutas:
                return ResultadoBacktracking()
            rutas_segmentos.append(res.ruta_mas_corta)

        # Combinar
        camino_completo = []
        distancia_total = 0.0
        tiempo_total = 0.0

        for i, ruta in enumerate(rutas_segmentos):
            if i == 0:
                camino_completo.extend(ruta.camino)
            else:
                camino_completo.extend(ruta.camino[1:])
            distancia_total += ruta.distancia_m
            tiempo_total += ruta.tiempo_min

        ruta_unica = RutaEncontrada(
            camino=camino_completo,
            distancia_m=distancia_total,
            tiempo_min=tiempo_total,
            num_paradas=len(camino_completo) - 2,
        )

        res_final = ResultadoBacktracking(
            todas_las_rutas=[ruta_unica],
            nodos_explorados=sum(r.nodos_explorados for r in rutas_segmentos),
            podas_aplicadas=sum(r.podas_aplicadas for r in rutas_segmentos),
            tiempo_computo_ms=sum(r.tiempo_computo_ms for r in rutas_segmentos),
            ruta_mas_corta=ruta_unica,
            ruta_mas_rapida=ruta_unica,
        )
        return res_final


# ─────────────────────────────────────────────────────────────────────────────
#  Función de conveniencia
# ─────────────────────────────────────────────────────────────────────────────

def buscar_rutas(
    grafo      : "Grafo",
    origen     : str,
    destino    : str,
    max_paradas: int = 8,
    max_rutas  : int = 30,
) -> ResultadoBacktracking:
    """
    Función de conveniencia que crea un BuscadorRutasBacktracking
    y ejecuta la búsqueda.

    Args:
        grafo      : Grafo del mapa.
        origen     : Nodo de inicio.
        destino    : Nodo de destino.
        max_paradas: Máximo de paradas.
        max_rutas  : Máximo de rutas.

    Returns:
        ResultadoBacktracking con las rutas encontradas.
    """
    buscador = BuscadorRutasBacktracking(grafo)
    return buscador.buscar(origen, destino, max_paradas, max_rutas)
