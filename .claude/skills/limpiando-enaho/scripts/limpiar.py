"""Limpia la ENAHO (INEI) y valida contra las cifras oficiales.

    uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024   # módulos 34 + 02
    uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2019   # solo módulo 34 (sumaria)

Entra:  datos/<codigo>-Modulo34.zip (y datos/966-Modulo02.zip para 2024)
Sale:   salidas/hogares_<anio>.parquet    un registro por hogar, con gasto real per cápita
        salidas/personas_2024.parquet     residentes habituales unidos a su hogar (solo 2024)
        salidas/validacion.txt            (2024) o salidas/validacion_<anio>.txt
        salidas/indicadores.csv           pobreza y Gini por año: nacional, área, Lima Metropolitana, departamento

Si una validación esencial falla, escribe el archivo de validación con el detalle y termina con código 1.
"""
import argparse
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
DATOS, SALIDAS = RAIZ / "datos", RAIZ / "salidas"
LLAVES = ["conglome", "vivienda", "hogar"]

# Código del INEI por año y cifras oficiales de referencia (pobreza monetaria, % de personas)
ANIOS = {
    2024: {"codigo": 966, "pobreza": 27.6, "residentes": 108_664, "urbano": 24.8, "rural": 39.3, "lima_metro": 28.2},
    2019: {"codigo": 687, "pobreza": 20.2},
}
TOLERANCIA_POBREZA = 0.1      # puntos porcentuales, según la consigna
TOLERANCIA_SECUNDARIA = 0.2   # urbano / rural / Lima: referencias redondeadas

COLS_SUMARIA = LLAVES + ["ubigeo", "dominio", "estrato", "pobreza", "mieperho", "gashog2d", "inghog2d", "ld",
                         "linea", "factor07"]
COLS_MIEMBROS = LLAVES + ["codperso", "p203", "p204", "p205", "p206", "p207", "p208a", "facpob07"]


# --------------------------------------------------------------------------------------------- lectura

def leer_stata(zip_path: Path, prefijo: str, columnas: list[str]) -> pd.DataFrame:
    """Lee el .dta que empieza con `prefijo` dentro del zip, sin convertir etiquetas y con llaves como texto."""
    if not zip_path.exists():
        sys.exit(f"ERROR: falta {zip_path.relative_to(RAIZ)}. Descárguenlo del INEI (ver README, sección 5).")
    with zipfile.ZipFile(zip_path) as zf:
        miembro = next((n for n in zf.namelist()
                        if Path(n).name.lower().startswith(prefijo) and n.lower().endswith(".dta")
                        and "12g" not in n.lower()), None)
        if miembro is None:
            sys.exit(f"ERROR: no encontré un archivo {prefijo}*.dta dentro de {zip_path.name}")
        with zf.open(miembro) as f:
            df = pd.read_stata(f, convert_categoricals=False)
    df.columns = df.columns.str.lower()                       # normalizar nombres (p. ej. "aÑo" → "año")
    faltan = [c for c in columnas if c not in df.columns]
    if faltan:
        sys.exit(f"ERROR: faltan columnas {faltan} en {miembro}")
    df = df[columnas].copy()
    for c in LLAVES + ["ubigeo", "codperso"]:                 # llaves como texto, sin perder ceros iniciales
        if c in df:
            df[c] = df[c].astype(str).str.strip()
    return df


# --------------------------------------------------------------------------------------------- indicadores

def media_ponderada(x, w) -> float:
    return float(np.average(x, weights=w))


def gini_ponderado(y, w) -> float:
    """Gini de y con pesos w (área bajo la curva de Lorenz por trapecios)."""
    y, w = np.asarray(y, float), np.asarray(w, float)
    orden = np.argsort(y)
    y, w = y[orden], w[orden]
    p = np.concatenate([[0], np.cumsum(w) / w.sum()])
    L = np.concatenate([[0], np.cumsum(w * y) / (w * y).sum()])
    return float(1 - np.sum((p[1:] - p[:-1]) * (L[1:] + L[:-1])))


def resumir(h: pd.DataFrame) -> dict:
    """Indicadores ponderados por personas (factor07 × mieperho) para un grupo de hogares."""
    w = h.peso_personas
    return {"pobreza_pct": round(100 * media_ponderada(h.pobre, w), 2),
            "pobreza_extrema_pct": round(100 * media_ponderada(h.pobre_extremo, w), 2),
            "gini_gasto": round(gini_ponderado(h.gasto_pc_real, w), 4),
            "gasto_pc_real_mensual": round(media_ponderada(h.gasto_pc_real, w), 1),
            "hogares_muestra": int(len(h)), "personas_expandidas": int(round(w.sum()))}


