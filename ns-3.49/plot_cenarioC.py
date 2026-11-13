import pandas as pd, numpy as np
import matplotlib.pyplot as plt

A = pd.read_csv("equipe_1_cenarioA.csv")
B = pd.read_csv("equipe_1_cenarioB.csv")

# (a) n=32, 26 dBm, 5 rodadas: perda por protocolo, mobilidade e padrão de tráfego
protos = [("udp", "UDP"), ("tcp", "TCP"), ("misto", "UDP+TCP (50/50)")]
combos = [("estatico", "cbr", "Estático | CBR"), ("estatico", "rajada", "Estático | Rajada"),
          ("movel", "cbr", "Móvel | CBR"), ("movel", "rajada", "Móvel | Rajada")]
cores = ["#4c78a8", "#9ecae9", "#e45756", "#ff9d98"]
tot = A[A.grupo == "total"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.9))
w = 0.2
x = np.arange(len(protos))
for i, (mob, pad, lab) in enumerate(combos):
    v, e = [], []
    for p, _ in protos:
        # no misto, "CBR" do CBR/Rajada não existe: usa-se trafego 'cbr' (todos CBR)
        g = tot[(tot.protocolo == p) & (tot.mobilidade == mob) & (tot.trafego == pad)]
        # agrega por rodada (uma linha por run)
        v.append(g.perda_pct.mean()); e.append(g.perda_pct.std())
    ax1.bar(x + (i - 1.5) * w, v, w, yerr=e, capsize=2, color=cores[i], label=lab,
            edgecolor="k", linewidth=0.4)
ax1.set_xticks(x); ax1.set_xticklabels([n for _, n in protos])
ax1.set_ylabel("Perda de pacotes (%)")
ax1.set_title("(a) 32 clientes, 26 dBm (média ± desvio, 5 rodadas)", fontsize=9)
ax1.legend(fontsize=7); ax1.grid(axis="y", alpha=0.3)

# (b) misto CBR, n=32: perda do UDP vs TCP na mesma simulação, em função da potência
m = B[(B.protocolo == "misto") & (B.nClientes == 32)]
pots = [16, 18, 20, 22, 26]
for mob, ls, nome in [("estatico", "-", "Estático"), ("movel", "--", "Móvel")]:
    for gr, c, mk, rot in [("udp", "tab:blue", "o", "UDP"), ("tcp", "tab:red", "s", "TCP")]:
        g = m[(m.mobilidade == mob) & (m.grupo == gr)].groupby("potenciaTx").perda_pct.agg(["mean", "std"]).reindex(pots)
        ax2.errorbar(pots, g["mean"], yerr=g["std"], ls=ls, marker=mk, color=c, capsize=2,
                     label=f"{rot} | {nome}")
ax2.set_xticks(pots)
ax2.set_xlabel("Potência de transmissão (dBm)")
ax2.set_ylabel("Perda de pacotes (%)")
ax2.set_title("(b) Misto 50/50, 32 clientes, CBR: UDP vs TCP", fontsize=9)
ax2.legend(fontsize=7); ax2.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("perda_protocolo.pdf"); plt.savefig("perda_protocolo.png", dpi=200)