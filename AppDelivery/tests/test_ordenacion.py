import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modelos.pedido import Pedido, Prioridad, EstadoPedido
from algoritmos.ordenacion import (
    merge_sort, ordenar_por_prioridad, ordenar_por_peso,
    ordenar_por_valor, ordenar_por_sector, ordenar_combinado,
)
from algoritmos.busqueda import busqueda_binaria_id, IndicePedidos


def _crear_pedidos():
    return [
        Pedido("P003", "Cliente C", "Wanchaq", -13.528, -71.968,
               5.0, 0.02, 80.0, Prioridad.URGENTE),
        Pedido("P001", "Cliente A", "San Blas", -13.5145, -71.976,
               2.5, 0.01, 45.0, Prioridad.ALTA),
        Pedido("P002", "Cliente B", "Santiago", -13.524, -71.992,
               8.0, 0.04, 120.0, Prioridad.MEDIA),
    ]


def test_merge_sort_prioridad():
    peds = _crear_pedidos()
    ords = ordenar_por_prioridad(peds)
    assert ords[0].prioridad == Prioridad.URGENTE
    assert ords[-1].prioridad == Prioridad.MEDIA


def test_merge_sort_peso():
    peds = _crear_pedidos()
    ords = ordenar_por_peso(peds)
    assert ords[0].peso_kg <= ords[-1].peso_kg


def test_merge_sort_valor():
    peds = _crear_pedidos()
    ords = ordenar_por_valor(peds)
    assert ords[0].valor >= ords[-1].valor


def test_merge_sort_sector():
    peds = _crear_pedidos()
    ords = ordenar_por_sector(peds)
    sectores = [p.sector for p in ords]
    assert sectores == sorted(sectores)


def test_ordenar_combinado():
    peds = _crear_pedidos()
    ords = ordenar_combinado(peds)
    assert ords[0].prioridad.value >= ords[-1].prioridad.value


def test_busqueda_binaria_existente():
    peds = _crear_pedidos()
    ords = sorted(peds, key=lambda p: p.id_pedido)
    res = busqueda_binaria_id(ords, "P001")
    assert res is not None
    assert res.id_pedido == "P001"


def test_busqueda_binaria_inexistente():
    peds = _crear_pedidos()
    ords = sorted(peds, key=lambda p: p.id_pedido)
    res = busqueda_binaria_id(ords, "P999")
    assert res is None


def test_indice_pedidos():
    peds = _crear_pedidos()
    idx = IndicePedidos(peds)
    assert idx.total() == 3
    assert idx.existe("P001")
    assert not idx.existe("P999")
    assert len(idx.buscar_por_sector("San Blas")) == 1
