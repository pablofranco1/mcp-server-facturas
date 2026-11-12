import pytest
from mcp.server.mcpserver.exceptions import ToolError

import server
from seed import crear_db


@pytest.fixture(autouse=True)
def db(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    crear_db(path)
    monkeypatch.setattr(server, "DB", path)


def test_listar_clientes():
    assert len(server.listar_clientes()) == 6


def test_crear_factura():
    factura = server.crear_factura(1, "Consultoría", 800)
    assert factura["importe"] == 800


def test_importe_maximo():
    with pytest.raises(ToolError):
        server.crear_factura(1, "Consultoría", 100000)


def test_importe_negativo():
    with pytest.raises(ToolError):
        server.crear_factura(1, "Consultoría", -50)


def test_cliente_inexistente():
    with pytest.raises(ToolError):
        server.crear_factura(999, "Consultoría", 800)


def test_limite_diario_contra_troceo():
    server.crear_factura(1, "Parte 1", 50000)
    with pytest.raises(ToolError):
        server.crear_factura(1, "Parte 2", 1)


def test_estado_invalido():
    with pytest.raises(ToolError):
        server.buscar_facturas(estado="borrada")


def test_inyeccion_sql():
    assert server.buscar_facturas(cliente="' OR 1=1 --") == []


def test_marcar_pagada_inexistente():
    with pytest.raises(ToolError):
        server.marcar_pagada(999)