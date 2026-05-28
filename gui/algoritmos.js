/**
 * algoritmos.js — Ejecución de algoritmos de optimización
 * =======================================================
 * 
 * Coordina las llamadas a los endpoints de la API REST para
 * ejecutar los algoritmos del sistema y muestra los resultados
 * en el panel derecho.
 * 
 * Cada función sigue el patrón:
 *   1. Activar spinner del botón
 *   2. Llamar a la API (medir tiempo con performance.now)
 *   3. Renderizar resultado en #resultado-algoritmo
 *   4. Registrar benchmark en la pestaña Big-O
 *   5. Recargar lista de pedidos (si el algoritmo los modificó)
 * 
 * Dependencias:
 *   state.js  → api, toast, btnLoading, registrarBench, recargarPedidos,
 *                setGrafoData, setPedidosData, renderizarPedidos
 *   mapa.js   → dibujarRutaEnMapa, limpiarRuta
 */

const REP_COLORS = ['#3dd6f5', '#2ecc71', '#f39c12', '#9b59b6', '#e74c3c', '#e91e63'];

import {
  api, toast, btnLoading, registrarBench,
  recargarPedidos, setGrafoData, setPedidosData,
  renderizarPedidos, grafoData,
} from './state.js';
import { dibujarRutaEnMapa, limpiarRuta, centrarEn, capaRuta, mapaLeaflet } from './mapa.js';


// ─────────────────────────────────────────────────────────────
//  Mostrar ruta de un repartidor en el mapa
// ─────────────────────────────────────────────────────────────

/**
 * GET /repartidores/{id}/ruta
 *
 * Obtiene la ruta completa de un repartidor (posición actual →
 * nodo más cercano → cada pedido asignado vía Dijkstra) y la
 * dibuja en el mapa con colores por segmento.
 *
 * @param {string} id - ID del repartidor (ej. "R01")
 * @param {string} color - Color CSS para la ruta
 */
export async function mostrarRutaRepartidor(id, color = '#3dd6f5') {
  limpiarRuta();
  try {
    const ruta = await api('GET', `/repartidores/${id}/ruta`);

    if (!ruta.segmentos || ruta.segmentos.length === 0) {
      toast(`📭 ${ruta.nombre} no tiene pedidos asignados para ruteo`, '#f39c12');
      return;
    }

    // Dibujar cada segmento en el mapa
    const todosPuntos = [];
    ruta.segmentos.forEach((seg, i) => {
      const coords = seg.camino.map(n => {
        const nodo = grafoData.nodos.find(x => x.id_nodo === n);
        return nodo ? [nodo.latitud, nodo.longitud] : null;
      }).filter(Boolean);
      todosPuntos.push(...coords);

      const segColor = REP_COLORS[i % REP_COLORS.length];
      L.polyline(coords, { color: segColor, weight: 5, opacity: 0.85, dashArray: '8,4' })
        .addTo(capaRuta);

      // Marcador del pedido destino
      if (coords.length) {
        L.circleMarker(coords[coords.length - 1], {
          radius: 8, color: segColor, fillColor: '#fff', fillOpacity: 0.9, weight: 3,
        }).bindPopup(`<b>${seg.id_pedido}</b><br>${seg.camino[seg.camino.length-1]}<br>${seg.distancia_m.toFixed(0)} m`).addTo(capaRuta);
      }
    });

    // Marcador del repartidor (inicio)
    if (todosPuntos.length) {
      L.circleMarker(todosPuntos[0], {
        radius: 10, color: color, fillColor: color, fillOpacity: 0.6, weight: 3,
      }).bindPopup(`<b>${ruta.nombre}</b><br>📍 Inicio`).addTo(capaRuta);
    }

    // Ajustar zoom
    const bounds = L.latLngBounds(todosPuntos);
    mapaLeaflet.fitBounds(bounds, { padding: [50, 50] });

    // Mostrar info de ruta en el panel
    let html = `<div class="result-block" style="border-left:4px solid ${color};margin-top:8px">
      <div class="rb-title" style="color:${color}">🚚 ${ruta.nombre} · Ruta (${ruta.segmentos.length} pedidos)</div>`;

    ruta.segmentos.forEach(seg => {
      html += `<div class="rb-row" style="font-size:11px">
        <span>📍 ${seg.id_pedido}</span>
        <span>${seg.distancia_m.toFixed(0)} m · ${seg.tiempo_min.toFixed(1)} min</span>
      </div>`;
    });

    html += `<div class="rb-row" style="border-top:1px solid var(--border);padding-top:6px;margin-top:4px">
      <span style="font-weight:600">🛣 Total</span>
      <span style="font-weight:600;color:${color}">${ruta.distancia_total_m.toFixed(0)} m · ${ruta.tiempo_total_min.toFixed(1)} min</span>
    </div></div>`;

    const container = document.getElementById('resultado-algoritmo');
    container.insertAdjacentHTML('beforeend', html);
    toast(`🗺 Ruta de ${ruta.nombre}: ${ruta.distancia_total_m.toFixed(0)} m, ${ruta.tiempo_total_min.toFixed(1)} min`);
  } catch (e) {
    toast(`Error al cargar ruta de ${id}: ${e.message}`, '#e74c3c');
  }
}


