"""Servidor MCP del BCRP: busca, descarga, resume y compara series oficiales del Banco Central de Reserva del Perú.

    uv run pytest -q                 # las 8 pruebas originales + 2 propias
    uv run mcp/server.py             # el servidor, por stdio (Claude Code lo lanza desde .mcp.json)

Las cuentas las hace Python, no el modelo: así cada cifra sale de una llamada que se puede repetir.
Basado en la plantilla de la Sesión 04 (d2cml-ai/Data-Science-Python).
"""
import re
import time
import unicodedata
from datetime import date
from functools import cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

AQUI = Path(__file__).parent
CATALOGO = AQUI / "datos" / "catalogo_bcrp.csv"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
         "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, serie para los datos y comparar_periodos para "
    "contrastar dos intervalos (por ejemplo 2019 frente a 2024). No calcules a mano: cita siempre el código de la "
    "serie, el periodo y la fuente."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


@cache
def catalogo():
    """El catálogo oficial: 17 mil series en unos 7 MB. Se baja una vez y queda en datos/."""
    if not CATALOGO.exists():
        CATALOGO.parent.mkdir(exist_ok=True)
        r = httpx.get(URL_CATALOGO, timeout=120)
        r.raise_for_status()
        CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
    df = pd.read_csv(CATALOGO, sep=";", dtype=str).fillna("")
    df = df.rename(columns={"Código de serie": "codigo", "Categoría de serie": "categoria", "Grupo de serie": "grupo",
                            "Nombre de serie": "nombre", "Frecuencia": "frecuencia",
                            "Fecha de actualización": "actualizada", "Fecha de inicio": "inicio",
                            "Unidad de medida": "unidad", "Fuente": "origen",
                            "Descripción de la serie": "descripcion"})
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes)
    return df


def _ficha(codigo):
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    return {"codigo": f.codigo, "nombre": f"{f.grupo} - {f.nombre}", "categoria": f.categoria,
            "frecuencia": f.frecuencia, "inicio": f.inicio, "actualizada": f.actualizada}


