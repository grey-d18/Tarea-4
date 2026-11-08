# Comparación Modo A vs. Modo B

**Fecha de ejecución:** 7 de noviembre de 2026.
**Modelo:** Claude Sonnet, el mismo en ambos modos.
**Comando:** `uv run evaluacion/evaluar.py --modelo sonnet`.
**Datos:** las respuestas, calificaciones, tiempos y costos están en `resultados.csv`, y cada sesión completa en
`registros/<modo>/<id>.jsonl`.

El diseño (preguntas, respuestas esperadas, tolerancias y criterios) se fijó **antes** de ejecutar, en
`protocolo.md` y `preguntas.csv`, y no se modificó después de ver los resultados.

## Condiciones

| | Modo A – sin MCP ni Skills | Modo B – con MCP y Skills |
|---|---|---|
| Servidor MCP `bcrp` | No (`--strict-mcp-config` sin configuración) | Sí (`--mcp-config .mcp.json`) |
| Skills del proyecto | No (`--disable-slash-commands`) | Sí (herramienta `Skill`) |
| Otras herramientas habilitadas | **Ninguna** (`--tools ""`): sin web, sin archivos, sin terminal | `Bash`, `Read`, `Glob`, `Grep`, y solo se aprueban automáticamente `uv run`, `ls`, `cat` y `head` |
| Acceso a `evaluacion/` | Imposible, porque no tiene herramientas de archivos | Prohibido por la instrucción y por reglas de permiso (`Read(./evaluacion/**)`, `Bash(*evaluacion*)`) |
| Instrucción | La misma | La misma |
| Sesiones | Una por pregunta (`claude -p --no-session-persistence`) | Una por pregunta (`claude -p --no-session-persistence`) |

**Independencia de las sesiones:**
- Los 20 registros tienen 20 identificadores de sesión distintos.
- Ninguna sesión escribió ni editó archivos.
- Ninguna sesión del modo B tocó `evaluacion/`. El script lo revisa en cada llamada a herramientas: columna
  `leyo_evaluacion`.

## Resultados

| Pregunta | Tipo | Esperada | Modo A | Modo B |
|---|---|---|---|---|
| Inflación Lima, dic. 2024 | BCRP | 1.97 % | ✅ 1.97 | ✅ 1.97 |
| Crecimiento del PBI 2024 | BCRP | 3.52 % | ❌ 3.30 | ✅ 3.52 |
| PBI abril 2020 (var. interanual) | BCRP | −39.28 % | ❌ −40.50 | ✅ −39.28 |
| PBI promedio 2024 vs. 2019 | BCRP | 7.14 % | ⚪ no responde | ✅ 7.14 |
| Pobreza nacional 2024 | ENAHO | 27.58 % | ✅ 27.60 | ✅ 27.60 |
| Pobreza rural 2024 | ENAHO | 39.30 % | ⚪ no responde | ✅ 39.30 |
| Pobreza Lima Metropolitana 2024 | ENAHO | 28.21 % | ⚪ no responde | ✅ 28.21 |
| Pobreza Cajamarca 2024 | ENAHO | 45.01 % | ⚪ no responde | ✅ 45.01 |
| Pobreza nacional 2019→2024 y PBI 2024 vs. 2019 | Combinada | +7.39 pp y 7.14 % | ⚪ 7.40 y sin PBI | ✅ 7.39 y 7.14, interpretación cumple |
| Pobreza urbana 2019→2024 y PBI 2024 | Combinada | +10.23 pp y 3.52 % | ⚪ sin respuesta | ✅ 10.23 y 3.50, interpretación cumple |

### Resumen

| Métrica | Modo A | Modo B |
|---|---|---|
| Correctas | **2 / 10** | **10 / 10** |
| Incorrectas (cifra fuera de la tolerancia) | 2 | 0 |
| No contestadas | 6 | 0 |
| Tiempo promedio por pregunta | 7.1 s | 11.4 s |
| Tiempo promedio: BCRP / ENAHO / combinadas | 7.0 / 5.9 / 9.8 s | 10.4 / 11.4 / 13.5 s |
| Costo total (10 preguntas) | 0.16 USD | 0.57 USD |
| Turnos promedio | 2.1 | 5.5 |

La interpretación de las 2 combinadas del modo B se calificó a mano según el `criterio_interpretacion`. Ambas
**cumplen**:
- Las dos concluyen que el PBI creció mientras la pobreza aumentaba.
- La segunda ubica el aumento en el área urbana.
- Ninguna afirma causalidad. La primera lo aclara de forma explícita: «no establece causalidad».

### Preguntas que mejoraron o empeoraron

