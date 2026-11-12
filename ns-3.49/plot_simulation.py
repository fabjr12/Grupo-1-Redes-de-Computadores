#!/usr/bin/env python3
"""
Gráficos do projeto PCS3614 (ns-3, Wi-Fi + enlace cabeado).

Uso:
    python3 gerar_graficos.py                       # usa equipe_1_resultados.csv
    python3 gerar_graficos.py caminho/resultados.csv

Saída: pasta ./graficos com um PNG (300 dpi) e um PDF por gráfico.

Dependências: pandas, numpy, matplotlib
    pip install pandas numpy matplotlib
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------------
CSV = sys.argv[1] if len(sys.argv) > 1 else "equipe_1_resultados.csv"
OUT = Path("graficos")

POT_REF = 26          # dBm usado nos gráficos 1, 2, 3 e 6

# Gráfico 4 (perda por tipo de tráfego): rajada e misto só existem em POT_REF,
# então a comparação entre tráfegos é feita nessa potência.
N_PERDA = None        # None = maior nº de clientes (onde a rede satura)
POT_PERDA = POT_REF
# Gráfico 5 (mobilidade): nível de potência (None = média entre todos os níveis, só tráfego CBR).
POT_MOB = None

PROTOCOLOS = ["udp", "tcp", "misto"]
TRAFEGOS = ["cbr", "rajada", "misto"]
MOBILIDADES = ["estatico", "movel"]
ROTULO = {"udp": "UDP", "tcp": "TCP", "misto": "UDP+TCP (50/50)",
          "cbr": "CBR", "rajada": "Rajada", "misto_t": "CBR/Rajada",
          "estatico": "Estático", "movel": "Móvel"}
COR = {"udp": "#1f77b4", "tcp": "#d62728", "misto": "#2ca02c"}
MARCA = {"estatico": "o", "movel": "s"}
ESTILO = {"estatico": "-", "movel": "--"}

plt.rcParams.update({
    "figure.dpi": 100, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 10,
})


# ----------------------------------------------------------------------------
# DADOS
# ----------------------------------------------------------------------------
def carregar(path):
    d = pd.read_csv(path)
    # O CSV repete linhas (grupo 'total' e grupo do protocolo, mais duplicatas).
    # Fica só o agregado de toda a rede.
    t = d[d["grupo"] == "total"].drop_duplicates().copy()
    if "potenciaTx" not in t.columns:
        sys.exit("O CSV precisa conter a coluna 'potenciaTx'.")
    t["pot_dbm"] = pd.to_numeric(t["potenciaTx"], errors="raise")
    return t.reset_index(drop=True)


def rot_pot(p):
    return f"{p} dBm"


def salvar(fig, nome):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / f"{nome}.png")
    fig.savefig(OUT / f"{nome}.pdf")
    print("salvo:", OUT / f"{nome}.png")
    plt.close(fig)


def legenda_proto_mob(ax_or_fig, loc="upper left"):
    h = [Line2D([], [], color=COR[p], lw=2, label=ROTULO[p]) for p in PROTOCOLOS]
    h += [Line2D([], [], color="gray", ls=ESTILO[m], marker=MARCA[m], label=ROTULO[m])
          for m in MOBILIDADES]
    ax_or_fig.legend(handles=h, loc=loc, fontsize=8, ncol=1)


# ----------------------------------------------------------------------------
# GRÁFICOS 1 a 3: desempenho e escalabilidade (vs número de clientes)
# ----------------------------------------------------------------------------
def linhas_vs_n(t, col, ylabel, titulo, nome, log_y=False):
    ref = t[t["pot_dbm"] == POT_REF]
    m = ref.groupby(["mobilidade", "protocolo", "nClientes"])[col].mean().reset_index()
    ns = sorted(t["nClientes"].unique())
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for mob in MOBILIDADES:
        for p in PROTOCOLOS:
            s = m[(m.mobilidade == mob) & (m.protocolo == p)].sort_values("nClientes")
            ax.plot(s["nClientes"], s[col], color=COR[p], ls=ESTILO[mob],
                    marker=MARCA[mob], ms=5, lw=1.8)
    ax.set_xscale("log", base=2)
    ax.set_xticks(ns)
    ax.set_xticklabels(ns)
    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel("Número de clientes")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{titulo}\n(potência: {rot_pot(POT_REF)}, média entre tipos de tráfego)")
    legenda_proto_mob(ax)
    salvar(fig, nome)


def g1(t):
    linhas_vs_n(t, "vazao_total_mbps", "Vazão total (Mbps)", "Gráfico 1: vazão total vs clientes", "g1_vazao_total")


def g2(t):
    linhas_vs_n(t, "vazao_media_cliente_kbps", "Vazão média por cliente (kbps)",
                "Gráfico 2: vazão por cliente vs clientes", "g2_vazao_por_cliente")


def g3(t):
    linhas_vs_n(t, "atraso_medio_ms", "Atraso médio (ms, escala log)",
                "Gráfico 3: atraso médio vs clientes", "g3_atraso_medio", log_y=True)


# ----------------------------------------------------------------------------
# GRÁFICO 4: perda de pacotes por tipo de tráfego
# ----------------------------------------------------------------------------
def g4(t):
    pr = POT_PERDA
    n = N_PERDA or t["nClientes"].max()
    ref = t[(t.pot_dbm == pr) & (t.nClientes == n)]
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    w = 0.26
    x = np.arange(len(TRAFEGOS))
    for ax, mob in zip(axs, MOBILIDADES):
        for i, p in enumerate(PROTOCOLOS):
            v = [ref[(ref.mobilidade == mob) & (ref.protocolo == p) & (ref.trafego == tr)]["perda_pct"].mean()
                 for tr in TRAFEGOS]
            b = ax.bar(x + (i - 1) * w, v, w, color=COR[p], label=ROTULO[p])
            ax.bar_label(b, fmt="%.1f", fontsize=7, padding=1)
        ax.set_xticks(x)
        ax.set_xticklabels([ROTULO.get(tr, tr) if tr != "misto" else "CBR/Rajada" for tr in TRAFEGOS])
        ax.set_xlabel("Tipo de tráfego")
        ax.set_title(ROTULO[mob])
        ax.set_ylim(bottom=0)
    axs[0].set_ylabel("Perda de pacotes (%)")
    axs[0].legend(title="Protocolo", fontsize=8)
    fig.suptitle(f"Gráfico 4: perda de pacotes por tipo de tráfego ({n} clientes, potência: {rot_pot(pr)})")
    salvar(fig, "g4_perda_por_trafego")


# ----------------------------------------------------------------------------
# GRÁFICO 5: penalidade de mobilidade
#   P_mob = (V_estatico - V_movel) / V_estatico * 100
# ----------------------------------------------------------------------------
def g5(t):
    if POT_MOB is None:
        ref = t[t.trafego == "cbr"]   # único tráfego com varredura completa de potência
        pot_txt = "média entre os níveis de potência, tráfego CBR; n=1 só em " + rot_pot(POT_REF)
    else:
        ref, pot_txt = t[t.pot_dbm == POT_MOB], f"potência: {rot_pot(POT_MOB)}"
    v = ref.groupby(["protocolo", "mobilidade", "nClientes"])["vazao_total_mbps"].mean().unstack("mobilidade")
    v["pmob"] = (v["estatico"] - v["movel"]) / v["estatico"] * 100
    pm = v["pmob"].unstack("nClientes")
    ns = list(pm.columns)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    w = 0.8 / len(ns)
    x = np.arange(len(PROTOCOLOS))
    cmap = plt.cm.viridis(np.linspace(0.15, 0.85, len(ns)))
    for i, n in enumerate(ns):
        vals = [pm.loc[p, n] for p in PROTOCOLOS]
        b = ax.bar(x + (i - (len(ns) - 1) / 2) * w, vals, w, color=cmap[i], label=f"{n} cliente(s)")
        ax.bar_label(b, fmt="%.1f", fontsize=7, padding=1)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([ROTULO[p] for p in PROTOCOLOS])
    ax.set_xlabel("Protocolo")
    ax.set_ylabel(r"$P_{mob}$ = (V$_{est}$ - V$_{mov}$) / V$_{est}$ × 100  (%)")
    ax.set_title(f"Gráfico 5: penalidade de mobilidade na vazão total\n({pot_txt}; negativo = móvel melhor)")
    ax.legend(fontsize=8)
    salvar(fig, "g5_penalidade_mobilidade")


# ----------------------------------------------------------------------------
# GRÁFICO 6: heatmap de atraso médio
# ----------------------------------------------------------------------------
def g6(t):
    pr = POT_REF
    ref = t[t.pot_dbm == pr].copy()
    trot = {"cbr": "CBR", "rajada": "Rajada", "misto": "CBR/Rajada"}
    ref["cenario"] = (ref["mobilidade"].map(ROTULO) + " | " + ref["protocolo"].map(ROTULO)
                      + " | " + ref["trafego"].map(trot))
    ordem = [f"{ROTULO[m]} | {ROTULO[p]} | {trot[tr]}"
             for m in MOBILIDADES for p in PROTOCOLOS for tr in TRAFEGOS]
    h = ref.pivot_table(index="cenario", columns="nClientes", values="atraso_medio_ms").reindex(ordem)
    fig, ax = plt.subplots(figsize=(7, 8))
    im = ax.imshow(h.values, aspect="auto", cmap="YlOrRd",
                   norm=LogNorm(vmin=max(np.nanmin(h.values[h.values > 0]), 0.05), vmax=h.values.max()))
    ax.set_xticks(range(h.shape[1]))
    ax.set_xticklabels(h.columns)
    ax.set_yticks(range(h.shape[0]))
    ax.set_yticklabels(h.index, fontsize=8)
    ax.grid(False)
    for i in range(h.shape[0]):
        for j in range(h.shape[1]):
            val = h.values[i, j]
            ax.text(j, i, f"{val:.2f}" if val < 10 else f"{val:.0f}", ha="center", va="center",
                    fontsize=8, color="white" if val > np.sqrt(h.values.max() * 0.05) * 3 else "black")
    fig.colorbar(im, ax=ax, label="Atraso médio (ms, escala log)")
    ax.set_xlabel("Número de clientes")
    ax.set_title(f"Gráfico 6: heatmap do atraso médio (ms)\npotência: {rot_pot(pr)}")
    salvar(fig, "g6_heatmap_atraso")


# ----------------------------------------------------------------------------
# GRÁFICO 7: vazão total vs atraso médio
# ----------------------------------------------------------------------------
def g7(t):
    # Linhas com vazão 0 (nenhum cliente associado) têm atraso 0 sem significado.
    s = t[t["vazao_total_mbps"] > 0]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for mob in MOBILIDADES:
        for p in PROTOCOLOS:
            q = s[(s.mobilidade == mob) & (s.protocolo == p)]
            ax.scatter(q["vazao_total_mbps"], q["atraso_medio_ms"], s=20 + 12 * np.log2(q["nClientes"] + 1) ** 2,
                       color=COR[p], marker=MARCA[mob], alpha=0.55,
                       edgecolor="k", linewidth=0.3)
    ax.set_yscale("log")
    ax.set_xlabel("Vazão total (Mbps)")
    ax.set_ylabel("Atraso médio (ms, escala log)")
    ax.set_title("Gráfico 7: vazão total vs atraso médio\n(todos os cenários e níveis de potência; tamanho do ponto cresce com nº de clientes)")
    legenda_proto_mob(ax, loc="center right")
    salvar(fig, "g7_vazao_vs_atraso")


# ----------------------------------------------------------------------------
# GRÁFICOS 8 e 9: 3D (clientes x potência x métrica)
# ----------------------------------------------------------------------------
def barras3d(t, col, zlabel, titulo, nome):
    t = t[t.trafego == "cbr"]   # único tráfego com varredura completa de potência
    ns = sorted(t["nClientes"].unique())
    pots = sorted(t["pot_dbm"].unique())
    fig = plt.figure(figsize=(16, 9))
    zmax = t.groupby(["mobilidade", "protocolo", "nClientes", "pot_dbm"])[col].mean().max()
    k = 1
    for mob in MOBILIDADES:
        for p in PROTOCOLOS:
            ax = fig.add_subplot(2, 3, k, projection="3d")
            k += 1
            q = t[(t.mobilidade == mob) & (t.protocolo == p)]
            z = q.groupby(["nClientes", "pot_dbm"])[col].mean().unstack("pot_dbm").reindex(index=ns, columns=pots)
            X, Y = np.meshgrid(range(len(ns)), range(len(pots)), indexing="ij")
            zz = z.values.ravel()
            ok = ~np.isnan(zz)   # n=1 só tem a potência de referência
            ax.bar3d(X.ravel()[ok] - 0.35, Y.ravel()[ok] - 0.35, 0, 0.7, 0.7, zz[ok],
                     color=plt.cm.viridis(zz[ok] / zmax), shade=True, edgecolor="k", linewidth=0.2)
            ax.set_xticks(range(len(ns)))
            ax.set_xticklabels(ns)
            ax.set_yticks(range(len(pots)))
            ax.set_yticklabels([rot_pot(x) for x in pots], fontsize=7)
            ax.set_xlabel("Clientes")
            ax.set_ylabel("Potência", labelpad=8)
            ax.set_zlabel(zlabel, labelpad=4)
            ax.set_zlim(0, zmax * 1.05)
            ax.set_title(f"{ROTULO[p]} | {ROTULO[mob]}", fontsize=10)
            ax.view_init(elev=25, azim=-60)
    fig.suptitle(titulo + " (tráfego CBR)", fontsize=12)
    fig.tight_layout()
    salvar(fig, nome)


def g8(t):
    barras3d(t, "vazao_total_mbps", "Vazão (Mbps)",
             "Gráfico 8: clientes x potência x vazão total", "g8_3d_vazao")


def g9(t):
    barras3d(t, "perda_pct", "Perda (%)",
             "Gráfico 9: clientes x potência x perda de pacotes", "g9_3d_perda")


# ----------------------------------------------------------------------------
if __name__ == "__main__":
    dados = carregar(CSV)
    dados.to_excel('resultado.xlsx', index=False)
    print(f"{len(dados)} linhas únicas | clientes: {sorted(dados.nClientes.unique())} | "
          f"potências: {sorted(dados.pot_dbm.unique())}")
    for f in (g1, g2, g3, g4, g5, g6, g7, g8, g9):
        f(dados)