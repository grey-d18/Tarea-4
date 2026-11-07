"""Gráficos de pobreza y desigualdad con la ENAHO (INEI), siempre con estimaciones ponderadas.

    uv run .claude/skills/graficando-enaho/scripts/graficar.py area           # urbano vs. rural, 2024
    uv run .claude/skills/graficando-enaho/scripts/graficar.py sexo           # por sexo de la persona y del jefe, 2024
    uv run .claude/skills/graficando-enaho/scripts/graficar.py edad           # por grupo de edad, 2024
    uv run .claude/skills/graficando-enaho/scripts/graficar.py departamento   # 25 departamentos, 2024
    uv run .claude/skills/graficando-enaho/scripts/graficar.py comparacion    # pobreza 2019 vs. 2024 por ámbito
    uv run .claude/skills/graficando-enaho/scripts/graficar.py gini           # Gini 2019 vs. 2024 por ámbito
    uv run .claude/skills/graficando-enaho/scripts/graficar.py cambio         # cambio 2019→2024 por departamento
    uv run .claude/skills/graficando-enaho/scripts/graficar.py todos

Cada gráfico se guarda en figuras/<nombre>.png (200 dpi) junto con figuras/<nombre>.csv con los valores graficados.
Lee las salidas de la skill limpiando-enaho; si faltan, termina pidiendo ejecutarla primero.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
SALIDAS, FIGURAS = RAIZ / "salidas", RAIZ / "figuras"

# Paleta (referencia validada de la guía de visualización; tema claro)
SUPERFICIE, TEXTO, TEXTO_2, GRILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
AZUL, NARANJA = "#2a78d6", "#eb6834"           # serie principal / segunda serie (categorías 1 y 2)
COLOR_ANIO = {2019: NARANJA, 2024: AZUL}

DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho", "06": "Cajamarca",
    "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco", "11": "Ica", "12": "Junín",
    "13": "La Libertad", "14": "Lambayeque", "15": "Lima", "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua",
    "19": "Pasco", "20": "Piura", "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali"}
FUENTE = "Fuente: INEI, ENAHO {anios}. Estimaciones ponderadas con factores de expansión. Elaboración propia."


# --------------------------------------------------------------------------------------------- datos

def _exigir(ruta: Path) -> Path:
    if not ruta.exists():
        sys.exit(f"Falta {ruta.relative_to(RAIZ)}. Ejecuta primero la skill limpiando-enaho "
                 "(uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024 y --anio 2019).")
    return ruta


def indicadores(anios=(2024,)) -> pd.DataFrame:
    df = pd.read_csv(_exigir(SALIDAS / "indicadores.csv"), dtype={"codigo": str})
    faltan = set(anios) - set(df.anio)
    if faltan:
        sys.exit(f"indicadores.csv no tiene el año {sorted(faltan)}. Ejecuta limpiar.py --anio {min(faltan)}.")
    return df


def personas() -> pd.DataFrame:
    return pd.read_parquet(_exigir(SALIDAS / "personas_2024.parquet"))


def tasa(df: pd.DataFrame, grupo: str) -> pd.DataFrame:
    """Pobreza ponderada con facpob07 por grupo (personas 2024)."""
    g = df.groupby(grupo, observed=True)
    return pd.DataFrame({"pobreza_pct": g.apply(lambda x: 100 * np.average(x.pobre, weights=x.facpob07),
                                                include_groups=False).round(2),
                         "personas_muestra": g.size()}).reset_index()


# --------------------------------------------------------------------------------------------- estilo

def lienzo(ancho=8, alto=4.5):
    fig, ax = plt.subplots(figsize=(ancho, alto), facecolor=SUPERFICIE)
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(GRILLA)
    ax.tick_params(colors=TEXTO_2, length=0)
    return fig, ax


def titular(fig, titulo, subtitulo, anios):
    """Título y subtítulo partidos en líneas según el ancho; reserva el espacio superior que ocupan."""
    import textwrap
    ancho, alto = fig.get_size_inches()
    t = textwrap.fill(titulo, width=int(ancho * 8.2))
    st = textwrap.fill(subtitulo, width=int(ancho * 12.5))
    y = 1 - 0.22 / alto
    fig.text(0.02, y, t, ha="left", va="top", fontsize=13, weight="bold", color=TEXTO, linespacing=1.25)
    y -= (0.27 * (t.count("\n") + 1) + 0.08) / alto
    fig.text(0.02, y, st, ha="left", va="top", fontsize=9.5, color=TEXTO_2, linespacing=1.3)
    y -= (0.2 * (st.count("\n") + 1) + 0.45) / alto
    fig.subplots_adjust(top=y)
    fig.text(0.02, 0.015, FUENTE.format(anios=anios), ha="left", va="bottom", fontsize=7.5, color=TEXTO_2)


def guardar(fig, nombre, tabla: pd.DataFrame):
    FIGURAS.mkdir(exist_ok=True)
    fig.savefig(FIGURAS / f"{nombre}.png", dpi=200, facecolor=SUPERFICIE)
    tabla.to_csv(FIGURAS / f"{nombre}.csv", index=False)
    plt.close(fig)
    print(f"Guardado figuras/{nombre}.png y figuras/{nombre}.csv")
    print(tabla.to_string(index=False))


def barras_verticales(ax, etiquetas, valores, color=AZUL, fmt="{:.1f} %"):
    x = np.arange(len(valores))
    ax.bar(x, valores, color=color, width=0.55, edgecolor=SUPERFICIE, linewidth=2)
    for xi, v in zip(x, valores):
        ax.text(xi, v + max(valores) * 0.02, fmt.format(v), ha="center", va="bottom", fontsize=10, color=TEXTO)
    ax.set_xticks(x, etiquetas, fontsize=10, color=TEXTO)
    ax.set_yticks([])
    ax.set_ylim(0, max(valores) * 1.18)


def barras_agrupadas(ax, etiquetas, series: dict, fmt="{:.1f} %"):
    x, ancho = np.arange(len(etiquetas)), 0.36
    tope = max(max(v) for v in series.values())
    for i, (anio, valores) in enumerate(series.items()):
        pos = x + (i - 0.5) * ancho
        ax.bar(pos, valores, width=ancho, color=COLOR_ANIO[anio], edgecolor=SUPERFICIE, linewidth=2, label=str(anio))
        for p, v in zip(pos, valores):
            ax.text(p, v + tope * 0.02, fmt.format(v), ha="center", va="bottom", fontsize=9, color=TEXTO)
    ax.set_xticks(x, etiquetas, fontsize=10, color=TEXTO)
    ax.set_yticks([])
    ax.set_ylim(0, tope * 1.2)
    ax.legend(frameon=False, loc="upper right", fontsize=9, labelcolor=TEXTO)


# --------------------------------------------------------------------------------------------- gráficos

def g_area():
    i = indicadores().query("anio == 2024 and nivel in ['nacional', 'area']")
    t = i.assign(grupo=i.grupo.replace({"Perú": "Nacional"}))[["grupo", "pobreza_pct", "hogares_muestra"]]
    t = t.set_index("grupo").loc[["Nacional", "Urbano", "Rural"]].reset_index()
    fig, ax = lienzo(7, 4.5)
    barras_verticales(ax, t.grupo, t.pobreza_pct.tolist())
    rur, urb = t.pobreza_pct.iloc[2], t.pobreza_pct.iloc[1]
    titular(fig, f"La pobreza rural ({rur:.1f} %) supera en {rur - urb:.1f} puntos a la urbana ({urb:.1f} %)",
            "Pobreza monetaria según área de residencia, Perú 2024 (% de personas)", "2024")
    fig.subplots_adjust(bottom=0.14)
    guardar(fig, "pobreza_area_2024", t)


def g_sexo():
    p = personas()
    jefes = p[p.jefe_hogar][["conglome", "vivienda", "hogar", "sexo"]].rename(columns={"sexo": "sexo_jefe"})
    p = p.merge(jefes, on=["conglome", "vivienda", "hogar"], how="left", validate="m:1")
    a = tasa(p, "sexo").assign(grupo=lambda d: d.sexo.map({"Hombre": "Hombres", "Mujer": "Mujeres"}))
    b = tasa(p, "sexo_jefe").assign(grupo=lambda d: "Hogar con jefe " + d.sexo_jefe.str.lower())
    t = pd.concat([a, b])[["grupo", "pobreza_pct", "personas_muestra"]]
    fig, ax = lienzo(8, 4.5)
    barras_verticales(ax, [g.replace("Hogar con ", "Hogar con\n") for g in t.grupo], t.pobreza_pct.tolist())
    d_sexo = abs(a.pobreza_pct.iloc[0] - a.pobreza_pct.iloc[1]); d_jefe = abs(b.pobreza_pct.iloc[0] - b.pobreza_pct.iloc[1])
    titular(fig, f"Brecha por sexo de {d_sexo:.1f} puntos; según el sexo del jefe(a) de hogar, {d_jefe:.1f} puntos",
            "Pobreza monetaria según sexo de la persona y del jefe(a) de hogar, Perú 2024 (% de personas)", "2024")
    fig.subplots_adjust(bottom=0.17)
    guardar(fig, "pobreza_sexo_2024", t)


def g_edad():
    p = personas()
    p["grupo"] = pd.cut(p.edad, [-1, 14, 29, 44, 64, 200], labels=["0–14", "15–29", "30–44", "45–64", "65 y más"])
    t = tasa(p, "grupo")
    fig, ax = lienzo(8, 4.5)
    barras_verticales(ax, t.grupo.astype(str), t.pobreza_pct.tolist())
    mayor = t.loc[t.pobreza_pct.idxmax()]
    titular(fig, f"El grupo de {mayor.grupo} años tiene la mayor pobreza monetaria ({mayor.pobreza_pct:.1f} %)",
            "Pobreza monetaria según grupo de edad, Perú 2024 (% de personas)", "2024")
    fig.subplots_adjust(bottom=0.14)
    guardar(fig, "pobreza_edad_2024", t)


def g_departamento():
    i = indicadores()
    nac = i.query("anio == 2024 and nivel == 'nacional'").pobreza_pct.iloc[0]
    t = i.query("anio == 2024 and nivel == 'departamento'").assign(departamento=lambda d: d.codigo.map(DEPARTAMENTOS))
    t = t.sort_values("pobreza_pct")[["codigo", "departamento", "pobreza_pct", "hogares_muestra"]]
    fig, ax = lienzo(8, 8.5)
    ax.spines["bottom"].set_visible(False)
    y = np.arange(len(t))
    ax.barh(y, t.pobreza_pct, color=AZUL, height=0.7, edgecolor=SUPERFICIE, linewidth=2)
    for yi, v in zip(y, t.pobreza_pct):
        ax.text(v + 0.6, yi, f"{v:.1f}", va="center", fontsize=8.5, color=TEXTO, zorder=3,
                bbox=dict(facecolor=SUPERFICIE, edgecolor="none", pad=0.6))
    ax.axvline(nac, color=TEXTO_2, linestyle="--", linewidth=1, zorder=0)
    ax.text(nac + 0.4, len(t) - 0.2, f"Nacional {nac:.1f} %", fontsize=8.5, color=TEXTO_2, va="bottom")
    ax.set_yticks(y, t.departamento, fontsize=9, color=TEXTO)
    ax.set_xticks([])
    ax.set_xlim(0, t.pobreza_pct.max() * 1.12)
    ax.set_ylim(-0.6, len(t) + 0.4)
    alto, bajo = t.iloc[-1], t.iloc[0]
    titular(fig, f"{alto.departamento} tiene la mayor pobreza ({alto.pobreza_pct:.1f} %) y {bajo.departamento} la menor "
                 f"({bajo.pobreza_pct:.1f} %)",
            "Pobreza monetaria por departamento, Perú 2024 (% de personas). Lima incluye Lima Metropolitana y "
            "provincias; Callao, aparte.", "2024")
    fig.subplots_adjust(bottom=0.05, left=0.18)
    guardar(fig, "pobreza_departamento_2024", t)


AMBITOS = [("PE", "Nacional"), ("U", "Urbano"), ("R", "Rural"), ("8", "Lima\nMetropolitana")]


def _por_ambito(valor):
    i = indicadores((2019, 2024)).query("nivel in ['nacional', 'area', 'dominio']")
    t = i.pivot(index="codigo", columns="anio", values=valor).loc[[c for c, _ in AMBITOS]]
    t.insert(0, "ambito", [n.replace("\n", " ") for _, n in AMBITOS])
    t["cambio"] = (t[2024] - t[2019]).round(4)
    return t.reset_index().rename(columns={2019: f"{valor}_2019", 2024: f"{valor}_2024"})


def g_comparacion():
    t = _por_ambito("pobreza_pct")
    fig, ax = lienzo(8, 4.8)
    barras_agrupadas(ax, [n for _, n in AMBITOS], {2019: t.pobreza_pct_2019.tolist(), 2024: t.pobreza_pct_2024.tolist()})
    c = t.set_index("codigo").cambio
    titular(fig, f"2019→2024: la pobreza urbana cambió {c['U']:+.1f} pp, la rural {c['R']:+.1f} pp "
                 f"y la de Lima Metropolitana {c['8']:+.1f} pp",
            "Pobreza monetaria por ámbito, Perú 2019 y 2024 (% de personas)", "2019 y 2024")
    fig.subplots_adjust(bottom=0.15)
    guardar(fig, "pobreza_2019_vs_2024", t)


def g_gini():
    t = _por_ambito("gini_gasto")
    fig, ax = lienzo(8, 4.8)
    barras_agrupadas(ax, [n for _, n in AMBITOS], {2019: t.gini_gasto_2019.tolist(), 2024: t.gini_gasto_2024.tolist()},
                     fmt="{:.3f}")
    cg = t.set_index("codigo").cambio["PE"]
    titular(fig, f"El Gini nacional del gasto pasó de {t.gini_gasto_2019.iloc[0]:.3f} a {t.gini_gasto_2024.iloc[0]:.3f} "
                 f"({'bajó' if cg < 0 else 'subió'} {abs(cg):.3f})",
            "Coeficiente de Gini del gasto real per cápita, Perú 2019 y 2024 (0 = igualdad total, 1 = máxima)",
            "2019 y 2024")
    fig.subplots_adjust(bottom=0.15)
    guardar(fig, "gini_2019_vs_2024", t)


def g_cambio():
    i = indicadores((2019, 2024)).query("nivel == 'departamento'")
    t = i.pivot(index="codigo", columns="anio", values="pobreza_pct").reset_index()
    t.columns = ["codigo", "pobreza_2019", "pobreza_2024"]
    t["departamento"] = t.codigo.map(DEPARTAMENTOS)
    t["cambio_pp"] = (t.pobreza_2024 - t.pobreza_2019).round(2)
    t = t.sort_values("cambio_pp")[["codigo", "departamento", "pobreza_2019", "pobreza_2024", "cambio_pp"]]
    fig, ax = lienzo(8, 8.5)
    ax.spines["bottom"].set_visible(False)
    y = np.arange(len(t))
    ax.hlines(y, t.pobreza_2019, t.pobreza_2024, color=GRILLA, linewidth=2.5, zorder=1)
    ax.scatter(t.pobreza_2019, y, s=46, color=NARANJA, zorder=2, label="2019", edgecolor=SUPERFICIE, linewidth=1.5)
    ax.scatter(t.pobreza_2024, y, s=46, color=AZUL, zorder=3, label="2024", edgecolor=SUPERFICIE, linewidth=1.5)
    for yi, (_, f) in zip(y, t.iterrows()):
        ax.text(max(f.pobreza_2019, f.pobreza_2024) + 1, yi, f"{f.cambio_pp:+.1f} pp", va="center", fontsize=8,
                color=TEXTO_2)
    ax.set_yticks(y, t.departamento, fontsize=9, color=TEXTO)
    ax.tick_params(axis="x", labelsize=8.5, colors=TEXTO_2)
    ax.set_xlim(0, 55)
    ax.grid(axis="x", color=GRILLA, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper right", fontsize=9, labelcolor=TEXTO)
    ax.set_xlabel("% de personas en pobreza monetaria", fontsize=9, color=TEXTO_2)
    titular(fig, f"La pobreza subió en {(t.cambio_pp > 0).sum()} de {len(t)} departamentos entre 2019 y 2024",
            "Puntos: pobreza en 2019 (naranja) y 2024 (azul); a la derecha, el cambio en puntos porcentuales. "
            "Diferencias pequeñas pueden deberse al error muestral.", "2019 y 2024")
    fig.subplots_adjust(bottom=0.08, left=0.18)
    guardar(fig, "pobreza_cambio_departamento", t)


GRAFICOS = {"area": g_area, "sexo": g_sexo, "edad": g_edad, "departamento": g_departamento,
            "comparacion": g_comparacion, "gini": g_gini, "cambio": g_cambio}

if __name__ == "__main__":
    pedido = sys.argv[1:] or ["todos"]
    nombres = list(GRAFICOS) if pedido == ["todos"] else pedido
    desconocidos = [n for n in nombres if n not in GRAFICOS]
    if desconocidos:
        sys.exit(f"Gráfico desconocido {desconocidos}. Opciones: {', '.join(GRAFICOS)} o todos.")
    for n in nombres:
        GRAFICOS[n]()
