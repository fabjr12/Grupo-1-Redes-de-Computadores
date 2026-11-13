#!/usr/bin/env bash
# Cenario C (Equipe 1): muitos clientes para evidenciar a saturacao do meio sem fio.
# Fixos: estatico, trafego CBR, 26 dBm. Varia: clientes x protocolo x rodadas (listas abaixo).
# Os casos com 32 clientes ja estao em equipe_1_cenarioA.csv (estatico, cbr, 26 dBm, runs 1-5).
#
# Uso (dentro da pasta ns-3.49):  bash executar_cenarioC.sh [rodadas]   (padrao: 3)
set -e

RODADAS=${1:-3}
CLIENTES=(32 48 64 128)
PROTOCOLOS=(udp tcp misto)
CSV="$(pwd)/cenarioC.csv"
rm -f "$CSV"

./ns3 build equipe_1_3q2026

for run in $(seq 1 "$RODADAS"); do
  for n in "${CLIENTES[@]}"; do
    for proto in "${PROTOCOLOS[@]}"; do
      echo "run=$run n=$n proto=$proto ($(date +%H:%M:%S))"
      ./ns3 run --no-build "equipe_1_3q2026 --mobilidade=0 --protocolo=$proto \
        --trafego=cbr --nClientes=$n --potenciaTx=26 --seed=1 --run=$run \
        --csv=$CSV" > /dev/null
    done
  done
done

echo "Resultados em $CSV"