// ─────────────────────────────────────────────────────────────
//  Greedy — Asignación masiva (Nearest Neighbor)
// ─────────────────────────────────────────────────────────────

/**
 * POST /algoritmos/greedy/asignacion
 * 
 * Asigna pedidos a repartidores usando el algoritmo del vecino
 * más cercano. Limpia el estado previo (resetear_estado: true).
 * 
 * Complejidad: O(p × r) — p = pedidos, r = repartidores
 * Tiempo:     O(p²/r) con distribución uniforme
 */
export async function ejecutarGreedy() {
  btnLoading('btn-greedy', true);
  try {
    const t0  = performance.now();
    const res = await api('POST', '/algoritmos/greedy/asignacion', { resetear_estado: true });
    const ms  = (performance.now() - t0).toFixed(2);

    let html = `<div class="metric-row">
      <div class="metric"><div class="mv">${res.total_asignados}</div><div class="ml">Asignados</div></div>
      <div class="metric"><div class="mv">${ms}ms</div><div class="ml">Tiempo</div></div>
    </div>`;

    res.asignaciones.filter(a => a.ruta_pedidos.length).forEach((a, i) => {
      const distKm = (a.distancia_total_m / 1000).toFixed(2);
      const color = REP_COLORS[i % REP_COLORS.length];
      html += `<div class="result-block" style="border-left:4px solid ${color};cursor:pointer"
        onclick="window.mostrarRutaRepartidor('${a.repartidor}')" title="Click para ver ruta en el mapa">
        <div class="rb-title">⚡ ${a.repartidor} <span style="font-size:10px;color:var(--text-dim)">(click para ruta)</span></div>
        <div class="rb-row"><span>Pedidos</span><span>${a.ruta_pedidos.join(', ')}</span></div>
        <div class="rb-row"><span>Distancia</span><span>${distKm} km</span></div>
        <div class="rb-row"><span>Tiempo est.</span><span>${a.tiempo_total_min.toFixed(1)} min</span></div>
        <div class="rb-route">${a.ruta_pedidos.join(' → ')}</div>
      </div>`;
    });

    document.getElementById('resultado-algoritmo').innerHTML = html;
    registrarBench('Greedy Asignación', ms, `O(p×r) · ${res.total_asignados}/${res.total_pedidos} pedidos`);
    await recargarPedidos();
    toast(`✅ Greedy: ${res.total_asignados}/${res.total_pedidos} pedidos en ${ms}ms`);
  } catch (e) { toast('Error: ' + e.message, '#e74c3c'); }
  finally { btnLoading('btn-greedy', false); }
}


// ─────────────────────────────────────────────────────────────
//  Divide y Vencerás — Partición espacial en cuadrantes
// ─────────────────────────────────────────────────────────────

