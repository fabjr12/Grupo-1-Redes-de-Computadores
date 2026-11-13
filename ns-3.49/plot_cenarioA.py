#!/usr/bin/env python3
"""Gera o heatmap da vazão média por cliente do cenário A."""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

CSV = "equipe_1_cenarioA.csv"
OUT = Path("graficos")

rotulo_mob = {"estatico": "Estático", "movel": "Móvel"}
rotulo_proto = {"udp": "UDP", "tcp": "TCP", "misto": "UDP+TCP (50/50)"}
rotulo_trafego = {"cbr": "CBR", "rajada": "Rajada", "misto": "CBR/Rajada"}
ordem_mob = ["estatico", "movel"]
ordem_proto = ["udp", "tcp", "misto"]
ordem_trafego = ["cbr", "rajada", "misto"]

dados = pd.read_csv(CSV)
dados = dados[dados["grupo"] == "total"].copy()
dados["cenario"] = (
    dados["mobilidade"].map(rotulo_mob)
    + " | "
    + dados["protocolo"].map(rotulo_proto)
    + " | "
    + dados["trafego"].map(rotulo_trafego)
)

ordem = [
    f"{rotulo_mob[m]} | {rotulo_proto[p]} | {rotulo_trafego[t]}"
    for m in ordem_mob
    for p in ordem_proto
    for t in ordem_trafego
]

tabela = dados.pivot_table(
    index="cenario",
    columns="nClientes",
    values="vazao_media_cliente_kbps",
    aggfunc="mean",
).reindex(ordem).T

fig, ax = plt.subplots(figsize=(12, 4.5))
valores = tabela.to_numpy(dtype=float)
imagem = ax.imshow(valores, aspect="auto", cmap="YlGnBu")

ax.set_xticks(np.arange(len(tabela.columns)))
ax.set_xticklabels(tabela.columns, rotation=45, ha="right", rotation_mode="anchor")
ax.set_yticks(np.arange(len(tabela.index)))
ax.set_yticklabels(tabela.index, fontsize=8)
ax.set_xlabel("Cenário")
ax.set_ylabel("Número de clientes")
ax.set_title("Cenário A: heatmap da vazão média por cliente (kbps)")

for i in range(valores.shape[0]):
    for j in range(valores.shape[1]):
        ax.text(j, i, f"{valores[i, j]:.1f}", ha="center", va="center")

fig.colorbar(imagem, ax=ax, label="Vazão média por cliente (kbps)")
fig.tight_layout()
OUT.mkdir(exist_ok=True)
fig.savefig(OUT / "cenarioA_heatmap_vazao_media.png", dpi=300)
fig.savefig(OUT / "cenarioA_heatmap_vazao_media.pdf")
plt.close(fig)
print("Gráficos salvos em graficos/cenarioA_heatmap_vazao_media.*")
