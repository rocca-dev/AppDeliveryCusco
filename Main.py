"""
Main.py — Punto de Entrada del Sistema de Rutas Óptimas — Cusco v2
===================================================================
Arranque:
    python Main.py

O directamente con uvicorn (modo desarrollo):
    uvicorn api.main:app --reload --port 8000

Cambios v2:
  - Informa versión 2.0.0 al arrancar.
  - Agrega hint de /info para ver el resumen de arquitectura.
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 55)
    print("  Sistema de Rutas Optimas - Cusco  v2.0.0")
    print("  http://localhost:8000       (interfaz web)")
    print("  http://localhost:8000/docs  (Swagger API)")
    print("  http://localhost:8000/info  (arquitectura)")
    print("=" * 55)
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
