"""Render the Task 4 dashboard (A4 landscape) as PNG, SVG and PDF.

Requires: pandas, numpy, matplotlib, pyshp, and geopandas==0.14.4 (used only for its bundled Natural Earth world map). Run: python dash_plot.py
"""
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapefile
from matplotlib.collections import PatchCollection
from matplotlib.colors import BoundaryNorm
from matplotlib.patches import FancyBboxPatch, Polygon

from dash_data import D, annual, annual_renew, emis, multiples, pc

ORANGE, GREEN, GREY, INK = "#E69F00", "#009E73", "#8C8C8C", "#222222"
plt.rcParams.update({"svg.fonttype": "none", "pdf.fonttype": 42,
                     "font.family": "DejaVu Sans", "font.size": 7,
                     "axes.edgecolor": "#555555", "axes.linewidth": 0.6,
                     "xtick.color": "#444444", "ytick.color": "#444444"})

# --- Net imported emissions, recomputed and checked against the report ---
cons = pd.read_csv(D + "Consumption.csv", dtype=str)
cons["iso"] = cons["Country Code"].str.strip().str.upper()
cons["year"] = cons.Year.str.extract(r"((?:19|20)\d{2})")[0].astype(int)
cons["v"] = cons["Consumption CO2"].str.replace(",", "").astype(float)
cons.loc[(cons.iso == "PAN") & cons.year.isin([2007, 2011]), "v"] = np.nan
panel = emis[["iso_code", "region", "year", "annual_co2_mt"]].merge(
    cons[["iso", "year", "v"]], left_on=["iso_code", "year"],
    right_on=["iso", "year"], how="left").sort_values(["iso_code", "year"])
panel["v"] = panel.groupby("iso_code").v.transform(
    lambda s: s.interpolate(limit_direction="both"))
panel["v"] = panel.v.fillna(panel.annual_co2_mt)
by_iso = panel.groupby(["iso_code", "region"])[["annual_co2_mt", "v"]].sum()
net_iso = (by_iso.v - by_iso.annual_co2_mt).droplevel("region")
net_reg = by_iso.groupby("region").sum()
net_reg = net_reg.v - net_reg.annual_co2_mt
assert abs(net_iso["USA"] - 7062.2) < 0.2 and abs(net_iso["CHN"] + 24691.0) < 0.2

# --- Figure scaffold ------------------------------------------------------
fig = plt.figure(figsize=(11.69, 8.27), dpi=200)
fig.patch.set_facecolor("white")
MM = 1 / 297, 1 / 210  # mm -> figure fraction


def frac(x, y, w, h):
    """Convert a top-left mm box to a matplotlib [left, bottom, w, h]."""
    return [x * MM[0], 1 - (y + h) * MM[1], w * MM[0], h * MM[1]]


def card(x, y, w, h, fill="white"):
    l, b, ww, hh = frac(x, y, w, h)
    fig.patches.append(FancyBboxPatch(
        (l, b), ww, hh, boxstyle="round,pad=0,rounding_size=0.006",
        transform=fig.transFigure, facecolor=fill, edgecolor="#BBBBBB",
        linewidth=0.8, zorder=-10))


def text(x, y, s, **kw):
    fig.text(x * MM[0], 1 - y * MM[1], s, **kw)


def panel_title(x, y, s, sub=None):
    text(x + 3, y + 5, s, fontsize=9, fontweight="bold", color=INK,
         va="baseline")
    if sub:
        text(x + 3, y + 9, sub, fontsize=6.5, color="#555555", va="baseline")


def style(ax, grid="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=2, labelsize=6.5)
    if grid:
        ax.grid(axis=grid, color="#E5E5E5", linewidth=0.5)
        ax.set_axisbelow(True)


fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}")

# --- Header ---------------------------------------------------------------
card(10, 10, 277, 20, "#F7F7F7")
text(14, 19, "The energy transition: growing fast, not yet fast enough",
     fontsize=17, fontweight="bold", color=INK, va="baseline")
text(14, 26, "Renewable electricity is growing faster than ever, yet annual "
     "CO2 emissions across 150 countries reached a record 34,067.6 Mt in "
     "2023: the transition is under way but has not yet bent the curve.",
     fontsize=7.4, color="#444444", va="baseline")

