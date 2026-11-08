"""Mapa coroplético de la pobreza monetaria por departamento (ENAHO, INEI).

    uv run .claude/skills/mapeando-enaho/scripts/mapear.py pobreza   # pobreza 2024 → mapas/pobreza_departamento_2024.png
    uv run .claude/skills/mapeando-enaho/scripts/mapear.py cambio    # cambio 2019→2024 → mapas/cambio_pobreza_2019_2024.png
    uv run .claude/skills/mapeando-enaho/scripts/mapear.py todos

Une indicadores y geometrías por código oficial: departamento (= ubigeo[:2]) con FIRST_IDDP, ambos como texto.
Exige las 25 unidades con dato (Lima 15 y Callao 07 separados) y compara la pobreza 2024 con
referencias/pobreza_departamento_2024.csv (Sesión 16). Escribe salidas/validacion_mapa.txt.
"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

RAIZ = Path(__file__).resolve().parents[4]
SALIDAS, MAPAS = RAIZ / "salidas", RAIZ / "mapas"
GEOJSON = RAIZ / "datos" / "peru_departamental_simple.geojson"
URL_GEOJSON = ("https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/"
               "Data/peru_departamental_simple.geojson")
REFERENCIA = RAIZ / "referencias" / "pobreza_departamento_2024.csv"

SUPERFICIE, TEXTO, TEXTO_2, BORDE = "#fcfcfb", "#0b0b0b", "#52514e", "#fcfcfb"
# Secuencial: un solo tono (azul), de claro a oscuro
AZULES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
# Divergente: azul (bajó) ↔ gris neutro ↔ rojo (subió)
DIVERGENTE = ["#256abf", "#86b6ef", "#f0efec", "#f2a3a2", "#e34948", "#a8302f"]


def _exigir(ruta: Path) -> Path:
    if not ruta.exists():
        sys.exit(f"Falta {ruta.relative_to(RAIZ)}. Ejecuta primero la skill limpiando-enaho "
                 "(uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024 y --anio 2019).")
    return ruta


def geometria() -> gpd.GeoDataFrame:
    if not GEOJSON.exists():
        sys.exit(f"Falta {GEOJSON.relative_to(RAIZ)}. Descárguenlo de {URL_GEOJSON}")
    g = gpd.read_file(GEOJSON)
    g["FIRST_IDDP"] = g.FIRST_IDDP.astype(str).str.zfill(2)
    return g


def unir(valores: pd.DataFrame, columna: str, validacion: list[str], mapa: str) -> gpd.GeoDataFrame:
    """Une por código (nunca por nombre) y exige 25 departamentos con dato."""
    g = geometria().merge(valores, left_on="FIRST_IDDP", right_on="codigo", how="left", validate="1:1")
    sin_dato = g[g[columna].isna()].NOMBDEP.tolist()
    ok = len(g) == 25 and not sin_dato and {"07", "15"} <= set(g.FIRST_IDDP)
    validacion.append(f"[{'APROBADA' if ok else 'FALLÓ':9}] Unión ubigeo[:2] = FIRST_IDDP: {len(g)} geometrías, "
                      f"{len(g) - len(sin_dato)} con dato" + (f"; sin dato: {sin_dato}" if sin_dato else "")
                      + "; Lima (15) y Callao (07) separados")
    if not ok:
        escribir_validacion(validacion, mapa)
        sys.exit(f"DETENIDO: la unión territorial no tiene 25 departamentos con dato ({sin_dato}).")
    return g


def escribir_validacion(lineas, mapa):
    """Reescribe solo la sección de este mapa en salidas/validacion_mapa.txt y conserva la del otro mapa."""
    SALIDAS.mkdir(exist_ok=True)
    archivo = SALIDAS / "validacion_mapa.txt"
    secciones = {}
    if archivo.exists():
        actual = None
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            if linea.startswith("## "):
                actual = linea[3:].strip()
                secciones[actual] = []
            elif actual and linea.strip():
                secciones[actual].append(linea)
    secciones[mapa] = lineas
    cuerpo = "\n\n".join(f"## {m}\n" + "\n".join(secciones[m]) for m in ("pobreza", "cambio") if m in secciones)
    archivo.write_text("Validación del mapa departamental\n\n" + cuerpo + "\n", encoding="utf-8")


def dibujar(g, columna, colores, cortes, etiquetas, titulo, subtitulo, leyenda, fuente, archivo):
    fig, ax = plt.subplots(figsize=(7, 9), facecolor=SUPERFICIE)
    ax.set_facecolor(SUPERFICIE)
    cmap, norm = ListedColormap(colores), BoundaryNorm(cortes, len(colores))
    g.plot(column=columna, cmap=cmap, norm=norm, ax=ax, edgecolor=BORDE, linewidth=0.8)
    # Valor sobre cada departamento (texto oscuro o claro según el relleno)
    for _, f in g.iterrows():
        p = f.geometry.representative_point()
        i = int(np.clip(np.searchsorted(cortes, f[columna], side="right") - 1, 0, len(colores) - 1))
        oscuro = colores[i] in ("#256abf", "#184f95", "#0d366b", "#3987e5", "#e34948", "#a8302f")
        txt = f"{f[columna]:+.0f}" if columna.startswith("cambio") else f"{f[columna]:.0f}"
        if f.FIRST_IDDP == "07":   # Callao es muy pequeño: etiqueta en el mar con línea guía
            ax.annotate(f"Callao {txt}", xy=(p.x, p.y), xytext=(p.x - 2.6, p.y - 0.3), fontsize=7.5, color=TEXTO,
                        ha="right", va="center", arrowprops=dict(arrowstyle="-", color=TEXTO_2, linewidth=0.7))
            continue
        ax.text(p.x, p.y, txt, ha="center", va="center", fontsize=7.5, color="white" if oscuro else TEXTO)
    ax.set_axis_off()
    ax.legend(handles=[Patch(facecolor=c, edgecolor="none", label=e) for c, e in zip(colores, etiquetas)],
              title=leyenda, loc="lower left", frameon=False, fontsize=8.5, title_fontsize=9, labelcolor=TEXTO)
    fig.text(0.04, 0.975, titulo, ha="left", va="top", fontsize=13, weight="bold", color=TEXTO, wrap=True)
    fig.text(0.04, 0.935, subtitulo, ha="left", va="top", fontsize=9.5, color=TEXTO_2, linespacing=1.3)
    fig.text(0.04, 0.015, fuente, ha="left", va="bottom", fontsize=7.5, color=TEXTO_2)
    fig.subplots_adjust(top=0.88, bottom=0.04, left=0.02, right=0.98)
    MAPAS.mkdir(exist_ok=True)
    fig.savefig(MAPAS / archivo, dpi=200, facecolor=SUPERFICIE)
    plt.close(fig)
    print(f"Guardado mapas/{archivo}")


def mapa_pobreza(validacion):
    ind = pd.read_csv(_exigir(SALIDAS / "indicadores.csv"), dtype={"codigo": str})
    v = ind.query("anio == 2024 and nivel == 'departamento'")[["codigo", "pobreza_pct"]]
    g = unir(v, "pobreza_pct", validacion, "pobreza")

    ref = pd.read_csv(REFERENCIA, dtype={"ccdd": str}).rename(columns={"pobreza_pct": "referencia"})
    c = g[["FIRST_IDDP", "NOMBDEP", "pobreza_pct"]].merge(ref, left_on="FIRST_IDDP", right_on="ccdd")
    c["diferencia"] = (c.pobreza_pct.round(1) - c.referencia).round(2)
    maxdif = c.diferencia.abs().max()
    validacion.append(f"[{'APROBADA' if maxdif <= 0.1 else 'FALLÓ':9}] Comparación con referencias/"
                      f"pobreza_departamento_2024.csv (Sesión 16): {len(c)}/25 departamentos, "
                      f"máxima diferencia {maxdif:.1f} pp (tolerancia 0.1 pp, redondeo)")
    c[["FIRST_IDDP", "NOMBDEP", "pobreza_pct", "referencia", "diferencia"]].to_csv(
        SALIDAS / "comparacion_mapa_referencia.csv", index=False)

    cortes = [0, 10, 15, 20, 25, 30, 40, 100]
    etiquetas = ["Menos de 10", "10 a 15", "15 a 20", "20 a 25", "25 a 30", "30 a 40", "40 o más"]
    alto, bajo = g.loc[g.pobreza_pct.idxmax()], g.loc[g.pobreza_pct.idxmin()]
    dibujar(g, "pobreza_pct", AZULES, cortes, etiquetas,
            "Pobreza monetaria por departamento, 2024",
            f"Mayor en {alto.NOMBDEP.title()} ({alto.pobreza_pct:.1f} %), menor en {bajo.NOMBDEP.title()} "
            f"({bajo.pobreza_pct:.1f} %).\nNacional: {ind.query('anio == 2024 and nivel == \"nacional\"').pobreza_pct.iloc[0]:.1f} %. "
            "Lima y Callao se muestran por separado.",
            "% de personas en pobreza", "Fuente: INEI, ENAHO 2024 (estimaciones ponderadas). Límites: repositorio "
            "del curso. Elaboración propia.", "pobreza_departamento_2024.png")


def mapa_cambio(validacion):
    ind = pd.read_csv(_exigir(SALIDAS / "indicadores.csv"), dtype={"codigo": str})
    if not {2019, 2024} <= set(ind.anio):
        sys.exit("indicadores.csv no tiene 2019 y 2024. Ejecuta limpiar.py --anio 2019 y --anio 2024.")
    w = ind.query("nivel == 'departamento'").pivot(index="codigo", columns="anio", values="pobreza_pct")
    v = (w[2024] - w[2019]).rename("cambio_pp").reset_index()
    g = unir(v, "cambio_pp", validacion, "cambio")
    colores = [DIVERGENTE[0], DIVERGENTE[1], DIVERGENTE[3], DIVERGENTE[4], DIVERGENTE[5]]
    cortes = [-100, -5, 0, 5, 10, 100]
    etiquetas = ["Bajó más de 5 pp", "Bajó hasta 5 pp", "Subió hasta 5 pp", "Subió 5 a 10 pp", "Subió más de 10 pp"]
    subio = int((g.cambio_pp > 0).sum())
    dibujar(g, "cambio_pp", colores, cortes, etiquetas,
            "Cambio de la pobreza monetaria, 2019 → 2024",
            f"La pobreza subió en {subio} de 25 departamentos (rojo) y bajó en {25 - subio} (azul).\n"
            "Cifras en puntos porcentuales; cambios pequeños pueden deberse al error muestral.",
            "Cambio en puntos porcentuales", "Fuente: INEI, ENAHO 2019 y 2024 (estimaciones ponderadas). "
            "Elaboración propia.", "cambio_pobreza_2019_2024.png")


if __name__ == "__main__":
    pedido = (sys.argv[1:] or ["pobreza"])[0]
    if pedido not in ("pobreza", "cambio", "todos"):
        sys.exit("Opciones: pobreza, cambio o todos.")
    for mapa, funcion in (("pobreza", mapa_pobreza), ("cambio", mapa_cambio)):
        if pedido in (mapa, "todos"):
            validacion = []
            funcion(validacion)
            escribir_validacion(validacion, mapa)
            print("\n".join(validacion))
