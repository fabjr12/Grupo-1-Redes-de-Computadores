#!/usr/bin/env bash
set -e

RODADAS=${1:-1}
CSV="$(pwd)/equipe_1_resultados.csv"

rm -f "$CSV"
./ns3 build equipe_1_3q2026

# O programa acrescenta cada resultado diretamente ao CSV.
rodar() {
  ./ns3 run --no-build "equipe_1_3q2026 --tempo=60 --nClientes=$4 --tamanho=140 \
    --potenciaTx=$5 --velMin=3.6 --velMax=7.2 --taxa=512kbps --tamUdp=512 --tamTcp=1500 \
    --mobilidade=$1 --protocolo=$2 --trafego=$3 --run=$6 \
    --csv=$CSV" > /dev/null
}

for mob in 0 1; do
  for proto in udp tcp misto; do
    for run in $(seq 1 "$RODADAS"); do
      # CBR: varia clientes e potência de transmissão.
      for n in 2 4 8 16 32; do
        for pot in 16 18 20 22 26; do
          rodar "$mob" "$proto" cbr "$n" "$pot" "$run"
        done
      done

      # CBR com um cliente, na potência de referência.
      rodar "$mob" "$proto" cbr 1 26 "$run"

      # Rajada e misto: potência de referência.
      for trafego in rajada misto; do
        for n in 1 2 4 8 16 32; do
          rodar "$mob" "$proto" "$trafego" "$n" 26 "$run"
        done
      done
    done
  done
done

echo "Resultados em $CSV"