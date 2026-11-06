# Tarea 4 – Agente de investigación socioeconómica (MCP + Skills)

> 🚧 En construcción. Ver [`PLAN.md`](PLAN.md) para el avance.

**Pregunta de investigación:** ¿La recuperación del PBI peruano entre 2019 y 2024 se reflejó en una menor pobreza
monetaria y desigualdad en los departamentos del país?

## 1. Objetivo
_Pendiente._

## 2. Arquitectura del agente
_Pendiente._

## 3. Herramientas MCP (`mcp/server.py`)
_Pendiente._

## 4. Skills (`.claude/skills/`)
_Pendiente._

## 5. Fuentes y descarga de datos

| Fuente | Datos | Enlace |
|---|---|---|
| INEI | ENAHO 2024, módulo 34 (sumaria) | https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip |
| INEI | ENAHO 2024, módulo 02 (miembros) | https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip |
| INEI | ENAHO 2019, módulo 34 (sumaria) | https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/687-Modulo34.zip |
| Curso | Límites departamentales | https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson |
| BCRP | Series estadísticas | https://estadisticas.bcrp.gob.pe/estadisticas/series/ |

Los archivos se guardan en `datos/`, que no se sube a GitHub.

## 6. Instalación con `uv`

```bash
uv sync
```

## 7. Conectar el MCP a Claude Code
El servidor está declarado en `.mcp.json`. Al abrir `claude` en esta carpeta, aprobar el servidor `bcrp` y revisar con `/mcp`.

## 8. Reproducir el procesamiento y las pruebas

```bash
uv run pytest -q          # pruebas del servidor MCP (meta: 10 passed)
```

## 9. Resultados de la evaluación
_Pendiente._

## 10. Limitaciones y problemas encontrados
_Pendiente._

## 11. Ejemplo de ejecución completa
_Pendiente._

## 12. Evidencias del uso de IA
Ver [`evidencias_ia/`](evidencias_ia/).
