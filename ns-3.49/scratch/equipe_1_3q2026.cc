/*
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * PCS3614 - Redes de Computadores I - Projeto Pratico (3o quadrimestre de 2026)
 * Equipe 1
 *
 * Topologia:
 *
 *   s2     s1     s0
 *   |      |      |
 *   ===================== AP          (CSMA, LAN 10.1.1.0/24)
 *                         *  *  *  *  *
 *                         |  |  |  |  |   (Wi-Fi 802.11a, 192.168.0.0/24, SSID "Equipe1")
 *                        c0 c1 c2 c3 cn
 *
 * O servidor e o no s2 (ultimo no da rede cabeada). Cada cliente sem fio consome um fluxo
 * enviado pelo servidor (downlink s2 -> AP -> ci).
 *
 * Cenarios (parametros de linha de comando):
 *   --nClientes=1|2|4|8|16|32       numero de clientes sem fio
 *   --mobilidade=0|1                0: ConstantPosition; 1: RandomWalk2d (pessoas caminhando)
 *   --protocolo=udp|tcp|misto       misto: 50% dos clientes UDP, 50% TCP (alternados)
 *   --trafego=cbr|rajada|misto      misto: primeira metade CBR, segunda metade em rajada
 *
 * Metricas (FlowMonitor, apenas fluxos de dados servidor -> clientes):
 *   vazao, atraso medio, jitter medio e perda de pacotes. Os resultados sao exibidos no
 *   terminal e acrescentados a um arquivo CSV para a geracao dos graficos.
 *
 * Exemplo:
 *   ./ns3 run "equipe_1_3q2026 --nClientes=8 --mobilidade=1 --protocolo=misto"
 */

#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/csma-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/wifi-module.h"

#include <algorithm>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <string>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("Equipe1Projeto3q2026");

namespace
{

/**
 * Metricas acumuladas de um conjunto de fluxos.
 */
struct Metricas
{
    uint32_t fluxos{0};        ///< numero de fluxos
    uint64_t txPacotes{0};     ///< pacotes transmitidos
    uint64_t rxPacotes{0};     ///< pacotes recebidos
    uint64_t rxBytes{0};       ///< bytes recebidos
    double somaAtraso{0};      ///< soma dos atrasos (s)
    double somaJitter{0};      ///< soma dos jitters (s)
    uint64_t amostrasJitter{0}; ///< numero de amostras de jitter

    /**
     * Acumula as estatisticas de um fluxo.
     * @param st estatisticas do fluxo
     */
    void Adicionar(const FlowMonitor::FlowStats& st)
    {
        fluxos++;
        txPacotes += st.txPackets;
        rxPacotes += st.rxPackets;
        rxBytes += st.rxBytes;
        somaAtraso += st.delaySum.GetSeconds();
        somaJitter += st.jitterSum.GetSeconds();
        if (st.rxPackets > 1)
        {
            amostrasJitter += st.rxPackets - 1;
        }
    }

    /**
     * @param duracao duracao do trafego (s)
     * @return vazao agregada em Mbps
     */
    double VazaoMbps(double duracao) const
    {
        return duracao > 0 ? rxBytes * 8.0 / duracao / 1e6 : 0.0;
    }

    /** @return atraso medio em ms */
    double AtrasoMs() const
    {
        return rxPacotes > 0 ? somaAtraso / rxPacotes * 1e3 : 0.0;
    }

    /** @return jitter medio em ms */
    double JitterMs() const
    {
        return amostrasJitter > 0 ? somaJitter / amostrasJitter * 1e3 : 0.0;
    }

    /** @return perda de pacotes em % */
    double PerdaPct() const
    {
        return txPacotes > 0 ? 100.0 * (txPacotes - std::min(rxPacotes, txPacotes)) / txPacotes
                             : 0.0;
    }
};

/**
 * Imprime um resumo das metricas no terminal.
 * @param rotulo nome do grupo de fluxos
 * @param m metricas
 * @param duracao duracao do trafego (s)
 */
void
ImprimirResumo(const std::string& rotulo, const Metricas& m, double duracao)
{
    std::cout << "  [" << rotulo << "] fluxos=" << m.fluxos << " | vazao=" << m.VazaoMbps(duracao)
              << " Mbps (" << (m.fluxos ? m.VazaoMbps(duracao) * 1e3 / m.fluxos : 0.0)
              << " kbps/cliente) | atraso=" << m.AtrasoMs() << " ms | jitter=" << m.JitterMs()
              << " ms | perda=" << m.PerdaPct() << " % (tx=" << m.txPacotes
              << ", rx=" << m.rxPacotes << ")" << std::endl;
}

} // namespace