# --- KPI tiles ------------------------------------------------------------
kpis = [
    ("34,067.6 Mt", "CO2 emitted in 2023: a record high", ORANGE),
    ("−4.04%", "2020 COVID-19 fall, reversed by +1,538.9 Mt in 2021",
     ORANGE),
    ("357 → 2,894 TWh", "China's renewable generation, 2004 to 2023",
     GREEN),
]
for (val, lab, col), x in zip(kpis, (10, 104, 198)):
    card(x, 33, 89, 22)
    fig.patches.append(FancyBboxPatch(
        (frac(x, 33, 1.6, 22)[0], frac(x, 33, 1.6, 22)[1]),
        1.6 * MM[0], 22 * MM[1], boxstyle="square,pad=0",
        transform=fig.transFigure, facecolor=col, edgecolor="none",
        zorder=-9))
    text(x + 6, 45, val, fontsize=18, fontweight="bold", color=col,
         va="baseline")
    text(x + 6, 51.5, lab, fontsize=7, color="#444444", va="baseline")

# --- Panel 1: annual CO2 and renewables -----------------------------------
card(10, 60, 170, 70)
panel_title(10, 60, "Emissions hit a record while renewables accelerate",
            "Annual totals, 150 countries, 2004–2023 "
            "(separate axes: the units differ)")
ax1 = fig.add_axes(frac(25, 72, 150, 24))
ax1.plot(annual.index, annual.values, color=ORANGE, lw=2)
ax1.fill_between(annual.index, annual.values, annual.min() * 0.97,
                 color=ORANGE, alpha=0.08)
for yr, lab in [(2009, "Financial\ncrisis"), (2020, "COVID-19")]:
    ax1.annotate(lab, (yr, annual[yr]), xytext=(yr + 0.2, annual[yr] - 4300),
                 fontsize=6.5, ha="center", color="#444444",
                 arrowprops=dict(arrowstyle="-", color=GREY, lw=0.6))
ax1.annotate("34,067.6", (2023, annual[2023]), xytext=(2021.6, 35100),
             fontsize=6.5, fontweight="bold", color=ORANGE)
ax1.set_ylabel("Annual CO2 (Mt)", fontsize=6.5)
ax1.set_ylim(annual.min() * 0.88, annual.max() * 1.06)
ax1.yaxis.set_major_formatter(fmt)
ax1.set_xticklabels([])
style(ax1)

ax2 = fig.add_axes(frac(25, 101, 150, 24))
ax2.plot(annual_renew.index, annual_renew.values, color=GREEN, lw=2)
ax2.fill_between(annual_renew.index, annual_renew.values, 0,
                 color=GREEN, alpha=0.08)
ax2.set_ylabel("Renewables (TWh)", fontsize=6.5)
ax2.set_ylim(0, annual_renew.max() * 1.15)
ax2.yaxis.set_major_formatter(fmt)
style(ax2)
for a in (ax1, ax2):
    a.set_xlim(2003.5, 2023.5)
    a.set_xticks(range(2004, 2024, 2))

# --- Panel 2: map of cumulative CO2 per person -----------------------------
card(185, 60, 102, 70)
panel_title(185, 60, "Where emissions per person are highest",
            "Cumulative CO2 per person since 2004 (tonnes)")
for i, (lab, active) in enumerate([("Total", False), ("Per person", True)]):
    x0 = 189 + i * 17
    l, b, w, h = frac(x0, 118.5, 16, 5)
    fig.patches.append(FancyBboxPatch(
        (l, b), w, h, boxstyle="round,pad=0,rounding_size=0.004",
        transform=fig.transFigure, edgecolor="#999999", linewidth=0.6,
        facecolor="#333333" if active else "white", zorder=5))
    text(x0 + 8, 122.2, lab, fontsize=6, ha="center", va="baseline",
         color="white" if active else "#444444")

