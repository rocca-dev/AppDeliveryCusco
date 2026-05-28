/**
 * state.js — Estado compartido y utilidades del frontend
 * =======================================================
 * 
 * Módulo central que mantiene el estado global (pedidos, grafo,
 * benchmarks) y expone utilidades de UI (toast, API wrapper,
 * renderizado de pedidos, tabs, benchmarks).
 * 
 * Las variables de estado se exportan como let bindings en vivo:
 * cualquier módulo que las importe verá los cambios automáticamente.
 * 
 * Dependencias: Ninguna (módulo raíz)
 */

// ─────────────────────────────────────────────────────────────
//  Estado global (mutable, live bindings)
// ─────────────────────────────────────────────────────────────

/** Datos del grafo (nodos + aristas) desde la API */
export let grafoData = null;

/** Lista actual de pedidos en formato API dict */
export let pedidosData = [];

/** Registro de benchmarks { nombre: { ms, nota } } */
export const benchTiempos = {};


// ─────────────────────────────────────────────────────────────
//  Setters (mantienen sincronía con window para onclick)
// ─────────────────────────────────────────────────────────────

/** Actualiza grafoData y sincroniza a window. */
export function setGrafoData(data) { grafoData = data; window.grafoData = data; }

/** Actualiza pedidosData y sincroniza a window. */
export function setPedidosData(data) { pedidosData = data; window.pedidosData = data; }


// ─────────────────────────────────────────────────────────────
//  Utilidades
// ─────────────────────────────────────────────────────────────

/**
 * Muestra una notificación toast temporal en la parte inferior.
 * @param {string} msg   - Mensaje a mostrar
 * @param {string} color - Color CSS del borde (default #c9a84c dorado)
 */
export function toast(msg, color = '#c9a84c') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.style.borderColor = color;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2800);
}

/**
 * Activa/desactiva el spinner de carga en un botón.
 * Guarda el HTML original en _orig para restaurarlo después.
 * 
 * @param {string}  id      - ID del botón
 * @param {boolean} loading - true = mostrar spinner, false = restaurar
 */
export function btnLoading(id, loading) {
  const b = document.getElementById(id);
  if (!b) return;
  if (loading) {
    b._orig = b.innerHTML;
    b.innerHTML = '<span class="spinner"></span> Calculando...';
    b.disabled = true;
  } else {
    b.innerHTML = b._orig || b.innerHTML;
    b.disabled = false;
  }
}

/**
 * Retorna el color CSS asociado a un nivel de prioridad.
 * @param {string} p - Prioridad (URGENTE|ALTA|MEDIA|BAJA)
 * @returns {string} Código hexadecimal
 */
export function prioColor(p) {
  const colores = { URGENTE: '#e74c3c', ALTA: '#f39c12', MEDIA: '#3dd6f5', BAJA: '#6b7280' };
  return colores[p] || '#ffffff';
}

/**
 * Wrapper de fetch para llamadas a la API REST del backend.
 * 
 * - Serializa body automáticamente a JSON.
 * - Setea Content-Type: application/json.
 * - Parsea la respuesta JSON.
 * - Lanza Error con detail si la respuesta no es OK.
 * 
 * @param {string} method - HTTP method (GET | POST | ...)
 * @param {string} path   - Ruta del endpoint (ej. /pedidos/)
 * @param {Object} [body] - Cuerpo opcional (se serializa a JSON)
 * @returns {Promise<Object>} Respuesta parseada
 * @throws {Error} Si la respuesta HTTP tiene código de error
 */
export async function api(method, path, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}

/**
 * Recarga pedidosData desde la API y refresca la lista en pantalla.
 * Útil después de ejecutar algoritmos que modifican estados.
 */
export async function recargarPedidos() {
  const data = await api('GET', '/pedidos/');
  setPedidosData(data);
  renderizarPedidos(data);
}


// ─────────────────────────────────────────────────────────────
//  Renderizado de pedidos (panel izquierdo)
// ─────────────────────────────────────────────────────────────

