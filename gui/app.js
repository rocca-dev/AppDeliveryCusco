/**
 * app.js — Punto de entrada del frontend
 * =======================================
 * 
 * Importa y coordina todos los módulos de la interfaz.
 * 
 * Responsabilidades:
 *   1. Inicializar estado, tabs y mapa
 *   2. Cargar datos iniciales (grafo, pedidos, health)
 *   3. Exponer funciones al ámbito global (window) para
 *      compatibilidad con atributos onclick en el HTML
 *   4. Poblar los selectores de nodos en los formularios
 * 
 * Orden de arranque (DOMContentLoaded):
 *   iniciarTabs() → iniciarMapa() → cargarTodo()
 * 
 * Dependencias:
 *   state.js      → estado, api, toast, setGrafoData, setPedidosData,
 *                   renderizarPedidos, iniciarTabs, recargarPedidos
 *   mapa.js       → iniciarMapa, dibujarGrafo
 *   algoritmos.js → todas las funciones de ejecución
 */

import {
  api, toast, setGrafoData, setPedidosData,
  renderizarPedidos, iniciarTabs, recargarPedidos, grafoData,
} from './state.js';
import { iniciarMapa, dibujarGrafo, centrarEn } from './mapa.js';
import {
  ejecutarGreedy,
  ejecutarDV,
  ejecutarKnapsack,
  ejecutarBacktracking,
  calcularRutaOptima,
  bloquearCalle,
  ordenarPedidos,
  buscarPedido,
  resetearSistema,
  ejecutarTodos,
  mostrarRutaRepartidor,
} from './algoritmos.js';


// ─────────────────────────────────────────────────────────────
//  Exposición global (para onclick="" en HTML)
// ─────────────────────────────────────────────────────────────

// Algoritmos
window.ejecutarGreedy       = ejecutarGreedy;
window.ejecutarDV           = ejecutarDV;
window.ejecutarKnapsack     = ejecutarKnapsack;
window.ejecutarBacktracking = ejecutarBacktracking;
window.calcularRutaOptima   = calcularRutaOptima;
window.bloquearCalle        = bloquearCalle;
window.ordenarPedidos       = ordenarPedidos;
window.buscarPedido         = buscarPedido;
window.resetearSistema      = resetearSistema;
window.ejecutarTodos        = ejecutarTodos;
window.mostrarRutaRepartidor = mostrarRutaRepartidor;

// UI
window.seleccionarPedido    = seleccionarPedido;


// ─────────────────────────────────────────────────────────────
//  Funciones expuestas
// ─────────────────────────────────────────────────────────────

/**
 * Centra el mapa en un pedido cuando se hace click en su tarjeta.
 * @param {string} id - ID del pedido (ej. "P003")
 */
function seleccionarPedido(id) {
  // Buscar en pedidosData (está en window gracias al sync de state.js)
  const p = (window.pedidosData || []).find(x => x.id_pedido === id);
  if (!p || !p.latitud) return;
  centrarEn(p.latitud, p.longitud, 16);
  toast(`📦 ${p.id_pedido} — ${p.cliente} (${p.sector})`);
}


// ─────────────────────────────────────────────────────────────
//  Carga inicial de datos
// ─────────────────────────────────────────────────────────────

/**
 * Carga los datos iniciales del sistema desde la API:
 *   1. Health check (actualiza indicador y badge de stats)
 *   2. Grafo del mapa (dibuja nodos y aristas)
 *   3. Pedidos (renderiza lista en panel izquierdo)
 */
async function cargarTodo() {
  // ── Health check ──────────────────────────────────────────
  try {
    const h = await api('GET', '/health');
    document.getElementById('health-dot').className = 'ok';
    document.getElementById('stats-badge').textContent =
      `${h.pedidos_total} pedidos · ${h.repartidores} repartidores · ${h.nodos_grafo} nodos`;
  } catch {
    document.getElementById('health-dot').className = 'err';
    toast('No se pudo conectar con el servidor', '#e74c3c');
  }

  // ── Grafo ─────────────────────────────────────────────────
  try {
    const g = await api('GET', '/mapa/grafo');
    setGrafoData(g);
    dibujarGrafo(g);
    poblarSelectNodos(g.nodos);
  } catch (e) { toast('Error cargando grafo: ' + e.message, '#e74c3c'); }

  // ── Pedidos ───────────────────────────────────────────────
  try {
    const p = await api('GET', '/pedidos/');
    setPedidosData(p);
    renderizarPedidos(p);
  } catch (e) { toast('Error cargando pedidos: ' + e.message, '#e74c3c'); }
}


// ─────────────────────────────────────────────────────────────
//  Poblar selects de nodos
// ─────────────────────────────────────────────────────────────

/**
 * Llena los menús desplegables de selección de nodos en los
 * paneles de bloqueo de calles, ruta óptima y backtracking.
 * 
 * @param {Object[]} nodos - Lista de nodos del grafo { id_nodo, nombre, sector }
 */
function poblarSelectNodos(nodos) {
  const selects = [
    '#blq-origen', '#blq-destino',
    '#rt-origen', '#rt-destino',
    '#bt-origen', '#bt-destino',
  ];
  selects.forEach(sel => {
    const el = document.querySelector(sel);
    if (!el) return;
    const placeholder = el.options[0]?.text || 'Seleccionar...';
    el.innerHTML = `<option value="">${placeholder}</option>`;
    nodos.forEach(n => {
      el.innerHTML += `<option value="${n.id_nodo}">${n.nombre} (${n.sector})</option>`;
    });
  });
}


// ─────────────────────────────────────────────────────────────
//  Arranque
// ─────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  iniciarTabs();
  iniciarMapa();
  cargarTodo();
});