/**
 * POST /algoritmos/divide-venceras
 * 
 * Particiona el mapa en cuadrantes (noroeste, noreste, suroeste,
 * sureste) recursivamente y asigna cada zona a un repartidor.
 * 
 * Complejidad: O(n log n)
 */
export async function ejecutarDV() {
  btnLoading('btn-dv', true);
  try {
    const t0  = performance.now();
    const res = await api('POST', '/algoritmos/divide-venceras', { umbral_pedidos: 3, max_profundidad: 3 });
    const ms  = (performance.now() - t0).toFixed(2);

    let html = `<div class="metric-row">
      <div class="metric"><div class="mv">${res.zonas_generadas}</div><div class="ml">Zonas</div></div>
      <div class="metric"><div class="mv">${ms}ms</div><div class="ml">Tiempo</div></div>
    </div>`;

    Object.entries(res.asignaciones).forEach(([rep, peds], i) => {
      if (!peds.length) return;
      const color = REP_COLORS[i % REP_COLORS.length];
      html += `<div class="result-block" style="border-left:4px solid ${color};cursor:pointer"
        onclick="window.mostrarRutaRepartidor('${rep}')" title="Click para ver ruta en el mapa">
        <div class="rb-title">🗂 ${rep} <span style="font-size:10px;color:var(--text-dim)">(click para ruta)</span></div>
        <div class="rb-row"><span>Zona asignada</span><span>${peds.join(', ')}</span></div>
        <div class="rb-route">${peds.join(' → ')}</div>
      </div>`;
    });

    document.getElementById('resultado-algoritmo').innerHTML = html;
    registrarBench('Divide y Vencerás', ms, `O(n log n) · ${res.zonas_generadas} zonas`);
    toast(`✅ D&V: ${res.total_asignados} pedidos en ${res.zonas_generadas} zonas — ${ms}ms`);
  } catch (e) { toast('Error: ' + e.message, '#e74c3c'); }
  finally { btnLoading('btn-dv', false); }
}


// ─────────────────────────────────────────────────────────────
//  Knapsack 0/1 — Optimización de carga con PD
// ─────────────────────────────────────────────────────────────

/**
 * POST /algoritmos/knapsack/flota
 * 
 * Optimiza la carga de cada repartidor maximizando el valor total
 * de pedidos, respetando restricciones de peso y volumen.
 * Usa tabulación 2D (programación dinámica).
 * 
 * Complejidad: O(n × W) por repartidor
 *             (n = candidatos, W = capacidad_kg × factor_escala)
 */
export async function ejecutarKnapsack() {
  btnLoading('btn-knapsack', true);
  try {
    const t0  = performance.now();
    const res = await api('POST', '/algoritmos/knapsack/flota', { bonus_urgente: 1.5 });
    const ms  = (performance.now() - t0).toFixed(2);

    let html = `<div class="metric-row">
      <div class="metric"><div class="mv">S/.${res.valor_flota_total}</div><div class="ml">Valor total</div></div>
      <div class="metric"><div class="mv">${ms}ms</div><div class="ml">Tiempo</div></div>
    </div>`;

    res.resultados.filter(r => r.pedidos_elegidos.length).forEach((r, i) => {
      const color = REP_COLORS[i % REP_COLORS.length];
      html += `<div class="result-block" style="border-left:4px solid ${color};cursor:pointer"
        onclick="window.mostrarRutaRepartidor('${r.repartidor}')" title="Click para ver ruta en el mapa">
        <div class="rb-title">🎒 ${r.repartidor} <span style="font-size:10px;color:var(--text-dim)">(click para ruta)</span></div>
        <div class="rb-row"><span>Elegidos</span><span>${r.pedidos_elegidos.join(', ')}</span></div>
        <div class="rb-row"><span>Peso</span><span>${r.peso_total}kg (${r.capacidad_usada_pct}%)</span></div>
        <div class="rb-row"><span>Valor</span><span style="color:var(--green)">S/.${r.valor_total}</span></div>
        <div class="rb-route">${r.pedidos_elegidos.join(' + ')}</div>
      </div>`;
    });

    document.getElementById('resultado-algoritmo').innerHTML = html;
    registrarBench('Knapsack 0/1', ms, `O(n×W) · S/.${res.valor_flota_total} valor máximo`);
    await recargarPedidos();
    toast(`✅ Knapsack: S/.${res.valor_flota_total} valor óptimo en ${ms}ms`);
  } catch (e) { toast('Error: ' + e.message, '#e74c3c'); }
  finally { btnLoading('btn-knapsack', false); }
}