# World outlines: the Natural Earth low-resolution map bundled with
# geopandas 0.14 (pip install "geopandas==0.14.4").
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import geopandas.datasets
shp = shapefile.Reader(geopandas.datasets.get_path("naturalearth_lowres"))
fields = [f[0] for f in shp.fields[1:]]
bins = [0, 25, 50, 100, 200, 400, 700]
cmap = matplotlib.colormaps["Oranges"].resampled(len(bins) - 1)
norm = BoundaryNorm(bins, cmap.N)
axm = fig.add_axes(frac(187, 71, 98, 45))
patches, colours = [], []
name_fix = {"France": "FRA", "Norway": "NOR"}
for rec, s in zip(shp.records(), shp.shapes()):
    r = dict(zip(fields, rec))
    if r["continent"] == "Antarctica":
        continue
    iso = name_fix.get(r["name"], r["iso_a3"])
    val = pc.co2_pc.get(iso, np.nan)
    pts, parts = s.points, list(s.parts) + [len(s.points)]
    for a, b in zip(parts[:-1], parts[1:]):
        patches.append(Polygon(pts[a:b], closed=True))
        colours.append(cmap(norm(val)) if np.isfinite(val) else "#EDEDED")
axm.add_collection(PatchCollection(patches, facecolor=colours,
                                   edgecolor="white", linewidth=0.15))
axm.set_xlim(-170, 190)
axm.set_ylim(-58, 84)
axm.set_aspect("equal")
axm.axis("off")
for lab, (lon, lat), (tx, ty) in [
        ("Qatar 588.8 t", (51.2, 25.3), (78, 2)),
        ("Bahrain 403.5 t", (50.6, 26.0), (68, 38)),
        ("Trinidad & Tobago 556.3 t", (-61.2, 10.4), (-62, -40))]:
    axm.annotate(lab, (lon, lat), xytext=(tx, ty), fontsize=5.8,
                 color=INK, fontweight="bold",
                 arrowprops=dict(arrowstyle="-", color=INK, lw=0.5))
axl = fig.add_axes(frac(226, 118.5, 56, 2.6))
cb = matplotlib.colorbar.ColorbarBase(axl, cmap=cmap, norm=norm,
                                      orientation="horizontal")
cb.ax.tick_params(labelsize=5.5, length=1.5)
cb.outline.set_linewidth(0.4)
text(226, 127.3, "grey = not in sample", fontsize=5.5, color=GREY,
     va="center")

# --- Panel 3: total vs per-person rankings --------------------------------
card(10, 135, 85, 55)
panel_title(10, 135, "The ranking depends on the measure",
            "Top 5 countries, 2023")
tot = pc.sort_values("cum", ascending=False).head(5)
per = pc.sort_values("co2_pc", ascending=False).head(5)
short = {"United States": "US", "United Arab Emirates": "UAE",
         "Trinidad and Tobago": "Trinidad & T."}
for (data, col, xpos, title, unit), in zip([
        (tot, "cum", 25, "Total (Mt)", "{:,.0f}"),
        (per, "co2_pc", 66, "Per person (t)", "{:,.0f}")]):
    ax = fig.add_axes(frac(xpos, 150, 24, 30))
    names = [short.get(n, n) for n in data.Country]
    vals = data[col].values
    ax.barh(range(5)[::-1], vals, color=ORANGE, height=0.6)
    ax.set_yticks(range(5)[::-1], names, fontsize=6.3)
    ax.set_xticks([])
    for i, v in enumerate(vals):
        ax.text(v, 4 - i, " " + unit.format(v), va="center", fontsize=5.6,
                color="#444444")
    ax.set_xlim(0, vals.max() * 1.55)
    ax.set_title(title, fontsize=6.8, fontweight="bold", loc="left",
                 color=INK)
    style(ax, grid=None)
    ax.spines["bottom"].set_visible(False)
text(13, 186.5, "Only the US and Saudi Arabia appear in both top-10 lists",
     fontsize=6, color="#555555", style="italic", va="baseline")

# --- Panel 4: net imported emissions --------------------------------------
card(100, 135, 92, 55)
panel_title(100, 135, "Trade moves emissions between countries",
            "Cumulative consumption minus production, 2004–2023 (Mt)")
