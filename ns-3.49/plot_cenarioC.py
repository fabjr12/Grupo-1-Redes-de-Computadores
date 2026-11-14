import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Uso: python gera_perda_cenarioC.py [caminho_do_csv]
caminho = sys.argv[1] if len(sys.argv) > 1 else "cenarioC.csv"
df = pd.read_csv(caminho)
ns = sorted(df.nClientes.unique())
nrod = df.run.nunique()

# (rótulo, protocolo, grupo, cor, hachura)
series = [
    ("UDP (puro)",        "udp",   "total", "tab:blue",  ""),
    ("TCP (puro)",        "tcp",   "total", "tab:red",   ""),
    ("Misto: fluxos UDP", "misto", "udp",   "#6baed6",   "//"),
    ("Misto: fluxos TCP", "misto", "tcp",   "#fc9272",   "//"),
]

w = 0.19
x = np.arange(len(ns))
fig, ax = plt.subplots(figsize=(8, 4.2))
for i, (rot, proto, gr, cor, hatch) in enumerate(series):
    g = df[(df.protocolo == proto) & (df.grupo == gr)]
    m = g.groupby("nClientes").perda_pct.agg(["mean", "std"]).reindex(ns)
    media = m["mean"].values
    desvio = m["std"].fillna(0).values
    inf = np.minimum(desvio, media)             # barra inferior não passa de 0
    pos = x + (i - 1.5) * w
    ax.bar(pos, media, w, yerr=[inf, desvio], capsize=2, color=cor, hatch=hatch,
           edgecolor="k", linewidth=0.5, label=rot, error_kw={"lw": 0.9})
    for px, v, d in zip(pos, media, desvio):
        ax.text(px, v + d + 1.0, f"{v:.1f}", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(ns)
ax.set_xlabel("Número de clientes")
ax.set_ylabel("Perda de pacotes (%)")
ax.set_ylim(0, max(ax.get_ylim()[1], 90))
ax.grid(axis="y", alpha=0.3)
ax.set_axisbelow(True)
ax.legend(fontsize=8, loc="upper left")
ax.set_title(f"Perda de pacotes por protocolo (26 dBm, estático, CBR; média ± desvio, {nrod} rodadas)",
             fontsize=10)
plt.tight_layout()
plt.savefig("perda_cenarioC.pdf")
plt.savefig("perda_cenarioC.png", dpi=200)
print("ok:", len(df), "linhas,", nrod, "rodadas, n =", ns)