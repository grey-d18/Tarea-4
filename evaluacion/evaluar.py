"""Evaluación Modo A (sin MCP ni Skills) vs. Modo B (con MCP y Skills) sobre las 10 preguntas de preguntas.csv.

    uv run evaluacion/evaluar.py                          # ambos modos, modelo sonnet
    uv run evaluacion/evaluar.py --modos A --modelo opus
    uv run evaluacion/evaluar.py --ids enaho_rural_2024 --salida /tmp/prueba.csv   # prueba rápida

Cada pregunta se hace en una sesión nueva de Claude Code (claude -p, sin guardar la sesión), con la misma instrucción y
el mismo modelo en ambos modos. La respuesta llega como JSON (valor, valor_2, interpretacion, fuente). El script
registra las herramientas usadas, el tiempo y los errores, califica las cifras con la tolerancia de preguntas.csv y
escribe evaluacion/resultados.csv; cada sesión completa queda en evaluacion/registros/<modo>/<id>.jsonl. La interpretación de las preguntas combinadas se califica a mano (columna
`calificacion_interpretacion`) siguiendo protocolo.md.
"""
import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
ESQUEMA = {"type": "object", "required": ["valor", "fuente"],
           "properties": {"valor": {"type": ["number", "null"]}, "valor_2": {"type": ["number", "null"]},
                          "interpretacion": {"type": "string"}, "fuente": {"type": "string"}}}
INSTRUCCION = (
    "Responde la pregunta con cifras. Pon la primera cifra pedida en «valor» y, si la pregunta pide una segunda, "
    "ponla en «valor_2», cada una en la unidad que pide la pregunta. Si la pregunta pide interpretar, escribe 2 a 4 "
    "oraciones en «interpretacion». Si no puedes saber una cifra con certeza, pon null: no estimes. En «fuente» di "
    "de dónde sale cada cifra (institución, serie o archivo y periodo). No leas la carpeta evaluacion/.\n\n")
SIN_MCP = ["--strict-mcp-config"]
MODOS = {
    # A: sin herramientas de ningún tipo, sin MCP y sin Skills (solo la memoria del modelo)
    "A": ["--tools", "", *SIN_MCP, "--disable-slash-commands"],
    # B: servidor MCP bcrp + Skills del proyecto + terminal y lectura para correr las Skills
    "B": ["--tools", "Bash,Read,Glob,Grep,Skill", "--strict-mcp-config", "--mcp-config", str(RAIZ / ".mcp.json"),
          "--allowedTools", "mcp__bcrp", "Skill", "Read", "Glob", "Grep", "Bash(uv run:*)", "Bash(ls:*)",
          "Bash(cat:*)", "Bash(head:*)",
          "--disallowedTools", "Read(./evaluacion/**)", "Bash(*evaluacion*)", "Grep(./evaluacion/**)"],
}


def preguntar(q, modo: str, modelo: str, registros: Path) -> dict:
    cmd = ["claude", "-p", INSTRUCCION + q.pregunta, "--output-format", "stream-json", "--verbose",
           "--json-schema", json.dumps(ESQUEMA), "--no-session-persistence", "--model", modelo, *MODOS[modo]]
    t = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900, cwd=RAIZ)
        salida, error = proc.stdout, proc.stderr.strip()[-300:]
    except subprocess.TimeoutExpired:
        salida, error = "", "tiempo agotado (900 s)"
    (registros / modo).mkdir(parents=True, exist_ok=True)
    (registros / modo / f"{q.id}.jsonl").write_text(salida)      # la sesión completa, como evidencia

    llamadas, final = {}, {}                                      # id de la llamada → (nombre, entrada, rechazada)
    for linea in salida.splitlines():
        try:
            ev = json.loads(linea)
        except json.JSONDecodeError:
            continue
        for c in ev.get("message", {}).get("content", []) if isinstance(ev.get("message"), dict) else []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use" and c["name"] != "StructuredOutput":
                nombre = c["name"]
                if nombre == "Skill":
                    nombre += f"({c.get('input', {}).get('skill', '')})"
                entrada = {k: v for k, v in c.get("input", {}).items() if k != "description"}
                llamadas[c["id"]] = [nombre, json.dumps(entrada, ensure_ascii=False), False]
            elif c.get("type") == "tool_result" and c.get("is_error") and c.get("tool_use_id") in llamadas:
                llamadas[c["tool_use_id"]][2] = True
        if ev.get("type") == "result":
            final = ev
    usadas = [n for n, _, rechazada in llamadas.values() if not rechazada]
    rechazadas = [n for n, _, rechazada in llamadas.values() if rechazada]
    toco_evaluacion = [e for n, e, rechazada in llamadas.values() if not rechazada and "evaluacion" in e]
    r = final.get("structured_output") or {}
    if final.get("is_error"):
        error = (error + " " + str(final.get("result", ""))).strip()[-300:]
    return {"valor": r.get("valor"), "valor_2": r.get("valor_2"), "interpretacion": r.get("interpretacion", ""),
            "fuente": r.get("fuente", "" if r else str(final.get("result", ""))[:300]),
            "herramientas": ";".join(usadas), "herramientas_rechazadas": ";".join(rechazadas),
            "leyo_evaluacion": " | ".join(toco_evaluacion)[:300],
            "segundos": round(time.time() - t, 1), "turnos": final.get("num_turns"),
            "costo_usd": final.get("total_cost_usd"), "error": error if not r else ""}


