/**
 * mapa.js — Funcionalidad del mapa Leaflet
 * Modularización de la lógica de visualización del grafo en el mapa.
 */

let mapaLeaflet = null;
let capaNodos   = null;
let capaAristas = null;
let capaRuta    = null;

export function iniciarMapa() {
  mapaLeaflet = L.map('map', { zoomControl: true, attributionControl: false })
    .setView([-13.5195, -71.9750], 14);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
  }).addTo(mapaLeaflet);

  capaAristas = L.layerGroup().addTo(mapaLeaflet);
  capaNodos   = L.layerGroup().addTo(mapaLeaflet);
  capaRuta    = L.layerGroup().addTo(mapaLeaflet);
}

export function dibujarGrafo(grafo) {
  capaAristas.clearLayers();
  capaNodos.clearLayers();

  grafo.aristas.forEach(a => {
    const origen  = grafo.nodos.find(n => n.id_nodo === a.origen);
    const destino = grafo.nodos.find(n => n.id_nodo === a.destino);
    if (!origen || !destino) return;
    const color = a.bloqueada ? '#e74c3c' : '#2a3245';
    L.polyline(
      [[origen.latitud, origen.longitud], [destino.latitud, destino.longitud]],
      { color, weight: a.bloqueada ? 3 : 2, opacity: 0.9,
        dashArray: a.bloqueada ? '6,4' : null }
    ).bindTooltip(`${a.distancia_m}m · ${a.tiempo_min}min${a.bloqueada ? ' BLOQUEADA' : ''}`,
      { sticky: true, className: 'leaflet-tooltip-dark' })
     .addTo(capaAristas);
  });

  grafo.nodos.forEach(n => {
    const color  = n.es_deposito ? '#c9a84c' : '#3dd6f5';
    const radius = n.es_deposito ? 9 : 6;
    L.circleMarker([n.latitud, n.longitud], {
      radius, color, fillColor: color,
      fillOpacity: 0.9, weight: 2
    }).bindPopup(`<b style="color:${color}">${n.nombre}</b><br>
      <small style="color:#888">${n.sector} · ${n.id_nodo}</small>`)
     .addTo(capaNodos);

    L.tooltip({ permanent: true, direction: 'top', offset: [0, -8],
                className: 'nodo-label' })
     .setContent(`<span style="font-size:9px;color:${color};font-family:monospace">${n.nombre.split(' ').slice(0,2).join(' ')}</span>`)
     .setLatLng([n.latitud, n.longitud])
     .addTo(mapaLeaflet);
  });
}

export function dibujarRutaEnMapa(camino, color = '#2ecc71') {
  capaRuta.clearLayers();
  if (!window.grafoData || camino.length < 2) return;

  const puntos = camino.map(id => {
    const n = window.grafoData.nodos.find(x => x.id_nodo === id);
    return n ? [n.latitud, n.longitud] : null;
  }).filter(Boolean);

  if (puntos.length < 2) return;

  L.polyline(puntos, {
    color, weight: 5, opacity: .9, dashArray: '10,6'
  }).addTo(capaRuta);

  mapaLeaflet.fitBounds(L.latLngBounds(puntos), { padding: [40, 40] });
}

export function centrarEn(lat, lon, zoom = 16) {
  if (mapaLeaflet) mapaLeaflet.setView([lat, lon], zoom);
}

export { mapaLeaflet, capaNodos, capaAristas, capaRuta };