def tabla_indicadores(h: pd.DataFrame, anio: int) -> pd.DataFrame:
    filas = [{"nivel": "nacional", "codigo": "PE", "grupo": "Perú", **resumir(h)}]
    for urbano, nombre in [(True, "Urbano"), (False, "Rural")]:
        filas.append({"nivel": "area", "codigo": "U" if urbano else "R", "grupo": nombre,
                      **resumir(h[h.urbano == urbano])})
    filas.append({"nivel": "dominio", "codigo": "8", "grupo": "Lima Metropolitana",
                  **resumir(h[h.dominio == 8])})
    for ccdd, g in h.groupby("departamento"):
        filas.append({"nivel": "departamento", "codigo": ccdd, "grupo": ccdd, **resumir(g)})
    df = pd.DataFrame(filas)
    df.insert(0, "anio", anio)
    return df


# --------------------------------------------------------------------------------------------- validación

class Validacion:
    def __init__(self):
        self.lineas, self.fallas_esenciales = [], []

    def check(self, nombre, ok, detalle, esencial=True):
        estado = "APROBADA" if ok else ("FALLÓ" if esencial else "ADVERTENCIA")
        self.lineas.append(f"[{estado:11}] {nombre}: {detalle}")
        if not ok and esencial:
            self.fallas_esenciales.append(nombre)

    def info(self, texto):
        self.lineas.append(f"[{'INFO':11}] {texto}")


# --------------------------------------------------------------------------------------------- pipeline