- **Mejoraron (8):**
  - Las 2 incorrectas del modo A, el PBI 2024 y el de abril de 2020, pasaron a correctas.
  - Las 6 no contestadas pasaron a correctas: la comparación de promedios del PBI, la pobreza rural, la de Lima
    Metropolitana y la de Cajamarca, y las 2 combinadas.
- **Sin cambio (2):** la inflación de diciembre de 2024 y la pobreza nacional 2024 fueron correctas en ambos modos.
  Son las dos cifras más difundidas del conjunto.
- **Empeoraron:** ninguna.

### Herramientas efectivamente usadas en el modo B

| Pregunta | Herramientas |
|---|---|
| Preguntas del BCRP | `buscar_series` + `serie` en tres de ellas; `comparar_periodos` en la de promedios |
| Pobreza rural, Lima Metropolitana y Cajamarca | `Bash`, `Read` y `Grep` sobre `salidas/indicadores.csv`, `salidas/validacion.txt` y `salidas/comparacion_mapa_referencia.csv` |
| Pobreza nacional 2024 | **Ninguna**: respondió de memoria |
| Combinadas | `comparar_periodos`, o `buscar_series` + `serie`, más `Bash` sobre las salidas de la ENAHO |

## Principales errores encontrados

1. **Modo A: cifras plausibles pero equivocadas.**
   - Respondió con seguridad 3.30 % para el PBI 2024. El valor real es 3.52 %.
   - Para abril de 2020 respondió −40.5 %; el valor real es −39.28 %.
   - Son los errores más riesgosos, porque no vienen acompañados de una advertencia.
2. **Modo A: abstención correcta.** En 6 preguntas dijo que no podía saber la cifra con certeza, como pedía la
   instrucción.
   - En la primera combinada dio bien la pobreza (+7.40 pp), pero no el PBI. Por regla, eso cuenta como «no
     responde».
   - En una pregunta intentó usar `Bash`, que no estaba disponible, y la llamada fue rechazada.
3. **Modo B: no ejecutó las Skills.** En las preguntas de ENAHO, el agente leyó los resultados que las Skills
   habían dejado en `salidas/` durante la ejecución integrada (Parte 3), en lugar de invocarlas.
   - Las cifras son correctas y salen del procesamiento validado de las Skills.
   - Pero la evaluación mide «MCP + salidas de las Skills», no la ejecución de las Skills desde cero.
   - Además, sus intentos de correr Python directamente con `python3 -c` quedaron bloqueados por los permisos.
4. **Modo B: una respuesta sin herramientas.** La pobreza nacional 2024 (27.6 %) la respondió de memoria y lo
   declaró en la fuente. Acertó porque es una cifra muy publicada, pero no está respaldada por las herramientas.
5. **Modo B: serie distinta a la prevista.**
   - En la segunda combinada usó `PM04983AA` en lugar de `PM04923AA`, que fue la fijada en el protocolo.
   - Es otra serie anual del PBI del BCRP y la consultó con el MCP. Dio 3.515 %, igual que la esperada.
   - Sin embargo, la reportó redondeada a 3.50. Sigue dentro de la tolerancia de ±0.05, pero muestra que el modelo
     puede redondear antes de responder.

## Conclusión

Con el MCP y las Skills (salidas incluidas), Claude Code pasó de **2 a 10 respuestas correctas de 10**, sin
ninguna cifra equivocada. El costo fue unos 4 segundos más por pregunta y unas 3.5 veces el gasto en tokens.

La mejora se explica por dos cosas:
- **Datos que el modelo no conoce de memoria:** la pobreza por área, por dominio y por departamento, y promedios
  calculados del índice del PBI. Sin herramientas, el modelo se abstiene.
- **Datos que cree conocer pero recuerda mal:** el PBI 2024 y el de abril de 2020. Sin herramientas, el modelo se
  equivoca sin advertirlo.

En el modo B, además, cada cifra viene con una fuente rastreable: el código de la serie y la URL de la API del BCRP,
o el archivo de `salidas/` con su validación.

Las cifras muy difundidas, como la inflación de 2024 o la pobreza nacional, salen bien en ambos modos. Ahí las
herramientas no cambian el resultado, aunque sí la trazabilidad.

**Limitaciones del experimento:**
- Hay una sola corrida por pregunta y modo, así que no mide la variabilidad de las respuestas.
- El modo B aprovechó salidas ya calculadas en lugar de ejecutar las Skills.
- Es un solo modelo y son 10 preguntas.

Una versión más exigente borraría `salidas/` antes del modo B, para obligar al agente a correr las Skills, y
repetiría cada pregunta varias veces.
