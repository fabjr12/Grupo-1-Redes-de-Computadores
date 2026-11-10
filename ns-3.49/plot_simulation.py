import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("equipe_1_resultados.csv")

# Usar apenas os resultados totais
df = df[df["grupo"] == "total"]

df.to_excel('resultado.xlsx', index=False)

# Exemplo: vazão por número de clientes
for mobilidade in ["estatico", "movel"]:
    dados = df[
        (df["mobilidade"] == mobilidade) &
        (df["protocolo"] == "udp") &
        (df["trafego"] == "cbr")
    ]

    plt.plot(
        dados["nClientes"],
        dados["atraso_medio_ms"],
        marker="o",
        label=mobilidade
    )

plt.xlabel("Número de clientes")
plt.ylabel("Atraso médio (ms)")
plt.legend()
plt.grid(True)
plt.show()