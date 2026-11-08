# Protocolo de evaluación (fijado antes de ejecutar los modos A y B)

**Fecha de diseño:** 7 de noviembre de 2026, antes de ejecutar cualquier pregunta en los modos A o B.

## Preguntas

`preguntas.csv` contiene 10 preguntas: 4 del BCRP, 4 de ENAHO y 2 combinadas. Cada una tiene una respuesta esperada,
una unidad y una tolerancia. Las combinadas piden dos cifras y una interpretación breve.

## Cómo se obtuvieron las respuestas esperadas

Las respuestas **no** salen del agente, ni del servidor MCP, ni de las Skills:

- **BCRP:** consulta directa a la API pública (`estadisticas.bcrp.gob.pe/estadisticas/series/api/...`).
- **ENAHO:** recálculo desde los `.dta` originales del INEI con un código mínimo propio
  (`verificar_respuestas.py`), contrastado con las cifras oficiales: la consigna de la tarea (27.6 %, 39.3 %), el
  README de la Sesión 16 (Lima Metropolitana 28.2 %) y la tabla de referencia departamental de la Sesión 16.

Para reproducirlo: `uv run evaluacion/verificar_respuestas.py`. Produce `verificacion_respuestas.csv` y termina con
error si alguna respuesta esperada no coincide.

**Las respuestas esperadas y las tolerancias no se modificarán después de ver los resultados.**

## Tolerancias

| Tipo | Tolerancia | Motivo |
|---|---|---|
| Tasas del BCRP (inflación, crecimiento) | ±0.05 pp | Redondeo a dos decimales |
| PBI abril 2020 y comparación de promedios | ±0.1 pp | Redondeo a un decimal |
| Pobreza ENAHO | ±0.1 pp | Diferencia máxima que acepta la consigna |
| Cambio de pobreza 2019→2024 | ±0.15 pp | Diferencia de dos cifras redondeadas |

## Calificación

Cada respuesta se califica como:

- **Correcta:** el valor está dentro de la tolerancia. En las combinadas, **las dos cifras** deben estar dentro de su
  tolerancia **y** la interpretación debe cumplir el `criterio_interpretacion`, es decir, ser coherente y sin
  afirmaciones causales.
- **Incorrecta:** da un valor fuera de la tolerancia, o una interpretación incoherente o causal.
- **No responde:** dice que no sabe, no da un número o falla.

## Modos

| | Modo A – sin MCP ni Skills | Modo B – con MCP y Skills |
|---|---|---|
| Servidor MCP `bcrp` | No | Sí |
| Skills del proyecto | No | Sí |
| Otras herramientas | Ninguna (sin web, sin archivos, sin terminal) | Las necesarias para correr las Skills (terminal y lectura de archivos del proyecto) |
| Modelo | El mismo en ambos modos | El mismo en ambos modos |
| Instrucción | La misma en ambos modos | La misma en ambos modos |

- Se ejecuta con `uv run evaluacion/evaluar.py --modelo sonnet` (ambos modos). Cada sesión completa queda en
  `registros/<modo>/<id>.jsonl`.
- Cada pregunta se ejecuta en una **sesión independiente** (`claude -p`, sin persistir la sesión).
- En el modo A, Claude no tiene acceso a archivos, así que no puede leer `preguntas.csv`, `salidas/` ni
  `verificacion_respuestas.csv`.
- En el modo B, el agente **no debe leer** `evaluacion/` (la instrucción lo prohíbe y se revisa en el registro de
  herramientas usadas).

## Qué se registra

Por cada pregunta y modo, en `resultados.csv`: la pregunta, la respuesta esperada, la respuesta generada, la fuente
citada, las herramientas usadas, la calificación, el tiempo de ejecución y los errores.
