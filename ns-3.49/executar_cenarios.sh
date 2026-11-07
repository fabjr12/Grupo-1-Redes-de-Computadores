#!/usr/bin/env bash
# Executa todos os cenarios do projeto (Equipe 1) e grava os resultados em um unico CSV.
# Uso (dentro da pasta ns-3.49): bash executar_cenarios.sh [numero_de_rodadas]
set -e

RODADAS=${1:-1}
CSV="$(pwd)/equipe_1_resultados.csv"
rm -f "$CSV"

./ns3 build equipe_1_3q2026

for mob in 0 1; do
    for proto in udp tcp misto; do
        for n in 1 2 4 8 16 32; do
            for run in $(seq 1 "$RODADAS"); do
                ./ns3 run --no-build "equipe_1_3q2026 --nClientes=$n --mobilidade=$mob --protocolo=$proto --run=$run --csv=$CSV"
            done
        done
    done
done

echo "Resultados em $CSV"