@mcp.tool(annotations=SOLO_LECTURA)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series del BCRP por palabras: todas deben aparecer en la categoría, el grupo o el nombre.

    Ejemplos: "ipc 12 meses", "tipo de cambio interbancario venta", "reservas internacionales netas",
    "tasa de referencia", "cobre precio". frecuencia: "Diaria", "Mensual", "Trimestral" o "Anual".
    Devuelve el código, el nombre completo, la frecuencia y desde cuándo hay datos. Si no hay resultados,
    prueben con menos palabras.
    """
    df = catalogo()
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(re.escape(palabra))
    if frecuencia:
        m &= df.frecuencia.str.lower() == frecuencia.lower()
    # primero las series vigentes y, entre ellas, las de nombre más corto (las más generales)
    sel = df[m]
    orden = sel.assign(vieja=sel.actualizada < "2025", largo=(sel.grupo + sel.nombre).str.len())
    return [_ficha(c) for c in orden.sort_values(["vieja", "largo"]).head(limite).codigo]


# ---------------------------------------------------------------- fechas: lo que pide la API y lo que devuelve

def _fecha_api(fecha: str, frecuencia: str) -> str:
    """Convierte "2025-01", "2025-T1", "2026-10-01" o "2025" al formato que pide la API según la frecuencia."""
    f, frec = str(fecha).strip(), frecuencia.lower()
    if frec == "diaria":
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", f):
            return f
    elif frec == "mensual":
        if m := re.fullmatch(r"(\d{4})-(\d{1,2})", f):
            return f"{m[1]}-{int(m[2])}"
    elif frec == "trimestral":
        if m := re.fullmatch(r"(\d{4})-T?([1-4])", f, re.I):
            return f"{m[1]}-{m[2]}"
    elif frec == "anual":
        if m := re.fullmatch(r"(\d{4})(-.*)?", f):
            return m[1]
    ejemplos = {"diaria": "2026-10-01", "mensual": "2025-01", "trimestral": "2025-T1", "anual": "2025"}
    raise ToolError(f"Fecha {fecha!r} no válida para una serie {frecuencia}. Usen el formato {ejemplos.get(frec, '?')}.")


def _anio(aa: str) -> int:
    """Años de dos dígitos ("26" → 2026, "97" → 1997)."""
    a = 2000 + int(aa)
    return a if a <= date.today().year + 1 else a - 100


def _periodo(nombre: str) -> str:
    """Normaliza los nombres de la API: Ene.2025 → 2025-01, 01.Oct.26 → 2026-10-01, T1.25 → 2025-T1, 2025 → 2025."""
    n = nombre.strip()
    if m := re.fullmatch(r"(\d{2})\.(\w{3})\.(\d{2})", n):
        return f"{_anio(m[3])}-{MESES[m[2].lower()]:02d}-{m[1]}"
    if m := re.fullmatch(r"(\w{3})\.(\d{4})", n):
        return f"{m[2]}-{MESES[m[1].lower()]:02d}"
    if m := re.fullmatch(r"T([1-4])\.(\d{2})", n):
        return f"{_anio(m[2])}-T{m[1]}"
    if re.fullmatch(r"\d{4}", n):
        return n
    raise ToolError(f"Periodo con formato desconocido en la respuesta del BCRP: {nombre!r}")


@cache
def _descargar(url: str) -> dict:
    """Pide la URL a la API; si responde HTML (límite de pedidos) espera y reintenta. Guarda en caché lo bajado."""
    for intento in range(5):
        try:
            r = httpx.get(url, timeout=60, follow_redirects=True)
            if r.status_code == 200:
                return r.json()
        except (httpx.HTTPError, ValueError):
            pass
        time.sleep(2 * (intento + 1))
    raise ToolError(f"El BCRP no respondió con datos para {url}. Revisen el periodo (¿hay datos en ese rango?) "
                    "o reintenten en unos segundos.")


def _serie(codigo: str, desde: str, hasta: str) -> dict:
    ficha = _ficha(codigo)
    url = f"{API}/{codigo}/json/{_fecha_api(desde, ficha['frecuencia'])}/{_fecha_api(hasta, ficha['frecuencia'])}"
    respuesta = _descargar(url)
    datos = []
    for p in respuesta.get("periods", []):
        valor = p["values"][0]
        if valor in ("n.d.", "", None):
            continue
        datos.append({"periodo": _periodo(p["name"]), "valor": round(float(valor), 6)})
    if not datos:
        raise ToolError(f"La serie {codigo} no tiene datos entre {desde} y {hasta}.")
    return {"codigo": codigo, "nombre": ficha["nombre"], "frecuencia": ficha["frecuencia"], "datos": datos,
            "fuente": url}


@mcp.tool(annotations=SOLO_LECTURA)
def serie(codigo: str, desde: str, hasta: str) -> dict:
    """Descarga los datos oficiales de una serie del BCRP entre dos fechas (ambas incluidas).

    Formato de fechas según la frecuencia de la serie: mensual "2025-01", trimestral "2025-T1", anual "2025",
    diaria "2026-10-01". Devuelve {"codigo", "nombre", "frecuencia", "datos": [{"periodo", "valor"}], "fuente"};
    "fuente" es la URL de la API del BCRP para verificar la cifra. Los valores "n.d." se omiten.
    Ejemplo: serie("PN01770AM", "2019-01", "2024-12") → PBI mensual, índice 2007 = 100.
    """
    return _serie(codigo, desde, hasta)


def _punto(s: pd.Series, idx) -> dict:
    return {"periodo": idx, "valor": round(float(s[idx]), 6)}


@mcp.tool(annotations=SOLO_LECTURA)
def resumen(codigo: str, desde: str, hasta: str) -> dict:
    """Resume una serie del BCRP entre dos fechas: primer y último dato, cambio absoluto, variación porcentual,
    promedio, máximo y mínimo (con su periodo) y número de observaciones.

    Úsenla siempre que haya que calcular algo: así el modelo nunca hace cuentas a mano. Fechas como en `serie`.
    Ojo: si la serie ya es una tasa (por ejemplo inflación en %), "cambio" está en puntos porcentuales.
    """
    r = _serie(codigo, desde, hasta)
    s = pd.Series({d["periodo"]: d["valor"] for d in r["datos"]})
    primero, ultimo = float(s.iloc[0]), float(s.iloc[-1])
    return {"codigo": codigo, "nombre": r["nombre"], "frecuencia": r["frecuencia"],
            "primero": _punto(s, s.index[0]), "ultimo": _punto(s, s.index[-1]),
            "cambio": round(ultimo - primero, 6),
            "variacion_pct": round((ultimo / primero - 1) * 100, 4) if primero != 0 else None,
            "promedio": round(float(s.mean()), 6),
            "maximo": _punto(s, s.idxmax()), "minimo": _punto(s, s.idxmin()),
            "observaciones": int(len(s)), "fuente": r["fuente"]}


@mcp.tool(annotations=SOLO_LECTURA)
def comparar_periodos(codigo: str, desde_a: str, hasta_a: str, desde_b: str, hasta_b: str) -> dict:
    """Compara una misma serie del BCRP en dos intervalos de tiempo (A = base, B = comparación).

    Úsenla para preguntas del tipo «¿el PBI de 2024 ya superó al de 2019?» o «¿la inflación promedio de 2022 fue
    mayor que la de 2019?». Para cada intervalo devuelve el promedio, el mínimo, el máximo y el número de datos; y
    luego la diferencia de promedios (B − A) y la variación porcentual de B respecto de A. Fechas como en `serie`.
    Ejemplo: comparar_periodos("PN01770AM", "2019-01", "2019-12", "2024-01", "2024-12").
    """
    resumen_intervalo = {}
    for nombre, (desde, hasta) in {"a": (desde_a, hasta_a), "b": (desde_b, hasta_b)}.items():
        r = _serie(codigo, desde, hasta)
        s = pd.Series({d["periodo"]: d["valor"] for d in r["datos"]})
        resumen_intervalo[nombre] = {"desde": desde, "hasta": hasta, "promedio": round(float(s.mean()), 6),
                                     "minimo": _punto(s, s.idxmin()), "maximo": _punto(s, s.idxmax()),
                                     "observaciones": int(len(s)), "fuente": r["fuente"]}
    a, b = resumen_intervalo["a"]["promedio"], resumen_intervalo["b"]["promedio"]
    if resumen_intervalo["a"]["observaciones"] != resumen_intervalo["b"]["observaciones"]:
        advertencia = "Los intervalos tienen distinto número de datos: comparen con cuidado (estacionalidad)."
    else:
        advertencia = None
    return {"codigo": codigo, "nombre": _ficha(codigo)["nombre"], "periodo_a": resumen_intervalo["a"],
            "periodo_b": resumen_intervalo["b"], "diferencia_promedios": round(b - a, 6),
            "variacion_pct": round((b / a - 1) * 100, 4) if a != 0 else None, "advertencia": advertencia}


# ---------------------------------------------------------------- recurso y prompt

@mcp.resource("bcrp://serie/{codigo}", mime_type="application/json")
def ficha_serie(codigo: str) -> dict:
    """Ficha descriptiva de una serie del BCRP: nombre, categoría, frecuencia, unidad, fuente original,
    desde cuándo hay datos y fecha de última actualización."""
    ficha = _ficha(codigo)
    f = catalogo().query("codigo == @codigo").iloc[0]
    return {**ficha, "unidad": f.unidad, "origen": f.origen, "descripcion": f.descripcion,
            "consulta_web": f"https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/{codigo}/html"
            if ficha["frecuencia"] == "Mensual" else "https://estadisticas.bcrp.gob.pe/estadisticas/series/"}


@mcp.prompt
def informe(tema: str, desde: str = "2019", hasta: str = "2024") -> str:
    """Pide un informe breve y verificable sobre un indicador macroeconómico del BCRP."""
    return (f"Elabora un informe breve sobre «{tema}» en el Perú entre {desde} y {hasta} usando solo las herramientas "
            "del servidor bcrp. Pasos: 1) busca la serie con buscar_series y elige la más pertinente explicando por qué; "
            "2) calcula los números con resumen o comparar_periodos (no hagas cuentas a mano); 3) presenta una tabla con "
            "cada cifra, su código de serie, su periodo y la URL de la fuente; 4) interpreta en 3 a 5 líneas sin afirmar "
            "relaciones causales; 5) indica limitaciones (frecuencia, revisiones de datos, cobertura geográfica). Si una "
            "herramienta falla o no hay datos, dilo en lugar de estimar.")


if __name__ == "__main__":
    mcp.run()
