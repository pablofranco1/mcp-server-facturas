\# MCP Server Facturas



Servidor MCP que permite a un LLM (Claude Desktop o cualquier cliente MCP) consultar y gestionar clientes y facturas. El modelo nunca accede a la base de datos directamente: solo puede usar un conjunto cerrado de herramientas, y el servidor valida cada operación independientemente de lo que decida el modelo.



!\[Resumen de deuda](docs/resumen.png)



\## Herramientas



| Herramienta | Qué hace |

|---|---|

| `listar\_clientes` | Lista los clientes |

| `buscar\_facturas` | Busca facturas por cliente y estado (pagada, pendiente, vencida) |

| `resumen\_deuda` | Importe pendiente y vencido por cliente |

| `crear\_factura` | Crea una factura para un cliente existente |

| `marcar\_pagada` | Marca una factura como pagada |



\## Seguridad



El modelo puede equivocarse o ser manipulado (por ejemplo, mediante prompt injection), así que las reglas de negocio se aplican en el servidor y no en el prompt:



\- \*\*Sin SQL libre:\*\* el modelo no puede ejecutar consultas arbitrarias, solo las herramientas definidas. Todas las consultas usan parámetros, sin concatenar texto.

\- \*\*Validación de entradas:\*\* importes entre 0 y 50.000 €, vencimientos entre 1 y 120 días, estados de una lista cerrada y conceptos limitados a 200 caracteres.

\- \*\*Límite acumulado:\*\* máximo de 50.000 € facturados por cliente y día.

\- \*\*Errores explicativos:\*\* los rechazos devuelven un motivo claro al modelo, que puede explicárselo al usuario en lugar de reintentar a ciegas.



\### Por qué un límite acumulado



En la primera versión, el límite era solo por factura. Al pedirle una factura de 100.000 €, el servidor la rechazó correctamente, pero el propio modelo propuso como alternativa partirla en dos facturas de 50.000 €. No había mala intención: intentaba ayudar. Aun así, demostraba que un agente puede esquivar un límite por operación troceando la acción.



Con el límite acumulado por cliente y día, la segunda factura se rechaza y la operación requiere aprobación manual:



!\[Límite diario](docs/limite.png)



\## Instalación



Requisitos: Python 3.10+ y Claude Desktop.



```

git clone https://github.com/pablofranco1/mcp-server-facturas.git

cd mcp-server-facturas

python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

python seed.py

```



`seed.py` crea una base de datos SQLite con clientes y facturas de ejemplo.



\## Conexión con Claude Desktop



En Claude Desktop: \*\*Configuración → Desarrollador → Editar configuración\*\*, y añade en `claude\_desktop\_config.json`:



```json

{

&#x20; "mcpServers": {

&#x20;   "facturas": {

&#x20;     "command": "C:\\\\ruta\\\\a\\\\mcp-server-facturas\\\\venv\\\\Scripts\\\\python.exe",

&#x20;     "args": \["C:\\\\ruta\\\\a\\\\mcp-server-facturas\\\\server.py"]

&#x20;   }

&#x20; }

}

```



Reinicia Claude Desktop y prueba, por ejemplo:



\- ¿Qué clientes me deben dinero y cuánto tienen vencido?

\- Crea una factura de 800 € a Talleres Ruzafa por consultoría

\- Marca como pagada la factura 12



\## Estructura



\- `server.py`: servidor MCP y herramientas

\- `seed.py`: genera la base de datos de ejemplo