int
main(int argc, char* argv[])
{
    // Parametros de simulacao (valores padrao conforme o enunciado)
    uint32_t nClientes = 1;
    bool mobilidade = false;
    std::string protocolo = "udp";
    std::string trafego = "cbr";
    double tempoSimulacao = 60.0;    // s
    double inicioApps = 2.0;         // s (tempo para associacao ao AP)
    double tamanhoCenario = 140.0;   // m (cenario quadrado)
    double potenciaTx = 16.0;        // dBm
    double velMinKmh = 3.6;          // km/h
    double velMaxKmh = 7.2;          // km/h
    std::string taxaDados = "512kbps";
    uint32_t tamPacoteUdp = 512;     // bytes (payload UDP)
    uint32_t tamQuadroTcp = 1500;    // bytes (pacote IP com segmento TCP)
    uint32_t seed = 1;
    uint32_t run = 1;
    std::string arquivoCsv = "equipe_1_resultados.csv";
    bool detalhado = false;

    CommandLine cmd(__FILE__);
    cmd.AddValue("nClientes", "Numero de clientes sem fio", nClientes);
    cmd.AddValue("mobilidade", "Clientes moveis (RandomWalk2d) se verdadeiro", mobilidade);
    cmd.AddValue("protocolo", "Transporte: udp, tcp ou misto (50%/50%)", protocolo);
    cmd.AddValue("trafego", "Aplicacao: cbr, rajada ou misto (CBR/rajada)", trafego);
    cmd.AddValue("tempo", "Tempo de simulacao (s)", tempoSimulacao);
    cmd.AddValue("tamanho", "Lado do cenario quadrado (m)", tamanhoCenario);
    cmd.AddValue("potenciaTx", "Potencia de transmissao Wi-Fi (dBm)", potenciaTx);
    cmd.AddValue("velMin", "Velocidade minima dos clientes moveis (km/h)", velMinKmh);
    cmd.AddValue("velMax", "Velocidade maxima dos clientes moveis (km/h)", velMaxKmh);
    cmd.AddValue("taxa", "Taxa de dados de cada fluxo", taxaDados);
    cmd.AddValue("tamUdp", "Tamanho do pacote UDP (bytes)", tamPacoteUdp);
    cmd.AddValue("tamTcp", "Tamanho do quadro TCP/IP (bytes)", tamQuadroTcp);
    cmd.AddValue("seed", "Semente do gerador aleatorio", seed);
    cmd.AddValue("run", "Numero da rodada (repeticao)", run);
    cmd.AddValue("csv", "Arquivo CSV de saida (vazio para desativar)", arquivoCsv);
    cmd.AddValue("detalhado", "Imprime as estatisticas de cada fluxo", detalhado);
    cmd.Parse(argc, argv);

    if (nClientes < 1)
    {
        std::cerr << "nClientes deve ser >= 1" << std::endl;
        return 1;
    }
    if (protocolo != "udp" && protocolo != "tcp" && protocolo != "misto")
    {
        std::cerr << "protocolo invalido: use udp, tcp ou misto" << std::endl;
        return 1;
    }
    if (trafego != "cbr" && trafego != "rajada" && trafego != "misto")
    {
        std::cerr << "trafego invalido: use cbr, rajada ou misto" << std::endl;
        return 1;
    }
    if (tempoSimulacao <= inicioApps + 1.0)
    {
        std::cerr << "tempo deve ser maior que " << inicioApps + 1.0 << " s" << std::endl;
        return 1;
    }
    if (tamQuadroTcp <= 40)
    {
        std::cerr << "tamTcp deve ser maior que 40 bytes (cabecalhos IP + TCP)" << std::endl;
        return 1;
    }

    RngSeedManager::SetSeed(seed);
    RngSeedManager::SetRun(run);

    // MSS = quadro - 20 (IP) - 20 (TCP), para que cada segmento gere um pacote IP de tamQuadroTcp
    const uint32_t mssTcp = tamQuadroTcp - 40;
    Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(mssTcp));

    // ---------------------------------------------------------------------
    // Nos
    // ---------------------------------------------------------------------
    NodeContainer hostsCabeados;
    hostsCabeados.Create(3); // s0, s1, s2
    Names::Add("s0", hostsCabeados.Get(0));
    Names::Add("s1", hostsCabeados.Get(1));
    Names::Add("s2", hostsCabeados.Get(2));
    Ptr<Node> servidor = hostsCabeados.Get(2);

    NodeContainer apNo;
    apNo.Create(1);
    Names::Add("AP", apNo.Get(0));

    NodeContainer clientes;
    clientes.Create(nClientes);
    for (uint32_t i = 0; i < nClientes; ++i)
    {
        Names::Add("c" + std::to_string(i), clientes.Get(i));
    }

    // ---------------------------------------------------------------------
    // Rede cabeada (LAN 10.1.1.0): s0, s1, s2 e AP
    // ---------------------------------------------------------------------
    NodeContainer noLan;
    noLan.Add(hostsCabeados);
    noLan.Add(apNo);

    CsmaHelper csma;
    csma.SetChannelAttribute("DataRate", StringValue("100Mbps"));
    csma.SetChannelAttribute("Delay", TimeValue(NanoSeconds(6560)));
    NetDeviceContainer dispLan = csma.Install(noLan);

    // ---------------------------------------------------------------------
    // Rede sem fio (192.168.0.0): AP + clientes, IEEE 802.11a
    // ---------------------------------------------------------------------
    YansWifiChannelHelper canal = YansWifiChannelHelper::Default();
    YansWifiPhyHelper phy;
    phy.SetChannel(canal.Create());
    phy.Set("TxPowerStart", DoubleValue(potenciaTx));
    phy.Set("TxPowerEnd", DoubleValue(potenciaTx));
    phy.Set("TxPowerLevels", UintegerValue(1));
    phy.Set("Antennas", UintegerValue(1));

    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211a);
    wifi.SetRemoteStationManager("ns3::IdealWifiManager");

    Ssid ssid = Ssid("Equipe1");
    WifiMacHelper mac;

    mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssid), "ActiveProbing", BooleanValue(false));
    NetDeviceContainer dispClientes = wifi.Install(phy, mac, clientes);

    mac.SetType("ns3::ApWifiMac", "Ssid", SsidValue(ssid));
    NetDeviceContainer dispAp = wifi.Install(phy, mac, apNo);

    // ---------------------------------------------------------------------
    // Mobilidade
    // ---------------------------------------------------------------------
    MobilityHelper mobAp;
    Ptr<ListPositionAllocator> posAp = CreateObject<ListPositionAllocator>();
    posAp->Add(Vector(tamanhoCenario / 2.0, tamanhoCenario / 2.0, 0.0));
    mobAp.SetPositionAllocator(posAp);
    mobAp.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobAp.Install(apNo);

    std::ostringstream uniformePos;
    uniformePos << "ns3::UniformRandomVariable[Min=0.0|Max=" << tamanhoCenario << "]";

    MobilityHelper mobClientes;
    mobClientes.SetPositionAllocator("ns3::RandomRectanglePositionAllocator",
                                     "X",
                                     StringValue(uniformePos.str()),
                                     "Y",
                                     StringValue(uniformePos.str()));
    if (mobilidade)
    {
        std::ostringstream velocidade;
        velocidade << "ns3::UniformRandomVariable[Min=" << velMinKmh / 3.6
                   << "|Max=" << velMaxKmh / 3.6 << "]";
        mobClientes.SetMobilityModel("ns3::RandomWalk2dMobilityModel",
                                     "Bounds",
                                     RectangleValue(Rectangle(0, tamanhoCenario, 0, tamanhoCenario)),
                                     "Speed",
                                     StringValue(velocidade.str()),
                                     "Mode",
                                     StringValue("Time"),
                                     "Time",
                                     TimeValue(Seconds(5.0)));
    }
    else
    {
        mobClientes.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    }
    mobClientes.Install(clientes);

    // ---------------------------------------------------------------------
    // Pilha de protocolos e enderecamento
    // ---------------------------------------------------------------------
    InternetStackHelper pilha;
    pilha.SetIpv6StackInstall(false);
    pilha.Install(hostsCabeados);
    pilha.Install(apNo);
    pilha.Install(clientes);

    Ipv4AddressHelper enderecos;
    enderecos.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer ifLan = enderecos.Assign(dispLan);

    enderecos.SetBase("192.168.0.0", "255.255.255.0");
    Ipv4InterfaceContainer ifAp = enderecos.Assign(dispAp);
    Ipv4InterfaceContainer ifClientes = enderecos.Assign(dispClientes);

    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    const Ipv4Address endServidor = ifLan.GetAddress(2);

    // ---------------------------------------------------------------------
    // Aplicacoes: servidor s2 envia um fluxo para cada cliente
    // ---------------------------------------------------------------------
    const uint16_t portaUdp = 9;
    const uint16_t portaTcp = 5000;
    const DataRate taxa(taxaDados);

    std::map<Ipv4Address, uint32_t> indiceCliente;
    std::map<uint32_t, std::string> descricaoCliente;

    ApplicationContainer appsSink;
    ApplicationContainer appsFonte;

    for (uint32_t i = 0; i < nClientes; ++i)
    {
        const bool usaTcp = (protocolo == "tcp") || (protocolo == "misto" && i % 2 == 1);
        const bool usaRajada = (trafego == "rajada") || (trafego == "misto" && i >= nClientes / 2);

        const std::string fabrica = usaTcp ? "ns3::TcpSocketFactory" : "ns3::UdpSocketFactory";
        const uint16_t porta = usaTcp ? portaTcp : portaUdp;
        const Ipv4Address endCliente = ifClientes.GetAddress(i);

        indiceCliente[endCliente] = i;
        descricaoCliente[i] = std::string(usaTcp ? "TCP" : "UDP") + "/" +
                              (usaRajada ? "rajada" : "CBR");

        PacketSinkHelper sink(fabrica, InetSocketAddress(Ipv4Address::GetAny(), porta));
        appsSink.Add(sink.Install(clientes.Get(i)));

        OnOffHelper fonte(fabrica, InetSocketAddress(endCliente, porta));
        fonte.SetAttribute("PacketSize", UintegerValue(usaTcp ? mssTcp : tamPacoteUdp));
        if (usaRajada)
        {
            // Periodos ON/OFF exponenciais de mesma media: a taxa de pico e o dobro da taxa
            // nominal, para que a taxa media seja igual a do CBR.
            fonte.SetAttribute("DataRate", DataRateValue(DataRate(taxa.GetBitRate() * 2)));
            fonte.SetAttribute("OnTime",
                               StringValue("ns3::ExponentialRandomVariable[Mean=0.5]"));
            fonte.SetAttribute("OffTime",
                               StringValue("ns3::ExponentialRandomVariable[Mean=0.5]"));
        }
        else
        {
            fonte.SetAttribute("DataRate", DataRateValue(taxa));
            fonte.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
            fonte.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
        }

        ApplicationContainer app = fonte.Install(servidor);
        // Pequeno deslocamento entre clientes para evitar fontes perfeitamente sincronizadas
        app.Start(Seconds(inicioApps + 0.005 * i));
        app.Stop(Seconds(tempoSimulacao));
        appsFonte.Add(app);
    }

    appsSink.Start(Seconds(1.0));
    appsSink.Stop(Seconds(tempoSimulacao + 1.0));

    // ---------------------------------------------------------------------
    // Monitoramento e execucao
    // ---------------------------------------------------------------------
    FlowMonitorHelper fmHelper;
    Ptr<FlowMonitor> monitor = fmHelper.InstallAll();

    const std::string rotuloMob = mobilidade ? "movel" : "estatico";

    std::cout << "=== Equipe1 | clientes=" << nClientes << " | mobilidade=" << rotuloMob
              << " | protocolo=" << protocolo << " | trafego=" << trafego
              << " | tempo=" << tempoSimulacao << " s | taxa=" << taxaDados
              << " | seed=" << seed << " run=" << run << " ===" << std::endl;
    std::cout << "Servidor s2: " << endServidor << " | AP (Wi-Fi): " << ifAp.GetAddress(0)
              << " | SSID: Equipe1" << std::endl;

    // 1 s extra apos o fim das aplicacoes para escoar os pacotes em transito
    Simulator::Stop(Seconds(tempoSimulacao + 1.0));
    Simulator::Run();

    for (uint32_t i = 0; i < nClientes; ++i)
{
    auto d = clientes.Get(i)->GetObject<MobilityModel>()
                 ->GetDistanceFrom(apNo.Get(0)->GetObject<MobilityModel>());
    std::cout << "c" << i << " dist AP = " << d << " m" << std::endl;
}

    monitor->CheckForLostPackets();
    Ptr<Ipv4FlowClassifier> classificador =
        DynamicCast<Ipv4FlowClassifier>(fmHelper.GetClassifier());
    const FlowMonitor::FlowStatsContainer& estatisticas = monitor->GetFlowStats();

    const double duracaoTrafego = tempoSimulacao - inicioApps;
    Metricas total;
    Metricas udp;
    Metricas tcp;

    std::cout << std::fixed << std::setprecision(3);
    for (const auto& [idFluxo, st] : estatisticas)
    {
        const Ipv4FlowClassifier::FiveTuple t = classificador->FindFlow(idFluxo);
        // Considera apenas os fluxos de dados servidor -> cliente (ignora ACKs TCP)
        if (t.sourceAddress != endServidor)
        {
            continue;
        }

        total.Adicionar(st);
        if (t.protocol == 6)
        {
            tcp.Adicionar(st);
        }
        else if (t.protocol == 17)
        {
            udp.Adicionar(st);
        }

        if (detalhado)
        {
            const auto it = indiceCliente.find(t.destinationAddress);
            const std::string nome =
                it != indiceCliente.end() ? "c" + std::to_string(it->second) : "?";
            const std::string desc =
                it != indiceCliente.end() ? descricaoCliente[it->second] : "?";
            Metricas f;
            f.Adicionar(st);
            std::cout << "  Fluxo " << idFluxo << " s2 -> " << nome << " (" << t.destinationAddress
                      << ", " << desc << "): vazao=" << f.VazaoMbps(duracaoTrafego) * 1e3
                      << " kbps | atraso=" << f.AtrasoMs() << " ms | jitter=" << f.JitterMs()
                      << " ms | perda=" << f.PerdaPct() << " %" << std::endl;
        }
    }

    std::cout << "Resultados (fluxos servidor -> clientes):" << std::endl;
    ImprimirResumo("TOTAL", total, duracaoTrafego);
    if (udp.fluxos > 0 && tcp.fluxos > 0)
    {
        ImprimirResumo("UDP", udp, duracaoTrafego);
        ImprimirResumo("TCP", tcp, duracaoTrafego);
    }

    if (!arquivoCsv.empty())
    {
        bool novoArquivo = true;
        {
            std::ifstream existente(arquivoCsv);
            novoArquivo = !existente.good() || existente.peek() == std::ifstream::traits_type::eof();
        }

        std::ofstream csv(arquivoCsv, std::ios::app);
        if (!csv)
        {
            std::cerr << "Nao foi possivel abrir " << arquivoCsv << std::endl;
        }
        else
        {
            if (novoArquivo)
            {
                csv << "mobilidade,protocolo,trafego,nClientes,seed,run,grupo,fluxos,"
                       "vazao_total_mbps,vazao_media_cliente_kbps,atraso_medio_ms,"
                       "jitter_medio_ms,perda_pct,tx_pacotes,rx_pacotes\n";
            }
            csv << std::fixed << std::setprecision(6);
            auto escrever = [&](const std::string& grupo, const Metricas& m) {
                csv << rotuloMob << "," << protocolo << "," << trafego << "," << nClientes << ","
                    << seed << "," << run << "," << grupo << "," << m.fluxos << ","
                    << m.VazaoMbps(duracaoTrafego) << ","
                    << (m.fluxos ? m.VazaoMbps(duracaoTrafego) * 1e3 / m.fluxos : 0.0) << ","
                    << m.AtrasoMs() << "," << m.JitterMs() << "," << m.PerdaPct() << ","
                    << m.txPacotes << "," << m.rxPacotes << "\n";
            };
            escrever("total", total);
            if (udp.fluxos > 0)
            {
                escrever("udp", udp);
            }
            if (tcp.fluxos > 0)
            {
                escrever("tcp", tcp);
            }
            std::cout << "Resultados acrescentados em " << arquivoCsv << std::endl;
        }
    }

    Simulator::Destroy();
    return 0;
}
