/**
 * mapa.js — Visualización del mapa y grafo vial de Cusco
 * =======================================================
 * 
 * Gestiona el mapa Leaflet centrado en Cusco, dibuja el grafo
 * (nodos como marcadores, aristas como líneas) y las rutas
 * calculadas por los algoritmos.
 * 
 * Dependencias: Leaflet (CDN), state.js (grafoData)
 */

import { grafoData } from './state.js';

// ─────────────────────────────────────────────────────────────
//  Estado interno del módulo
// ─────────────────────────────────────────────────────────────

/** Instancia del mapa Leaflet */
let mapaLeaflet = null;

/** Capa de aristas (calles) */
let capaAristas = null;

/** Capa de nodos (intersecciones) */
let capaNodos = null;

/** Capa de ruta activa (polyline de la ruta calculada) */
let capaRuta = null;


// ─────────────────────────────────────────────────────────────
//  Inicialización
// ─────────────────────────────────────────────────────────────

/**
 * Inicializa el mapa Leaflet centrado en la Plaza de Armas de Cusco.
 * Crea tres capas superpuestas: aristas, nodos y rutas.
 * 
 * @param {string} containerId - ID del elemento <div> del mapa
 */
export function iniciarMapa(containerId = 'map') {
  mapaLeaflet = L.map(containerId, {
    zoomControl: true,
    attributionControl: false,
  }).setView([-13.5195, -71.9750], 14);

  // Capa base OpenStreetMap con filtro oscuro (CSS)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
  }).addTo(mapaLeaflet);

  // Capas del grafo
  capaAristas = L.layerGroup().addTo(mapaLeaflet);
  capaNodos   = L.layerGroup().addTo(mapaLeaflet);
  capaRuta    = L.layerGroup().addTo(mapaLeaflet);
}


// ─────────────────────────────────────────────────────────────
//  Dibujado del grafo
// ─────────────────────────────────────────────────────────────

/**
 * Dibuja el grafo vial completo sobre el mapa.
 * 
 * Cada arista se representa como una polyline (color gris por defecto,
 * rojo si está bloqueada, con dashArray para indicar bloqueo).
 * Cada nodo se representa como un circleMarker (dorado si es depósito,
 * cian si es intersección normal) con tooltip permanente.
 * 
 * @param {Object} grafo - Objeto del grafo con { nodos: [...], aristas: [...] }
 */
export function dibujarGrafo(grafo) {
  if (!mapaLeaflet) return;
  capaAristas.clearLayers();
  capaNodos.clearLayers();

  // ── Aristas ────────────────────────────────────────────────
  grafo.aristas.forEach(a => {
    const origen  = grafo.nodos.find(n => n.id_nodo === a.origen);
    const destino = grafo.nodos.find(n => n.id_nodo === a.destino);
    if (!origen || !destino) return;

    const color  = a.bloqueada ? '#e74c3c' : '#2a3245';
    const weight = a.bloqueada ? 3 : 2;
    const dash   = a.bloqueada ? '6,4' : null;

    L.polyline(
      [[origen.latitud, origen.longitud], [destino.latitud, destino.longitud]],
      { color, weight, opacity: 0.9, dashArray: dash }
    )
      .bindTooltip(`${a.distancia_m}m · ${a.tiempo_min}min${a.bloqueada ? ' 🔴 BLOQUEADA' : ''}`,
        { sticky: true, className: 'leaflet-tooltip-dark' })
      .addTo(capaAristas);
  });

  // ── Nodos ──────────────────────────────────────────────────
  grafo.nodos.forEach(n => {
    const color  = n.es_deposito ? '#c9a84c' : '#3dd6f5';
    const radius = n.es_deposito ? 9 : 6;

    L.circleMarker([n.latitud, n.longitud], {
      radius, color, fillColor: color,
      fillOpacity: 0.9, weight: 2,
    })
      .bindPopup(`<b style="color:${color}">${n.nombre}</b><br>
        <small style="color:#888">${n.sector} · ${n.id_nodo}</small>`)
      .addTo(capaNodos);

    L.tooltip({
      permanent: true, direction: 'top', offset: [0, -8],
      className: 'nodo-label',
    })
      .setContent(`<span style="font-size:9px;color:${color};font-family:monospace">
        ${n.nombre.split(' ').slice(0, 2).join(' ')}</span>`)
      .setLatLng([n.latitud, n.longitud])
      .addTo(mapaLeaflet);
  });
}


// ─────────────────────────────────────────────────────────────
//  Rutas
// ─────────────────────────────────────────────────────────────

/**
 * Dibuja una ruta óptima como polyline verde en el mapa.
 * Limpia cualquier ruta previa.
 * 
 * @param {string[]} camino - Lista ordenada de id_nodo desde origen a destino
 * @param {string}   color  - Color CSS de la polyline (default verde)
 */
export function dibujarRutaEnMapa(camino, color = '#2ecc71') {
  if (!mapaLeaflet) return;
  capaRuta.clearLayers();
  if (!grafoData || camino.length < 2) return;

  const puntos = camino
    .map(id => {
      const n = grafoData.nodos.find(x => x.id_nodo === id);
      return n ? [n.latitud, n.longitud] : null;
    })
    .filter(Boolean);

  if (puntos.length < 2) return;

  // Línea de la ruta
  L.polyline(puntos, { color, weight: 5, opacity: 0.9, dashArray: '10,6' })
    .addTo(capaRuta);

  // Marcadores de inicio (círculo) y fin (rombo)
  const iconStart = L.divIcon({
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:3px solid #fff;"></div>`,
    className: '',
  });
  const iconEnd = L.divIcon({
    html: `<div style="width:16px;height:16px;border-radius:3px;background:#e74c3c;border:3px solid #fff;transform:rotate(45deg)"></div>`,
    className: '',
  });
  L.marker(puntos[0], { icon: iconStart }).addTo(capaRuta);
  L.marker(puntos[puntos.length - 1], { icon: iconEnd }).addTo(capaRuta);

  // Ajustar zoom
  mapaLeaflet.fitBounds(L.latLngBounds(puntos), { padding: [40, 40] });
}


// ─────────────────────────────────────────────────────────────
//  Utilidades del mapa
// ─────────────────────────────────────────────────────────────

/**
 * Centra el mapa en unas coordenadas con el zoom indicado.
 * @param {number} lat  - Latitud
 * @param {number} lon  - Longitud
 * @param {number} zoom - Nivel de zoom (default 16)
 */
export function centrarEn(lat, lon, zoom = 16) {
  if (mapaLeaflet) mapaLeaflet.setView([lat, lon], zoom);
}

/**
 * Limpia la capa de rutas del mapa.
 */
export function limpiarRuta() {
  if (capaRuta) capaRuta.clearLayers();
}


// ─────────────────────────────────────────────────────────────
//  Exportaciones para depuración
// ─────────────────────────────────────────────────────────────

export { mapaLeaflet, capaNodos, capaAristas, capaRuta };
