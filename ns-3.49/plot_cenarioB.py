#!/usr/bin/env python3
"""Gera os gráficos 3D de atraso médio do cenário B."""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

CSV = "equipe_1_cenarioB.csv"
OUT = Path("graficos")

rotulo_mob = {"estatico": "Estático", "movel": "Móvel"}
rotulo_proto = {"udp": "UDP", "tcp": "TCP", "misto": "UDP+TCP (50/50)"}
mobilidades = ["estatico", "movel"]
protocolos = ["udp", "tcp", "misto"]

dados = pd.read_csv(CSV)
dados = dados[(dados["grupo"] == "total") & (dados["trafego"] == "cbr")].copy()
clientes = sorted(dados["nClientes"].unique())
potencias = sorted(dados["potenciaTx"].unique())
zmax = dados["atraso_medio_ms"].max()
zmin = dados.loc[dados["atraso_medio_ms"] > 0, "atraso_medio_ms"].min()

fig = plt.figure(figsize=(16, 9))
for indice, mobilidade in enumerate(mobilidades):
    for protocolo in protocolos:
        ax = fig.add_subplot(2, 3, indice * 3 + protocolos.index(protocolo) + 1,
                             projection="3d")
        filtro = dados[
            (dados["mobilidade"] == mobilidade)
            & (dados["protocolo"] == protocolo)
        ]
        tabela = filtro.pivot_table(
            index="nClientes",
            columns="potenciaTx",
            values="atraso_medio_ms",
            aggfunc="mean",
        ).reindex(index=clientes, columns=potencias)

        tabela = tabela.replace(0, np.nan)

        x, y = np.meshgrid(
            np.arange(len(clientes)),
            np.arange(len(potencias)),
            indexing="ij",
        )
        alturas = tabela.to_numpy(dtype=float).ravel()
        validos = np.isfinite(alturas) & (alturas > 0)
        escala = alturas[validos] / zmax if zmax > 0 else alturas[validos]
        base = zmin / 2

        ax.bar3d(
            x.ravel()[validos] - 0.35,
            y.ravel()[validos] - 0.35,
            base,
            0.7,
            0.7,
            alturas[validos] - base,
            color=plt.cm.viridis(escala),
            shade=True,
            edgecolor="k",
            linewidth=0.2,
        )
        ax.set_xticks(np.arange(len(clientes)))
        ax.set_xticklabels(clientes)
        ax.set_yticks(np.arange(len(potencias)))
        ax.set_yticklabels([f"{p} dBm" for p in potencias], fontsize=7)
        ax.set_xlabel("Clientes")
        ax.set_ylabel("Potência", labelpad=8)
        ax.set_zlabel("Atraso médio (ms, escala log)", labelpad=4)
        ax.set_zscale("log")
        ax.set_zlim(zmin / 2, zmax * 1.05 if zmax > 0 else 1)
        ax.set_title(f"{rotulo_proto[protocolo]} | {rotulo_mob[mobilidade]}")
        ax.view_init(elev=25, azim=-60)

fig.suptitle("Cenário B: clientes x potência x atraso médio (CBR)")
fig.tight_layout()
OUT.mkdir(exist_ok=True)
fig.savefig(OUT / "cenarioB_3d_atraso_medio.png", dpi=300)
fig.savefig(OUT / "cenarioB_3d_atraso_medio.pdf")
plt.close(fig)
print("Gráficos salvos em graficos/cenarioB_3d_atraso_medio.*")