/**
 * Renderiza la lista de pedidos como tarjetas en el panel lateral.
 * Cada tarjeta muestra ID, cliente, sector, peso, valor, prioridad y estado.
 * 
 * @param {Object[]} pedidos - Lista de objetos pedido (formato API /pedidos/)
 */
export function renderizarPedidos(pedidos) {
  const cont = document.getElementById('lista-pedidos');
  if (!cont) return;
  if (!pedidos || !pedidos.length) {
    cont.innerHTML = '<div style="color:var(--text-dim);font-size:11px;text-align:center;padding:20px">Sin pedidos</div>';
    return;
  }
  cont.innerHTML = pedidos.map(p => `
    <div class="pedido-card" onclick="seleccionarPedido('${p.id_pedido}')">
      <div class="pid">
        <span>${p.id_pedido}</span>
        <span class="prioridad-badge prio-${p.prioridad}">${p.prioridad}</span>
      </div>
      <div class="pname">${p.cliente}</div>
      <div class="pmeta">${p.sector} · ${p.peso_kg}kg · S/.${p.valor}</div>
      <div class="pmeta" style="color:var(--text-dim)">${p.estado}</div>
    </div>`).join('');
}


// ─────────────────────────────────────────────────────────────
//  Navegación por pestañas (tabs)
// ─────────────────────────────────────────────────────────────

/**
 * Configura los manejadores de click para las pestañas del panel.
 * Cada .tab con data-tab="X" alterna la visibilidad de #tab-X.
 * Soporta múltiples grupos de tabs (panel izquierdo y derecho).
 */
export function iniciarTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const group = tab.parentElement;
      const panel = tab.closest('#panel-left, #panel-right');
      if (!panel) return;
      group.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const name = tab.dataset.tab;
      panel.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
      const target = panel.querySelector(`#tab-${name}`);
      if (target) target.style.display = 'flex';
    });
  });
}


// ─────────────────────────────────────────────────────────────
//  Benchmarks (panel derecho, pestaña Big-O)
// ─────────────────────────────────────────────────────────────

/**
 * Registra el tiempo de ejecución de un algoritmo en el panel
 * de benchmarks comparativos (pestaña Big-O).
 * 
 * @param {string} nombre - Nombre del algoritmo
 * @param {number|string} ms - Milisegundos de ejecución
 * @param {string} nota - Descripción (complejidad, detalles)
 */
export function registrarBench(nombre, ms, nota) {
  benchTiempos[nombre] = { ms: parseFloat(ms), nota };
  _renderizarBench();
}

/** Renderiza la tabla de benchmarks ordenada por tiempo ascendente. */
function _renderizarBench() {
  const cont = document.getElementById('benchmark-resultados');
  if (!cont) return;
  const items = Object.entries(benchTiempos).sort((a, b) => a[1].ms - b[1].ms);
  if (!items.length) {
    cont.innerHTML = '<div style="color:var(--text-dim);font-size:11px">Ejecuta algoritmos para ver tiempos reales.</div>';
    return;
  }
  const max = Math.max(...items.map(x => x[1].ms));
  cont.innerHTML = items.map(([nombre, { ms, nota }]) => {
    const pct   = max > 0 ? (ms / max * 100).toFixed(1) : 0;
    const color = ms < 1 ? '#2ecc71' : ms < 10 ? '#f39c12' : '#e74c3c';
    return `<div style="margin-bottom:10px">
      <div style="display:flex;justify-content:space-between;font-size:10px;margin-bottom:3px">
        <span style="color:var(--text)">${nombre}</span>
        <span style="color:${color};font-family:var(--mono)">${ms}ms</span>
      </div>
      <div style="height:4px;background:var(--border);border-radius:2px">
        <div style="height:100%;width:${pct}%;background:${color};border-radius:2px;transition:width .4s"></div>
      </div>
      <div style="font-size:9px;color:var(--text-dim);margin-top:2px">${nota}</div>
    </div>`;
  }).join('');
}
