#!/usr/bin/env bash
set -e
RODADAS=${1:-1}
OUT="$(pwd)/resultados_tmp"; CSV="$(pwd)/equipe_1_resultados.csv"
rm -rf "$OUT" "$CSV"; mkdir -p "$OUT"
./ns3 build equipe_1_3q2026

rodar() {  # args: mob proto trafego n pot run
  ./ns3 run --no-build "equipe_1_3q2026 --tempo=60 --nClientes=$4 --tamanho=140 \
    --potenciaTx=$5 --velMin=3.6 --velMax=7.2 --taxa=512kbps --tamUdp=512 --tamTcp=1500 \
    --mobilidade=$1 --protocolo=$2 --trafego=$3 --run=$6 \
    --csv=$OUT/m$1_p$2_t$3_n$4_w$5_r$6.csv" > /dev/null
}
export -f rodar; export OUT

gerar() {
  for mob in 0 1; do for proto in udp tcp misto; do for run in $(seq 1 "$RODADAS"); do
    # varredura completa de potencia, so cbr, n>=2
    for n in 2 4 8 16 32; do for pot in 16 18 20 22 26; do
      echo $mob $proto cbr $n $pot $run; done; done
    # n=1 uma vez
    echo $mob $proto cbr 1 26 $run
    # outros trafegos so na potencia de referencia
    for tr in rajada misto; do for n in 1 2 4 8 16 32; do
      echo $mob $proto $tr $n 26 $run; done; done
  done; done; done
}

gerar | xargs -P 10 -L 1 bash -c 'rodar "$@"' _

# junta os CSVs (mantem o cabecalho so uma vez)
f=$(ls "$OUT"/*.csv | head -1); head -1 "$f" > "$CSV"
tail -q -n +2 "$OUT"/*.csv >> "$CSV"
echo "Resultados em $CSV"