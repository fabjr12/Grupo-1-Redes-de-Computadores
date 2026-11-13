#!/usr/bin/env bash
# Cenarios especificos (Equipe 1).
#
# Uso (dentro da pasta ns-3.49):
#   bash executar_especificos.sh A [rodadas] [nClientes] [potenciaTx]
#       Fixa clientes e potencia; varia mobilidade x protocolo x trafego.
#       Padrao: 5 rodadas, 32 clientes, 26 dBm.  -> equipe_1_cenarioA.csv
#
#   bash executar_especificos.sh B [rodadas] [trafego]
#       Fixa o trafego; varia clientes x potencia para cada protocolo e mobilidade.
#       Padrao: 1 rodada, trafego cbr.            -> equipe_1_cenarioB.csv
set -e

EXPERIMENTO=${1:?"informe o experimento: A ou B"}
CLIENTES=(1 2 4 8 16 32)
POTENCIAS=(16 18 20 22 26)

rodar() {  # args: csv mob proto trafego n pot run
  echo "  mob=$2 proto=$3 trafego=$4 n=$5 pot=$6 run=$7"
  ./ns3 run --no-build "equipe_1_3q2026 --tempo=60 --nClientes=$5 --tamanho=140 \
    --potenciaTx=$6 --velMin=3.6 --velMax=7.2 --taxa=512kbps --tamUdp=512 --tamTcp=1500 \
    --mobilidade=$2 --protocolo=$3 --trafego=$4 --run=$7 --csv=$1" > /dev/null
}

case "$EXPERIMENTO" in
  A)
    RODADAS=${2:-5}; N=${3:-32}; POT=${4:-26}
    CSV="$(pwd)/equipe_1_cenarioA.csv"
    echo "Experimento A: n=$N, potencia=$POT dBm, $RODADAS rodada(s)"
    ;;
  B)
    RODADAS=${2:-1}; TRAFEGO=${3:-cbr}
    CSV="$(pwd)/equipe_1_cenarioB.csv"
    echo "Experimento B: trafego=$TRAFEGO, $RODADAS rodada(s)"
    ;;
  *)
    echo "experimento invalido: use A ou B"; exit 1 ;;
esac

rm -f "$CSV"
./ns3 build equipe_1_3q2026

for run in $(seq 1 "$RODADAS"); do
  for mob in 0 1; do
    for proto in udp tcp misto; do
      if [ "$EXPERIMENTO" = A ]; then
        for trafego in cbr rajada misto; do
          rodar "$CSV" "$mob" "$proto" "$trafego" "$N" "$POT" "$run"
        done
      else
        for n in "${CLIENTES[@]}"; do
          for pot in "${POTENCIAS[@]}"; do
            rodar "$CSV" "$mob" "$proto" "$TRAFEGO" "$n" "$pot" "$run"
          done
        done
      fi
    done
  done
done

echo "Resultados em $CSV"
