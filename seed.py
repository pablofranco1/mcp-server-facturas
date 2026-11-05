import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB = Path(__file__).parent / "facturas.db"

CLIENTES = [
    ("Panadería Sol", "B12345678", "info@panaderiasol.es"),
    ("Talleres Ruzafa", "B23456789", "admin@talleresruzafa.es"),
    ("Clínica Dental Turia", "B34567890", "contacto@dentalturia.es"),
    ("Estudio Arquitectura Mar", "B45678901", "hola@estudiomar.es"),
    ("Frutas Huerta Norte", "B56789012", "pedidos@huertanorte.es"),
    ("Gimnasio Benimaclet", "B67890123", "info@gymbenimaclet.es"),
]

CONCEPTOS = ["Mantenimiento web", "Consultoría", "Desarrollo a medida", "Hosting anual", "Soporte técnico"]

random.seed(42)
DB.unlink(missing_ok=True)

con = sqlite3.connect(DB)
con.executescript("""
CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT, nif TEXT, email TEXT);
CREATE TABLE facturas (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    fecha TEXT,
    vencimiento TEXT,
    concepto TEXT,
    importe REAL,
    pagada INTEGER DEFAULT 0
);
""")
con.executemany("INSERT INTO clientes (nombre, nif, email) VALUES (?, ?, ?)", CLIENTES)

hoy = date.today()
for _ in range(40):
    fecha = hoy - timedelta(days=random.randint(0, 180))
    con.execute(
        "INSERT INTO facturas (cliente_id, fecha, vencimiento, concepto, importe, pagada) VALUES (?, ?, ?, ?, ?, ?)",
        (
            random.randint(1, len(CLIENTES)),
            fecha.isoformat(),
            (fecha + timedelta(days=30)).isoformat(),
            random.choice(CONCEPTOS),
            round(random.uniform(150, 3000), 2),
            int(random.random() < 0.7),
        ),
    )

con.commit()
con.close()
print("Base de datos creada:", DB)