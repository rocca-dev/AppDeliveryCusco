# Sistema de Gestión de Rutas Óptimas — Cusco

**UNSAAC · Programación III** — Sistema de reparto con 5 algoritmos: Merge Sort, Greedy, Divide y Vencerás, Programación Dinámica (Knapsack 0/1 + Dijkstra), Backtracking.

## Instalación

```bash
pip install -r requirements.txt
```

## Arranque

```bash
python Main.py
# o directamente:
uvicorn api.main:app --reload --port 8000
```

## URLs

| URL | Descripción |
|-----|-------------|
| http://localhost:8000 | Interfaz web (GUI) |
| http://localhost:8000/docs | Swagger UI (documentación API) |
| http://localhost:8000/health | Estado del sistema |

## Estructura del proyecto

```
AppDelivery/
├── README.md
├── requirements.txt
├── Main.py                      # Punto de entrada
├── datos/                       # Datos JSON (mapa, pedidos, repartidores)
├── modelos/                     # Clases del dominio (Grafo, Pedido, Repartidor)
├── algoritmos/                  # Implementación de los 5 algoritmos
│   ├── ordenacion.py            # Merge Sort O(n log n)
│   ├── busqueda.py              # Búsqueda Binaria O(log n) + Hash Map O(1)
│   ├── greedy.py                # Nearest Neighbor O(n²) + Asignación O(p×r)
│   ├── divide_venceras.py       # Particionado cuaternario O(n log n)
│   ├── programacion_dinamica.py # Knapsack 0/1 O(n×W) + Dijkstra O((V+E)logV)
│   ├── backtracking.py          # DFS con poda O(b^d)
│   └── benchmark_*.py           # Benchmarks individuales
├── api/                         # API REST (FastAPI)
│   ├── main.py                  # Configuración de la app
│   ├── estado.py                # Estado global del sistema
│   ├── schemas.py               # Pydantic request/response models
│   └── routers/                 # Endpoints
│       ├── pedidos.py           # /pedidos
│       ├── algoritmos.py        # /algoritmos
│       └── mapa.py              # /mapa
├── gui/                         # Frontend web (Leaflet + vanilla JS)
│   ├── index.html
│   ├── estilos.css
│   ├── algoritmos.js
│   └── mapa.js
└── tests/                       # Pruebas unitarias
    ├── test_ordenacion.py
    ├── test_greedy.py
    ├── test_dinamica.py
    └── test_backtracking.py
```

## Algoritmos implementados

| Módulo | Archivo | Complejidad |
|--------|---------|-------------|
| Merge Sort | `ordenacion.py` | O(n log n) |
| Búsqueda Binaria | `busqueda.py` | O(log n) |
| Hash Map | `busqueda.py` | O(1) |
| Greedy (Nearest Neighbor) | `greedy.py` | O(n²) |
| Asignación Greedy | `greedy.py` | O(p × r) |
| Divide y Vencerás | `divide_venceras.py` | O(n log n) |
| Knapsack 0/1 | `programacion_dinamica.py` | O(n × W) |
| Dijkstra + memo | `programacion_dinamica.py` | O((V+E) log V) |
| Backtracking con podas | `backtracking.py` | O(b^d) |

## Benchmarks

```bash
python -m algoritmos.benchmark_ordenacion
python -m algoritmos.benchmark_greedy
python -m algoritmos.benchmark_divide_venceras
python -m algoritmos.benchmark_pd
python -m algoritmos.benchmark_backtracking
```

## Tests

```bash
python -m pytest tests/ -v
```