// ─────────────────────────────────────────────────────────────
//  Backtracking — Búsqueda exhaustiva de rutas
// ─────────────────────────────────────────────────────────────

/**
 * POST /algoritmos/backtracking
 * 
 * Busca todas las rutas posibles entre dos nodos del grafo usando
 * backtracking con poda (nodos repetidos, nodos prohibidos, límite
 * de paradas y de rutas). Muestra la ruta más corta en el mapa.
 * 
 * Lee los inputs del DOM: bt-origen, bt-destino, bt-prohibidos.
 * 
 * Complejidad: O(b^d) peor caso (b = branching, d = profundidad)
 *             La poda reduce drásticamente en grafos reales.
 */
export async function ejecutarBacktracking() {
  const origen  = document.getElementById('bt-origen').value;
  const destino = document.getElementById('bt-destino').value;
  if (!origen || !destino) { toast('Selecciona origen y destino para Backtracking', '#f39c12'); return; }

  const prohibText = document.getElementById('bt-prohibidos').value.trim();
  const prohibidos = prohibText ? prohibText.split(',').map(s => s.trim()).filter(Boolean) : [];

  btnLoading('btn-bt', true);
  try {
    const t0  = performance.now();
    const res = await api('POST', '/algoritmos/backtracking', {
      origen, destino, max_paradas: 8, max_rutas: 30,
      nodos_prohibidos: prohibidos, puntos_obligatorios: [],
    });
    const ms = (performance.now() - t0).toFixed(2);

    let html = `<div class="metric-row">
      <div class="metric"><div class="mv">${res.rutas_encontradas}</div><div class="ml">Rutas</div></div>
      <div class="metric"><div class="mv">${res.podas_aplicadas}</div><div class="ml">Podas</div></div>
    </div>
    <div class="metric-row">
      <div class="metric"><div class="mv">${res.nodos_explorados}</div><div class="ml">Nodos exp.</div></div>
      <div class="metric"><div class="mv">${ms}ms</div><div class="ml">Tiempo</div></div>
    </div>`;

    if (res.ruta_mas_corta) {
      dibujarRutaEnMapa(res.ruta_mas_corta.camino, '#2ecc71');
      html += `<div class="result-block">
        <div class="rb-title">📏 Ruta más corta</div>
        <div class="rb-row"><span>Distancia</span><span>${res.ruta_mas_corta.distancia_m.toLocaleString()} m</span></div>
        <div class="rb-row"><span>Tiempo</span><span>${res.ruta_mas_corta.tiempo_min} min</span></div>
        <div class="rb-row"><span>Paradas</span><span>${res.ruta_mas_corta.num_paradas}</span></div>
        <div class="rb-route">${res.ruta_mas_corta.camino.join(' → ')}</div>
      </div>`;
    }

    if (res.todas_las_rutas.length > 1) {
      html += `<div class="result-block"><div class="rb-title">📋 Todas las rutas (${res.todas_las_rutas.length})</div>`;
      res.todas_las_rutas.slice(0, 6).forEach((r, i) => {
        html += `<div class="rb-row" style="font-size:10px;margin-bottom:4px">
          <span>${i + 1}. ${r.camino.join('→')}</span>
          <span style="color:var(--green);margin-left:8px">${r.distancia_m.toLocaleString()}m</span>
        </div>`;
      });
      if (res.todas_las_rutas.length > 6)
        html += `<div style="color:var(--text-dim);font-size:10px">...y ${res.todas_las_rutas.length - 6} más</div>`;
      html += `</div>`;
    }

    document.getElementById('resultado-algoritmo').innerHTML = html;
    registrarBench('Backtracking', ms, `O(b^d) · ${res.rutas_encontradas} rutas, ${res.podas_aplicadas} podas`);
    toast(`✅ Backtracking: ${res.rutas_encontradas} rutas, ${res.podas_aplicadas} podas — ${ms}ms`);
  } catch (e) { toast('Error: ' + e.message, '#e74c3c'); }
  finally { btnLoading('btn-bt', false); }
}