def main(anio: int):
    if anio not in ANIOS:
        sys.exit(f"ERROR: año {anio} no configurado. Disponibles: {sorted(ANIOS)}")
    ref, v = ANIOS[anio], Validacion()
    SALIDAS.mkdir(exist_ok=True)

    # 1. Sumaria (hogares)
    h = leer_stata(DATOS / f"{ref['codigo']}-Modulo34.zip", "sumaria", COLS_SUMARIA)
    v.check("Llaves de hogar únicas en la sumaria", not h.duplicated(LLAVES).any(),
            f"{len(h):,} hogares, {h.duplicated(LLAVES).sum()} duplicados")
    v.check("Factores de expansión válidos", h.factor07.notna().all() and (h.factor07 > 0).all(),
            f"factor07 nulos={h.factor07.isna().sum()}, no positivos={(h.factor07 <= 0).sum()}")

    # 2. Indicadores del hogar
    h["departamento"] = h.ubigeo.str[:2]
    h["urbano"] = h.estrato <= 5
    h["pobre"] = (h.pobreza <= 2).astype(int)
    h["pobre_extremo"] = (h.pobreza == 1).astype(int)
    h["peso_personas"] = h.factor07 * h.mieperho
    h["gasto_pc_real"] = h.gashog2d / (12 * h.mieperho * h.ld)    # S/ mensuales, a precios de Lima Metropolitana

    deps = sorted(h.departamento.unique())
    esperados = [f"{i:02d}" for i in range(1, 26)]
    v.check("25 códigos territoriales (01–25)", deps == esperados,
            f"{len(deps)} códigos encontrados" + ("" if deps == esperados else f": {deps}"))
    v.check("Lima (15) y Callao (07) separados", {"07", "15"} <= set(deps), "ambos presentes" if {"07", "15"} <= set(deps) else "falta alguno")

    pob = 100 * media_ponderada(h.pobre, h.peso_personas)
    v.check(f"Pobreza monetaria nacional ≈ {ref['pobreza']} % (±{TOLERANCIA_POBREZA} pp)",
            abs(pob - ref["pobreza"]) <= TOLERANCIA_POBREZA,
            f"{pob:.2f} % con sumaria y factor07 × mieperho (diferencia {pob - ref['pobreza']:+.2f} pp)")

    # 3. Personas (solo cuando existe el módulo 02 del año)
    p = None
    if anio == 2024:
        p = leer_stata(DATOS / f"{ref['codigo']}-Modulo02.zip", "enaho01", COLS_MIEMBROS)
        v.check("Llaves de persona únicas en el módulo 02", not p.duplicated(LLAVES + ["codperso"]).any(),
                f"{len(p):,} filas")
        residente = ((p.p204 == 1) & (p.p205 == 2)) | ((p.p204 == 2) & (p.p206 == 1))
        p = p[residente].copy()
        v.check(f"Residentes habituales = {ref['residentes']:,}", len(p) == ref["residentes"], f"{len(p):,} personas")

        cols_hogar = LLAVES + ["departamento", "urbano", "dominio", "estrato", "pobreza", "pobre", "pobre_extremo",
                               "mieperho", "gasto_pc_real", "factor07"]
        n_antes = len(p)
        try:
            p = p.merge(h[cols_hogar], on=LLAVES, how="left", validate="m:1", indicator=True)
        except pd.errors.MergeError as e:
            v.check("Unión personas–hogares m:1", False, str(e))
            p = None
        if p is not None:
            v.check("Unión personas–hogares m:1 sin duplicar filas", len(p) == n_antes,
                    f"{n_antes:,} antes, {len(p):,} después")
            sin_hogar = int((p._merge != "both").sum())
            v.check("Todas las personas encuentran su hogar", sin_hogar == 0, f"{sin_hogar} sin hogar")
            p = p.drop(columns="_merge")
            v.check("facpob07 válido", p.facpob07.notna().all() and (p.facpob07 > 0).all(),
                    f"nulos={p.facpob07.isna().sum()}")
            pob_p = 100 * media_ponderada(p.pobre, p.facpob07)
            v.check(f"Pobreza con personas y facpob07 ≈ {ref['pobreza']} % (±{TOLERANCIA_POBREZA} pp)",
                    abs(pob_p - ref["pobreza"]) <= TOLERANCIA_POBREZA, f"{pob_p:.2f} %")
            sin_pond = 100 * p.pobre.mean()
            v.info(f"Control: promedio simple SIN ponderar = {sin_pond:.2f} % (no usar; muestra por qué se pondera)")
            p["sexo"] = p.p207.map({1: "Hombre", 2: "Mujer"})
            p["edad"] = p.p208a
            p["jefe_hogar"] = p.p203 == 1

    # 4. Referencias secundarias (no detienen el proceso)
    ind = tabla_indicadores(h, anio)
    for clave, codigo, nombre in [("urbano", "U", "Pobreza urbana"), ("rural", "R", "Pobreza rural"),
                                  ("lima_metro", "8", "Pobreza Lima Metropolitana")]:
        if clave in ref:
            val = ind.query("codigo == @codigo").pobreza_pct.iloc[0]
            v.check(f"{nombre} ≈ {ref[clave]} %", abs(val - ref[clave]) <= TOLERANCIA_SECUNDARIA, f"{val:.2f} %",
                    esencial=False)
    g = ind.query("nivel == 'nacional'").gini_gasto.iloc[0]
    v.check("Gini del gasto real per cápita plausible (0.2–0.6)", 0.2 < g < 0.6, f"{g:.4f}", esencial=False)

    # 5. Escribir la validación; guardar las bases solo si no hubo fallas esenciales
    nombre_val = "validacion.txt" if anio == 2024 else f"validacion_{anio}.txt"
    aprobadas = sum(l.startswith("[APROBADA") for l in v.lineas)
    total = sum(not l.startswith("[INFO") for l in v.lineas)
    encabezado = [f"Validación ENAHO {anio} (código INEI {ref['codigo']})",
                  f"Generado: {datetime.now():%Y-%m-%d %H:%M} con {Path(__file__).relative_to(RAIZ)}",
                  f"Resultado: {aprobadas}/{total} verificaciones aprobadas; "
                  + ("SIN fallas esenciales" if not v.fallas_esenciales else f"FALLAS ESENCIALES: {v.fallas_esenciales}"),
                  ""]
    (SALIDAS / nombre_val).write_text("\n".join(encabezado + v.lineas) + "\n", encoding="utf-8")
    print("\n".join(encabezado + v.lineas))

    if v.fallas_esenciales:
        sys.exit(f"\nDETENIDO: fallaron validaciones esenciales {v.fallas_esenciales}. "
                 "No se guardaron bases ni indicadores; corrijan el procesamiento.")

    h.to_parquet(SALIDAS / f"hogares_{anio}.parquet", index=False)
    if p is not None and anio == 2024:
        p.to_parquet(SALIDAS / "personas_2024.parquet", index=False)
    ruta_ind = SALIDAS / "indicadores.csv"
    if ruta_ind.exists():
        previo = pd.read_csv(ruta_ind, dtype={"codigo": str})
        ind = pd.concat([previo[previo.anio != anio], ind], ignore_index=True)
    ind.sort_values(["anio", "nivel", "codigo"]).to_csv(ruta_ind, index=False)
    print(f"\nGuardado: salidas/hogares_{anio}.parquet"
          + (", salidas/personas_2024.parquet" if anio == 2024 else "") + ", salidas/indicadores.csv")


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--anio", type=int, default=2024)
    main(a.parse_args().anio)
