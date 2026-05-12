"""
Módulo: Divide y Vencerás
=========================
Segmenta el mapa de Cusco en cuadrantes/zonas de forma recursiva,
reduciendo el problema de ruteo de toda la ciudad a subproblemas
independientes que cada repartidor resuelve en su sub-zona.

ESTRATEGIA
──────────
  1. ParticionadorCuadrantes  — divide el bounding box del mapa en 4
                                 cuadrantes (NE, NO, SE, SO) de forma
                                 recursiva hasta que cada zona tenga
                                 ≤ umbral pedidos o profundidad máxima.

  2. AsignadorZonas           — dado el árbol de partición, asigna cada
                                 zona hoja a un repartidor disponible
                                 y delega la ruta interna al Greedy.

  3. MergeSortEspacial        — variante de Merge Sort para ordenar
                                 pedidos por coordenada X o Y antes de
                                 partir; acelera el particionado.

ANÁLISIS Big-O
──────────────
  Particionado recursivo:
      T(n) = 4·T(n/4) + O(n)   →   O(n log n)  por el Teorema Maestro
      (caso 2: a=4, b=4, f(n)=n → log_b(a)=1 → O(n log n))

  Asignación de zonas a repartidores:
      O(z × r)  donde z = zonas hoja, r = repartidores

  Ruta interna por zona (Greedy):
      O(k²)  donde k = pedidos de esa zona (k << n global)

  Beneficio clave: k << n  →  O(k²) << O(n²)
  Ejemplo: 40 pedidos, 4 zonas de 10 c/u
    Global Greedy : O(40²) = 1600 ops
    D&V + Greedy  : 4 × O(10²) = 400 ops  → 4× más rápido
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math

from modelos.pedido     import Pedido, EstadoPedido
from modelos.repartidor import Repartidor
from modelos.grafo      import Grafo, Nodo


# ─────────────────────────────────────────────────────────────
#  Bounding Box — rectángulo geográfico de una zona
# ─────────────────────────────────────────────────────────────

@dataclass
class BoundingBox:
    """
    Rectángulo geográfico definido por sus extremos.
    Todas las coordenadas son latitud/longitud reales de Cusco.
    """
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float

    def contiene(self, lat: float, lon: float) -> bool:
        """O(1) — verifica si un punto cae dentro del rectángulo."""
        return (self.lat_min <= lat <= self.lat_max and
                self.lon_min <= lon <= self.lon_max)

    def centro(self) -> tuple[float, float]:
        """Retorna el centroide del rectángulo."""
        return ((self.lat_min + self.lat_max) / 2,
                (self.lon_min + self.lon_max) / 2)

    def area_aprox_m2(self) -> float:
        """Área aproximada en m² usando conversión 1°lat≈111km."""
        altura_m = (self.lat_max - self.lat_min) * 111_000
        ancho_m  = (self.lon_max - self.lon_min) * 111_000
        return abs(altura_m * ancho_m)

    def dividir_en_4(self) -> tuple["BoundingBox", "BoundingBox",
                                    "BoundingBox", "BoundingBox"]:
        """
        Divide el rectángulo en 4 cuadrantes iguales.
        Retorna: (NE, NO, SE, SO)
        O(1)
        """
        lat_mid = (self.lat_min + self.lat_max) / 2
        lon_mid = (self.lon_min + self.lon_max) / 2

        NE = BoundingBox(lat_mid, self.lat_max, lon_mid, self.lon_max)
        NO = BoundingBox(lat_mid, self.lat_max, self.lon_min, lon_mid)
        SE = BoundingBox(self.lat_min, lat_mid, lon_mid, self.lon_max)
        SO = BoundingBox(self.lat_min, lat_mid, self.lon_min, lon_mid)

        return NE, NO, SE, SO

    def __repr__(self) -> str:
        return (f"BBox(lat[{self.lat_min:.4f}→{self.lat_max:.4f}], "
                f"lon[{self.lon_min:.4f}→{self.lon_max:.4f}])")


# ─────────────────────────────────────────────────────────────
#  Nodo del árbol de partición
# ─────────────────────────────────────────────────────────────

@dataclass
class ZonaParticion:
    """
    Nodo del árbol cuaternario de partición del mapa.

    Cada nodo es:
      - Interno  : tiene 4 hijos (NE, NO, SE, SO), no tiene pedidos.
      - Hoja     : no tiene hijos, contiene la lista de pedidos de esa zona.
    """
    bbox       : BoundingBox
    nombre     : str
    profundidad: int                          = 0
    pedidos    : list[Pedido]                 = field(default_factory=list)
    hijos      : list["ZonaParticion"]        = field(default_factory=list)
    repartidor : Optional[Repartidor]         = None   # asignado en fase 2

    @property
    def es_hoja(self) -> bool:
        return len(self.hijos) == 0

    @property
    def total_pedidos(self) -> int:
        """Pedidos en esta zona y todos sus descendientes."""
        if self.es_hoja:
            return len(self.pedidos)
        return sum(h.total_pedidos for h in self.hijos)

    def zonas_hoja(self) -> list["ZonaParticion"]:
        """Retorna todas las zonas hoja del subárbol."""
        if self.es_hoja:
            return [self]
        hojas = []
        for h in self.hijos:
            hojas.extend(h.zonas_hoja())
        return hojas

    def __repr__(self) -> str:
        tipo = "HOJA" if self.es_hoja else "NODO"
        return (f"Zona({tipo} | {self.nombre} | "
                f"prof={self.profundidad} | "
                f"pedidos={self.total_pedidos})")


# ─────────────────────────────────────────────────────────────
#  1. PARTICIONADOR RECURSIVO
# ─────────────────────────────────────────────────────────────

class ParticionadorCuadrantes:
    """
    Divide el mapa de Cusco recursivamente en cuadrantes hasta que
    cada zona hoja tenga ≤ umbral_pedidos pedidos o se alcance
    la profundidad máxima.

    Complejidad:
        T(n) = 4·T(n/4) + O(n)  →  O(n log n)
        donde n = número total de pedidos.

    Espacio: O(n log n) — cada pedido aparece una vez por nivel.
    """

    # Bounding box real del centro de Cusco (con margen)
    BBOX_CUSCO = BoundingBox(
        lat_min = -13.5420,
        lat_max = -13.5020,
        lon_min = -72.0200,
        lon_max = -71.9500,
    )

    NOMBRES_CUADRANTES = ["NE", "NO", "SE", "SO"]

    def __init__(self,
                 umbral_pedidos: int = 3,
                 max_profundidad: int = 3):
        """
        Args:
            umbral_pedidos  : Máximo de pedidos por zona hoja antes de dividir.
            max_profundidad : Profundidad máxima del árbol (evita recursión infinita).
        """
        self.umbral_pedidos  = umbral_pedidos
        self.max_profundidad = max_profundidad

    def particionar(self,
                    pedidos: list[Pedido],
                    bbox: Optional[BoundingBox] = None,
                    nombre: str = "Cusco",
                    profundidad: int = 0) -> ZonaParticion:
        """
        Divide recursivamente los pedidos en cuadrantes.

        Algoritmo Divide y Vencerás:
          BASE: si len(pedidos) ≤ umbral o profundidad == max → zona hoja
          DIVIDE: partir bbox en 4 cuadrantes
          DISTRIBUYE: asignar cada pedido al cuadrante que lo contiene O(n)
          CONQUISTA: llamar recursivamente a cada cuadrante  4×T(n/4)
          COMBINA: retornar el nodo con 4 hijos               O(1)

        Returns:
            Raíz del árbol de partición.
        """
        if bbox is None:
            bbox = self.BBOX_CUSCO

        zona = ZonaParticion(bbox=bbox, nombre=nombre,
                             profundidad=profundidad)

        # ── CASO BASE ─────────────────────────────────────────
        if (len(pedidos) <= self.umbral_pedidos or
                profundidad >= self.max_profundidad):
            zona.pedidos = list(pedidos)
            return zona

        # ── DIVIDIR bbox en 4 cuadrantes ─────────────────────
        sub_bboxes = bbox.dividir_en_4()          # O(1)

        # ── DISTRIBUIR pedidos a su cuadrante ────────────────
        grupos: list[list[Pedido]] = [[] for _ in range(4)]
        sin_zona: list[Pedido] = []

        for p in pedidos:                         # O(n)
            asignado = False
            for i, sb in enumerate(sub_bboxes):
                if sb.contiene(p.latitud, p.longitud):
                    grupos[i].append(p)
                    asignado = True
                    break
            if not asignado:
                sin_zona.append(p)                # pedido fuera del bbox

        # Pedidos sin zona van al cuadrante más cercano por centroide
        for p in sin_zona:
            mejor_i   = 0
            mejor_d   = float("inf")
            for i, sb in enumerate(sub_bboxes):
                clat, clon = sb.centro()
                d = math.sqrt((p.latitud - clat)**2 + (p.longitud - clon)**2)
                if d < mejor_d:
                    mejor_d = d
                    mejor_i = i
            grupos[mejor_i].append(p)

        # ── CONQUISTAR recursivamente ─────────────────────────
        for i, (sb, grupo) in enumerate(zip(sub_bboxes, grupos)):
            nombre_hijo = f"{nombre}_{self.NOMBRES_CUADRANTES[i]}"
            hijo = self.particionar(
                pedidos     = grupo,
                bbox        = sb,
                nombre      = nombre_hijo,
                profundidad = profundidad + 1,
            )
            if hijo.total_pedidos > 0:          # no agregar zonas vacías
                zona.hijos.append(hijo)

        # Si todos los pedidos cayeron en la misma sub-zona (edge case),
        # convertir en hoja para evitar recursión infinita
        if len(zona.hijos) <= 1:
            zona.hijos.clear()
            zona.pedidos = list(pedidos)

        return zona

    def imprimir_arbol(self, zona: ZonaParticion, indent: int = 0):
        """Imprime el árbol de partición de forma legible."""
        pref = "  " * indent
        tipo = "📦 HOJA" if zona.es_hoja else "🗂  NODO"
        rep  = (f"[{', '.join(p.id_pedido for p in zona.pedidos)}]"
                if zona.es_hoja and zona.pedidos else "")
        print(f"{pref}{tipo} {zona.nombre:<30} "
              f"pedidos={zona.total_pedidos}  {rep}")
        for h in zona.hijos:
            self.imprimir_arbol(h, indent + 1)


# ─────────────────────────────────────────────────────────────
#  2. ASIGNADOR DE ZONAS A REPARTIDORES
# ─────────────────────────────────────────────────────────────

@dataclass
class ResultadoDivideVenceras:
    """Resultado completo del algoritmo Divide y Vencerás."""
    arbol_particion : ZonaParticion
    asignaciones    : dict[str, list[Pedido]]  = field(default_factory=dict)
    # { id_repartidor → [pedidos de su zona] }
    zonas_sin_rep   : list[ZonaParticion]      = field(default_factory=list)

    def resumen(self) -> str:
        lineas = ["── Asignación por Divide y Vencerás ──"]
        for rep_id, peds in self.asignaciones.items():
            ids = [p.id_pedido for p in peds]
            lineas.append(f"  {rep_id}: {ids}")
        if self.zonas_sin_rep:
            sin = [z.nombre for z in self.zonas_sin_rep]
            lineas.append(f"  Sin repartidor: {sin}")
        return "\n".join(lineas)

    def to_dict(self) -> dict:
        return {
            "asignaciones": {
                rep_id: [p.id_pedido for p in peds]
                for rep_id, peds in self.asignaciones.items()
            },
            "zonas_sin_repartidor": [z.nombre for z in self.zonas_sin_rep],
        }


class AsignadorZonas:
    """
    Fase 2 de Divide y Vencerás:
    Toma el árbol de partición y asigna cada zona hoja al repartidor
    cuyo sector_asignado coincida, o al más cercano al centroide.

    Complejidad: O(z × r)
    donde z = zonas hoja, r = repartidores
    """

    def asignar(self,
                raiz: ZonaParticion,
                repartidores: list[Repartidor]) -> ResultadoDivideVenceras:
        """
        Asigna zonas hoja a repartidores.

        Estrategia:
          1. Intentar asignación por sector_asignado (nombre de zona).
          2. Si no coincide, asignar al repartidor más cercano al centroide.
          3. Un repartidor puede recibir múltiples zonas si hay más
             zonas que repartidores.

        O(z × r)
        """
        hojas     = raiz.zonas_hoja()
        resultado = ResultadoDivideVenceras(arbol_particion=raiz)

        # Inicializar dict de asignaciones
        for r in repartidores:
            resultado.asignaciones[r.id_repartidor] = []

        reps_disponibles = list(repartidores)

        for zona in hojas:
            if not zona.pedidos:
                continue

            rep_elegido = self._elegir_repartidor(zona, reps_disponibles)

            if rep_elegido is None:
                resultado.zonas_sin_rep.append(zona)
                continue

            zona.repartidor = rep_elegido
            resultado.asignaciones[rep_elegido.id_repartidor].extend(
                zona.pedidos
            )

        return resultado

    def _elegir_repartidor(self,
                            zona: ZonaParticion,
                            repartidores: list[Repartidor]
                            ) -> Optional[Repartidor]:
        """
        Elige el repartidor más apropiado para una zona.
        Prioridad: sector coincidente > más cercano al centroide.
        O(r)
        """
        clat, clon = zona.bbox.centro()

        # Intentar match por nombre de sector
        for rep in repartidores:
            if (rep.sector_asignado and
                    rep.sector_asignado.lower() in zona.nombre.lower()):
                return rep

        # Fallback: más cercano al centroide de la zona
        mejor_rep  = None
        mejor_dist = float("inf")

        for rep in repartidores:
            d = math.sqrt(
                (rep.latitud_actual  - clat) ** 2 +
                (rep.longitud_actual - clon) ** 2
            )
            if d < mejor_dist:
                mejor_dist = d
                mejor_rep  = rep

        return mejor_rep


# ─────────────────────────────────────────────────────────────
#  3. MERGE SORT ESPACIAL (auxiliar)
#     Ordena pedidos por coordenada antes del particionado.
#     Mejora la distribución en casos con pedidos concentrados.
# ─────────────────────────────────────────────────────────────

def merge_sort_espacial(pedidos: list[Pedido],
                        eje: str = "lat") -> list[Pedido]:
    """
    Ordena pedidos por latitud o longitud usando Merge Sort.
    Usado como preproceso opcional para el particionado.

    Args:
        pedidos : Lista de pedidos.
        eje     : "lat" (norte-sur) o "lon" (este-oeste).

    Complejidad: O(n log n)
    """
    if len(pedidos) <= 1:
        return pedidos[:]

    medio = len(pedidos) // 2
    izq   = merge_sort_espacial(pedidos[:medio], eje)
    der   = merge_sort_espacial(pedidos[medio:], eje)

    return _merge_espacial(izq, der, eje)


def _merge_espacial(izq: list[Pedido],
                    der: list[Pedido],
                    eje: str) -> list[Pedido]:
    resultado = []
    i = j = 0
    while i < len(izq) and j < len(der):
        val_i = izq[i].latitud  if eje == "lat" else izq[i].longitud
        val_j = der[j].latitud  if eje == "lat" else der[j].longitud
        if val_i <= val_j:
            resultado.append(izq[i]); i += 1
        else:
            resultado.append(der[j]); j += 1
    resultado.extend(izq[i:])
    resultado.extend(der[j:])
    return resultado


# ─────────────────────────────────────────────────────────────
#  4. PIPELINE COMPLETO: particionar + asignar + rutas internas
# ─────────────────────────────────────────────────────────────

def ejecutar_divide_venceras(
        pedidos      : list[Pedido],
        repartidores : list[Repartidor],
        grafo        : Grafo,
        umbral       : int = 3,
        max_prof     : int = 3,
) -> ResultadoDivideVenceras:
    """
    Pipeline completo de Divide y Vencerás:
      1. Particionar mapa en cuadrantes.          O(n log n)
      2. Asignar zonas a repartidores.            O(z × r)
      3. Calcular ruta Greedy por zona.           O(k²) por zona

    Args:
        pedidos      : Pedidos pendientes.
        repartidores : Repartidores disponibles.
        grafo        : Mapa de Cusco.
        umbral       : Pedidos máx por zona hoja.
        max_prof     : Profundidad máxima de recursión.

    Returns:
        ResultadoDivideVenceras con árbol y asignaciones.
    """
    from algoritmos.greedy import NearestNeighborGreedy

    # Paso 1: Particionar
    particionador = ParticionadorCuadrantes(umbral, max_prof)
    arbol = particionador.particionar(pedidos)

    # Paso 2: Asignar zonas
    asignador  = AsignadorZonas()
    resultado  = asignador.asignar(arbol, repartidores)

    # Paso 3: Ruta Greedy interna por zona (subproblema reducido)
    nn = NearestNeighborGreedy(grafo)
    for rep in repartidores:
        peds_zona = resultado.asignaciones.get(rep.id_repartidor, [])
        if peds_zona:
            # Resetear estados para que Greedy los procese
            for p in peds_zona:
                p.estado = p.estado  # mantener estado actual
            nn.construir_ruta(rep, peds_zona)

    return resultado