rows = [("United States", net_iso["USA"]), ("China", net_iso["CHN"]),
        ("", np.nan)]
rows += [(r, net_reg[r]) for r in net_reg.sort_values(ascending=False).index]
ax = fig.add_axes(frac(124, 145, 62, 33))
labels = [r[0] for r in rows]
vals = np.array([r[1] for r in rows])
ypos = np.arange(len(rows))[::-1]
ax.barh(ypos, np.nan_to_num(vals),
        color=["#0072B2" if v > 0 else "#D55E00" for v in np.nan_to_num(vals)],
        height=0.62)
ax.axvline(0, color="#555555", lw=0.7)
ax.set_yticks(ypos, labels, fontsize=6.3)
ax.tick_params(axis="y", length=0)
for y, v in zip(ypos, vals):
    if np.isfinite(v):
        ax.text(v + (600 if v >= 0 else -600), y, f"{v:+,.0f}",
                va="center", ha="left" if v >= 0 else "right",
                fontsize=5.6, color="#444444")
ax.set_xlim(-34000, 16000)
ax.xaxis.set_major_formatter(fmt)
ax.tick_params(axis="x", labelsize=5.5)
style(ax, grid="x")
ax.text(-33500, ypos[2] + 0.05, "Countries above, regions below",
        fontsize=5.5, color=GREY, va="center")
text(130, 187.5, "← net exporter", fontsize=6, color="#D55E00",
     va="baseline")
text(170, 187.5, "net importer →", fontsize=6, color="#0072B2",
     va="baseline")

# --- Panel 5: diverging pathways ------------------------------------------
card(197, 135, 90, 55)
panel_title(197, 135, "Some countries are bending the curve",
            "Index, 2004 = 100 (log scale):")
text(250, 144, "— CO2", fontsize=6.5, color=ORANGE, va="baseline",
     fontweight="bold")
text(262, 144, "— renewables", fontsize=6.5, color=GREEN,
     va="baseline", fontweight="bold")
text(247.5, 144.0, "— CO2", fontsize=1, color="white")
cells = [("DEU", "Germany", "Falling", 199, 147), ("USA", "United States",
         "Falling", 243, 147), ("CHN", "China", "Still rising", 199, 168),
         ("IND", "India", "Still rising", 243, 168)]
for iso, name, verdict, x, y in cells:
    co2, ren = multiples[iso]
    ax = fig.add_axes(frac(x + 7, y + 4, 34, 13))
    ax.plot(co2.index, co2.values, color=ORANGE, lw=1.4)
    ax.plot(ren.index, ren.values, color=GREEN, lw=1.4)
    ax.axhline(100, color="#CCCCCC", lw=0.5, ls="--")
    ax.set_yscale("log")
    ax.set_ylim(40, 1400)
    ax.set_yticks([50, 100, 300, 1000], ["50", "100", "300", "1000"])
    ax.set_xticks([2004, 2023], ["2004", "2023"])
    ax.tick_params(labelsize=5.2, length=1.5)
    ax.minorticks_off()
    style(ax, grid=None)
    text(x + 7, y + 3.2, f"{name}  ", fontsize=6.5, fontweight="bold",
         color=INK, va="baseline")
    text(x + 41, y + 3.2, verdict, fontsize=6, ha="right", va="baseline",
         color="#555555", style="italic")

# --- Footer ---------------------------------------------------------------
card(10, 193, 277, 8, "#F7F7F7")
text(14, 198.2, "Data: Our World in Data (Global Carbon Project, Ember, "
     "Energy Institute, World Bank) · 150 countries, 2004–2023  "
     "·  How to read this: consumption-based emissions count the "
     "emissions from everything a country buys, wherever it was made.",
     fontsize=6.2, color="#444444", va="center")

for a in fig.axes:
    a.set_zorder(1)
    a.patch.set_alpha(0)
for t in fig.texts:
    t.set_zorder(6)
fig.savefig("dashboard.png", dpi=200,
            facecolor="white")
fig.savefig("dashboard.svg", facecolor="white")
fig.savefig("dashboard.pdf", facecolor="white")
print("saved; regions:", net_reg.round(1).to_dict())
