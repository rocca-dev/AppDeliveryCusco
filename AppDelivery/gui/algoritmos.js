/**
 * algoritmos.js — Interfaz de ejecución de algoritmos
 * Proporciona funciones helper para los botones del panel de algoritmos.
 */

const API = 'http://localhost:8000';

export async function api(method, path, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(API + path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}

export function toast(msg, color = '#c9a84c') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.borderColor = color;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2800);
}

export function btnLoading(id, loading) {
  const b = document.getElementById(id);
  if (!b) return;
  if (loading) {
    b._orig = b.innerHTML;
    b.innerHTML = '<span class="spinner"></span> Calculando...';
    b.disabled = true;
  } else {
    b.innerHTML = b._orig;
    b.disabled = false;
  }
}

export function prioColor(p) {
  const colors = {
    URGENTE: '#e74c3c', ALTA: '#f39c12',
    MEDIA: '#3dd6f5', BAJA: '#6b7280'
  };
  return colors[p] || '#fff';
}
