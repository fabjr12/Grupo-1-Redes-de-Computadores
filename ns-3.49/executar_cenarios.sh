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
        for trafego in cbr rajada misto; do
            for n in 1 2 4 6; do
                for pot in 16 20 23 26; do
                    for run in $(seq 1 "$RODADAS"); do
                        ./ns3 run --no-build \
                        "equipe_1_3q2026 \
                        --tempo=60 \
                        --nClientes=$n \
                        --tamanho=140 \
                        --potenciaTx=26 \
                        --velMin=3.6 \
                        --velMax=7.2 \
                        --taxa=512kbps \
                        --tamUdp=512 \
                        --tamTcp=1500 \
                        --mobilidade=$mob \
                        --protocolo=$proto \
                        --trafego=$trafego \
                        --run=$run \
                        --csv=$CSV"
                    done
                done
            done
        done
    done
done

echo "Resultados em $CSV"