def dentro(valor, esperado, tolerancia) -> bool:
    return valor is not None and abs(float(valor) - esperado) <= tolerancia


def calificar(q, r) -> tuple[str, str]:
    """(calificacion_numerica, calificacion). Las combinadas quedan «revisar» hasta calificar la interpretación."""
    if r["valor"] is None or (pd.notna(q.respuesta_esperada_2) and r["valor_2"] is None):
        return "no responde", "no responde"
    ok = dentro(r["valor"], q.respuesta_esperada, q.tolerancia)
    if pd.notna(q.respuesta_esperada_2):
        ok = ok and dentro(r["valor_2"], q.respuesta_esperada_2, q.tolerancia_2)
        return ("correcta" if ok else "incorrecta"), ("revisar" if ok else "incorrecta")
    return (("correcta" if ok else "incorrecta"),) * 2


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--modos", nargs="+", default=["A", "B"], choices=list(MODOS))
    p.add_argument("--modelo", default="sonnet")
    p.add_argument("--ids", nargs="+", help="solo estas preguntas (para probar)")
    p.add_argument("--paralelo", type=int, default=4, help="llamadas simultáneas en el modo A")
    p.add_argument("--salida", default=str(AQUI / "resultados.csv"))
    a = p.parse_args()

    preguntas = pd.read_csv(AQUI / "preguntas.csv")
    if a.ids:
        preguntas = preguntas[preguntas.id.isin(a.ids)]
    registros = Path(a.salida).parent / "registros"
    respuestas = {}
    for modo in a.modos:
        # El modo B corre de a una pregunta: las Skills escriben en salidas/ y figuras/
        hilos = a.paralelo if modo == "A" else 1
        print(f"Modo {modo}: {len(preguntas)} preguntas con {a.modelo} ({hilos} a la vez)...", flush=True)
        with ThreadPoolExecutor(hilos) as ex:
            for q, r in zip(preguntas.itertuples(), ex.map(lambda q: preguntar(q, modo, a.modelo, registros),
                                                           preguntas.itertuples())):
                respuestas[(q.id, modo)] = r
                print(f"  {modo} {q.id}: {r['valor']} / {r['valor_2']}  [{r['herramientas'] or 'sin herramientas'}]"
                      f"  {r['segundos']} s {r['error']}", flush=True)

    filas = []
    for q in preguntas.itertuples():
        for modo in a.modos:
            r = respuestas[(q.id, modo)]
            num, cal = calificar(q, r)
            filas.append({"id": q.id, "tipo": q.tipo, "modo": modo, "modelo": a.modelo, "pregunta": q.pregunta,
                          "respuesta_esperada": q.respuesta_esperada, "respuesta_esperada_2": q.respuesta_esperada_2,
                          "valor": r["valor"], "valor_2": r["valor_2"], "interpretacion": r["interpretacion"],
                          "fuente": r["fuente"], "herramientas": r["herramientas"],
                          "herramientas_rechazadas": r["herramientas_rechazadas"],
                          "leyo_evaluacion": r["leyo_evaluacion"], "calificacion_numerica": num,
                          "calificacion_interpretacion": "", "calificacion": cal, "segundos": r["segundos"],
                          "turnos": r["turnos"], "costo_usd": r["costo_usd"], "error": r["error"]})
    res = pd.DataFrame(filas)
    res.to_csv(a.salida, index=False)
    print(f"\nGuardado {a.salida}")
    print(res.pivot(index="id", columns="modo", values="calificacion").to_string())
    print("\n" + res.groupby("modo").calificacion.value_counts().unstack(fill_value=0).to_string())
    if res.leyo_evaluacion.fillna("").astype(bool).any():
        print("\n¡OJO! Alguna respuesta tocó la carpeta evaluacion/: revisar y anular según protocolo.md.")
    if (res.calificacion == "revisar").any():
        print("\nCalifica a mano la interpretación de las filas «revisar» (columna calificacion_interpretacion: "
              "cumple / no cumple) y pon la calificación final en «calificacion».")