// ─────────────────────────────────────────────────────────────
//  Dijkstra — Ruta óptima con memoización LRU
// ─────────────────────────────────────────────────────────────

/**
 * GET /algoritmos/ruta-optima/{origen}/{destino}
 * 
 * Calcula la ruta más corta entre dos nodos usando Dijkstra.
 * El servidor mantiene un caché LRU compartido entre requests
 * (segunda llamada al mismo par es O(1)).
 * 
 * Complejidad: O((V+E) log V) primera vez, O(1) desde caché
 */
export async function calcularRutaOptima() {
  const origen  = document.getElementById('rt-origen').value;
  const destino = document.getElementById('rt-destino').value;
  if (!origen || !destino) { toast('Selecciona origen y destino', '#f39c12'); return; }

  try {
    const t0  = performance.now();
    const res = await api('GET', `/algoritmos/ruta-optima/${origen}/${destino}`);
    const ms  = (performance.now() - t0).toFixed(2);

    dibujarRutaEnMapa(res.camino, '#3dd6f5');
    document.getElementById('ruta-resultado').innerHTML = `
      <div class="result-block">
        <div class="rb-title">⚡ Ruta Óptima ${res.desde_cache ? '(CACHE HIT)' : '(nuevo)'}</div>
        <div class="rb-row"><span>Distancia</span><span>${res.distancia_m.toLocaleString()} m</span></div>
        <div class="rb-row"><span>Tiempo est.</span><span>${res.tiempo_min} min</span></div>
        <div class="rb-row"><span>Cómputo</span><span>${ms} ms</span></div>
        <div class="rb-row"><span>Desde cache</span><span>${res.desde_cache ? '✅ O(1)' : '🔄 O((V+E)logV)'}</span></div>
        <div class="rb-route">${res.camino.join(' → ')}</div>
      </div>`;
    registrarBench('Dijkstra+memo', ms, res.desde_cache ? 'O(1) cache' : 'O((V+E)logV)');
  } catch (e) { toast('Error: ' + e.message, '#e74c3c'); }
}


// ─────────────────────────────────────────────────────────────
//  Bloquear / Desbloquear calles en el grafo
// ─────────────────────────────────────────────────────────────

/**
 * POST /mapa/bloquear  |  POST /mapa/desbloquear
 * 
 * Marca o desmarca una calle como bloqueada en el grafo del
 * servidor. Después de la operación recarga el grafo y lo
 * redibuja en el mapa. También limpia el caché de Dijkstra
 * del servidor (las rutas que usaban esa calle se invalidan).
 * 
 * @param {boolean} bloquear - true = bloquear, false = desbloquear
 */
export async function bloquearCalle(bloquear) {
  const origen  = document.getElementById('blq-origen').value;
  const destino = document.getElementById('blq-destino').value;
  if (!origen || !destino) { toast('Selecciona origen y destino', '#f39c12'); return; }

  const path = bloquear ? '/mapa/bloquear' : '/mapa/desbloquear';
  try {
    await api('POST', path, { origen, destino });
    // Recargar grafo actualizado desde el servidor
    const { dibujarGrafo } = await import('./mapa.js');
    const nuevoGrafo = await api('GET', '/mapa/grafo');
    setGrafoData(nuevoGrafo);
    dibujarGrafo(nuevoGrafo);
    toast(bloquear
      ? `🔴 Calle bloqueada: ${origen} → ${destino}`
      : `🟢 Calle liberada: ${origen} → ${destino}`);
  } catch (e) { toast('Error: ' + e.message, '#e74c3c'); }
}


// ─────────────────────────────────────────────────────────────
//  Merge Sort — Ordenación de pedidos
// ─────────────────────────────────────────────────────────────

