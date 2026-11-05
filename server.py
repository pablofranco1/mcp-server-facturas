import sqlite3
from datetime import date, timedelta
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

DB = Path(__file__).parent / "facturas.db"
mcp = MCPServer("facturas", version="1.0.0")

ESTADO = """CASE WHEN f.pagada THEN 'pagada'
                 WHEN f.vencimiento < date('now') THEN 'vencida'
                 ELSE 'pendiente' END"""


def query(sql, params=()):
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(sql, params)]


@mcp.tool()
def listar_clientes() -> list[dict]:
    """Devuelve todos los clientes con su id, nombre, NIF y email."""
    return query("SELECT * FROM clientes ORDER BY nombre")


@mcp.tool()
def buscar_facturas(cliente: str = "", estado: str = "") -> list[dict]:
    """Busca facturas. Filtra opcionalmente por nombre de cliente (parcial) y por estado: pagada, pendiente o vencida."""
    if estado and estado not in ("pagada", "pendiente", "vencida"):
        raise ToolError("Estado no válido: usa pagada, pendiente o vencida")

    rows = query(
        f"""SELECT f.id, c.nombre AS cliente, f.fecha, f.vencimiento, f.concepto, f.importe, {ESTADO} AS estado
            FROM facturas f JOIN clientes c ON c.id = f.cliente_id
            WHERE c.nombre LIKE ?
            ORDER BY f.fecha DESC""",
        (f"%{cliente}%",),
    )
    return [r for r in rows if not estado or r["estado"] == estado]


@mcp.tool()
def resumen_deuda() -> list[dict]:
    """Importe pendiente y vencido por cliente, ordenado de mayor a menor deuda."""
    return query(
        f"""SELECT c.nombre AS cliente,
                   ROUND(SUM(CASE WHEN {ESTADO} = 'pendiente' THEN f.importe ELSE 0 END), 2) AS pendiente,
                   ROUND(SUM(CASE WHEN {ESTADO} = 'vencida' THEN f.importe ELSE 0 END), 2) AS vencido
            FROM facturas f JOIN clientes c ON c.id = f.cliente_id
            WHERE f.pagada = 0
            GROUP BY c.nombre
            ORDER BY pendiente + vencido DESC"""
    )


@mcp.tool()
def crear_factura(cliente_id: int, concepto: str, importe: float, dias_vencimiento: int = 30) -> dict:
    """Crea una factura nueva para un cliente existente."""
    if not 0 < importe <= 50000:
        raise ToolError("El importe debe estar entre 0 y 50.000 €")
    if not 1 <= dias_vencimiento <= 120:
        raise ToolError("El vencimiento debe estar entre 1 y 120 días")
    if not query("SELECT id FROM clientes WHERE id = ?", (cliente_id,)):
        raise ToolError(f"No existe el cliente {cliente_id}")

    hoy = date.today()
    facturado_hoy = query(
        "SELECT COALESCE(SUM(importe), 0) AS total FROM facturas WHERE cliente_id = ? AND fecha = ?",
        (cliente_id, hoy.isoformat()),
    )[0]["total"]
    if facturado_hoy + importe > 50000:
        raise ToolError(
            f"Límite diario de 50.000 € por cliente superado (ya facturado hoy: {facturado_hoy:.2f} €). "
            "Requiere aprobación manual."
        )

    vencimiento = hoy + timedelta(days=dias_vencimiento)
    with sqlite3.connect(DB) as con:
        cur = con.execute(
            "INSERT INTO facturas (cliente_id, fecha, vencimiento, concepto, importe) VALUES (?, ?, ?, ?, ?)",
            (cliente_id, hoy.isoformat(), vencimiento.isoformat(), concepto[:200], round(importe, 2)),
        )
    return {"id": cur.lastrowid, "cliente_id": cliente_id, "concepto": concepto, "importe": round(importe, 2)}

@mcp.tool()
def marcar_pagada(factura_id: int) -> str:
    """Marca una factura como pagada."""
    with sqlite3.connect(DB) as con:
        cur = con.execute("UPDATE facturas SET pagada = 1 WHERE id = ?", (factura_id,))
    if cur.rowcount == 0:
        raise ToolError(f"No existe la factura {factura_id}")
    return f"Factura {factura_id} marcada como pagada"


if __name__ == "__main__":
    mcp.run()