/**
 * POST /pedidos/ordenar/resultado
 * 
 * Ordena los pedidos según el criterio seleccionado en el
 * menú desplegable (prioridad, valor, peso, sector, combinado).
 * Usa Merge Sort implementado en el backend.
 * 
 * Complejidad: O(n log n) — estable
 */
export async function ordenarPedidos() {
  const criterio = document.getElementById('sort-criterio').value;
  try {
    const t0  = performance.now();
    const res = await api('POST', '/pedidos/ordenar/resultado', { criterio, descendente: true });
    const ms  = (performance.now() - t0).toFixed(2);

    setPedidosData(res.pedidos);
    renderizarPedidos(res.pedidos);
    toast(`✅ Merge Sort por "${criterio}" — ${res.total} pedidos en ${ms}ms`);
    registrarBench('Merge Sort', ms, `O(n log n) · criterio: ${criterio}`);
  } catch (e) { toast('Error: ' + e.message, '#e74c3c'); }
}


// ─────────────────────────────────────────────────────────────
//  Búsqueda Binaria — Buscar pedido por ID
// ─────────────────────────────────────────────────────────────

/**
 * POST /pedidos/buscar/resultado
 * 
 * Busca un pedido por su ID usando búsqueda binaria sobre
 * la lista ordenada del backend. Si encuentra resultados,
 * reemplaza la lista mostrada.
 * 
 * Complejidad: O(log n)
 */
export async function buscarPedido() {
  const termino = document.getElementById('search-input').value.trim();
  if (!termino) return;
  try {
    const t0  = performance.now();
    const res = await api('POST', '/pedidos/buscar/resultado', { termino, tipo: 'id' });
    const ms  = (performance.now() - t0).toFixed(2);

    if (res.resultado.length) {
      renderizarPedidos(res.resultado);
      toast(`🔍 Búsqueda binaria: "${termino}" encontrado en ${ms}ms`);
      registrarBench('Búsqueda Binaria', ms, `O(log n) · "${termino}"`);
    } else {
      toast(`Sin resultados para "${termino}"`, '#f39c12');
    }
  } catch (e) { toast('Error: ' + e.message, '#e74c3c'); }
}


// ─────────────────────────────────────────────────────────────
//  Reset del sistema
// ─────────────────────────────────────────────────────────────

/**
 * POST /algoritmos/resetear
 * 
 * Reinicia el estado completo del sistema:
 *   - DeliveryCoordinator: limpia reservas
 *   - DijkstraMemo: limpia caché de rutas
 *   - Pedidos: todos vuelven a PENDIENTE
 *   - Repartidores: limpia pedidos_asignados
 */
export async function resetearSistema() {
  try {
    await api('POST', '/algoritmos/resetear');
    limpiarRuta();
    await recargarPedidos();
    document.getElementById('resultado-algoritmo').innerHTML =
      '<div style="color:var(--text-dim);font-size:11px;text-align:center;padding:20px">Sistema reseteado.</div>';
    toast('↺ Sistema reseteado correctamente');
  } catch (e) { toast('Error: ' + e.message, '#e74c3c'); }
}


// ─────────────────────────────────────────────────────────────
//  Benchmark completo — ejecuta todos los algoritmos
// ─────────────────────────────────────────────────────────────

/**
 * Ejecuta todos los algoritmos en secuencia y registra
 * los tiempos en la pestaña Big-O para comparación.
 * 
 * Orden: Greedy → Knapsack → D&V → Backtracking → Dijkstra → Merge Sort
 */
export async function ejecutarTodos() {
  await ejecutarGreedy();
  await ejecutarKnapsack();
  await ejecutarDV();

  document.querySelector('#bt-origen').value  = 'san_blas';
  document.querySelector('#bt-destino').value = 'wanchaq_centro';
  await ejecutarBacktracking();

  document.querySelector('#rt-origen').value  = 'san_blas';
  document.querySelector('#rt-destino').value = 'wanchaq_centro';
  await calcularRutaOptima();

  await ordenarPedidos();
  toast('✅ Benchmark completo — revisa la pestaña Big-O');
}
