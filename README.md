# PCS3614 - Redes de Computadores I

## Projeto Prático

**Universidade de São Paulo (USP)**  
**Escola Politécnica (Poli)**  
**Disciplina:** PCS3614 - Redes de Computadores I  
**Professor:** Prof. Dr. Joahannes Bruno Dias da Costa  
**Entrega:** 17 de novembro de 2026

## Resumo

O projeto prático tem como principal objetivo colocar em prática os conceitos aprendidos nas aulas teóricas.

Os tópicos explorados são:

- Instalação do simulador de redes;
- Criação de uma topologia de rede que envolva diferentes enlaces;
- Enlaces com e sem fio operando conjuntamente;
- Cenários com e sem mobilidade dos nós sem fio;
- Utilização de aplicações com TCP, UDP e TCP/UDP;
- Medição de desempenho da rede.

## Instruções gerais

1. O projeto deve ser desenvolvido em equipe de até cinco estudantes. Na página da disciplina no Moodle, em **Projeto Prático / Defina seu grupo**, existe um formulário para definir a composição do grupo. O estudante cujo nome não constar no formulário no momento da entrega terá desconto de 1,0 ponto na nota do projeto.
2. O professor estará disponível sob demanda, mediante agendamento prévio, para esclarecer dúvidas.
3. O projeto é dividido em duas partes:
   - Execução de experimentos no simulador de redes Network Simulator (ns-3);
   - Relatório técnico do que foi desenvolvido.
4. O relatório deve ter no máximo 8 páginas. Para cada página excedente será aplicado desconto de 1,0 ponto.

## Entregáveis

As entregas devem ser feitas exclusivamente pelo Moodle, usando rigorosamente os seguintes nomes:

- **Relatório:** `equipe_x_relatorio_redes_3q2026.pdf`
- **Arquivo de simulação:** `equipe_x_3q2026.cc` ou `equipe_x_3q2026.py`

Substitua `x` pelo número da equipe conforme o formulário do Moodle.

Equipes que não seguirem rigorosamente a nomenclatura estabelecida terão desconto de 1,0 ponto na nota.

## Data da entrega

A entrega deve ser feita até **17 de novembro de 2026, às 23h59**.

Os arquivos devem ser submetidos no Moodle, dentro da tarefa do projeto. Apenas uma pessoa por grupo deve submeter o projeto; não é necessário duplicar as submissões.

Recomenda-se submeter o trabalho com antecedência. Não serão aceitas submissões por outros meios nem entregas após a data e o horário limite, independentemente do motivo do atraso.

## Relatório

Após o desenvolvimento, deve ser entregue um relatório usando o template da Sociedade Brasileira de Computação (LaTeX ou Word).

Modelos:

- [Template LaTeX no Overleaf](https://www.overleaf.com/project/674e4b8981bb8c813a4208b5)
- [Modelos para publicação da SBC](https://www.sbc.org.br/wp-content/uploads/2024/07/modelosparapublicaodeartigos.zip)

O relatório deve conter as seguintes seções:

1. **Resumo:** visão geral do projeto.
2. **Introdução.**
3. **Descrição do exercício proposto:**
   - Apresentar uma imagem da topologia da rede;
   - Usar a criatividade para montar uma representação da topologia.
4. **Avaliação de desempenho:**
   - **Metodologia:** descrever como os experimentos foram realizados e informar a configuração da máquina utilizada;
   - **Parâmetros:** apresentar os parâmetros de simulação dos cenários investigados.
5. **Resultados:**
   - Apresentar gráficos mostrando o impacto das variações;
   - Atraso;
   - Vazão;
   - Perda de pacotes;
   - Discussão dos resultados e explicação dos comportamentos observados nos gráficos.
6. **Detalhamento da divisão do trabalho:** parágrafo ou tabela descrevendo o que cada membro fez.
7. **Conclusão:** explicar os principais pontos do trabalho.

## Desenvolvimento

Documentos importantes para o desenvolvimento:

- [Documentação do ns-3](https://www.nsnam.org)
- [Instalação do ns-3](https://www.nsnam.org/documentation/latest/)
- [Tutorial do ns-3](https://www.nsnam.org/documentation/latest/)
- [Biblioteca de modelos do ns-3](https://www.nsnam.org/documentation/latest/models/)

## Exemplo de parâmetros de simulação

| Parâmetro | Valor |
|---|---|
| Tempo de simulação | 60 s |
| Número de clientes | 1, 2, 4 e 6 |
| Tamanho do cenário | 140 m x 140 m |
| Padrão de comunicação | IEEE 802.11a |
| Potência de transmissão | 16 dBm |
| Velocidade dos clientes no cenário estático | 0 km/h |
| Velocidade dos clientes no cenário móvel | 3,6 a 7,2 km/h |
| Modelo de mobilidade para nós estáticos | `ConstantPositionMobility` |
| Modelo de mobilidade para nós móveis | `ConstantVelocityMobility` |
| Taxa de dados | 512 kbps |
| Tamanho do quadro UDP | 512 bytes |
| Tamanho do quadro TCP | 1500 bytes |
| Número de antenas no AP | 1 |
| Aplicações | CBR, rajada e CBR/rajada |

## Instalação e configuração do simulador

Seguir as indicações da documentação para instalar o simulador no ambiente escolhido. É permitido escolher o sistema operacional.

O projeto deste repositório utiliza o **ns-3.49**, localizado na pasta [`ns-3.49`](./ns-3.49).

## Construção da simulação

A topologia deve conter um host servidor conectado por meio de uma conexão cabeada a um Access Point (AP). O host servidor deve ser o último nó da rede cabeada, representado pelo nó `s2` na figura do enunciado.

Nesse ambiente, `n` clientes (`c0`, `c1`, `c2`, `c3`, ..., `cn`) podem se conectar ao AP para consumir uma aplicação servida pelo host servidor.

O SSID do AP deve ser definido como `EquipeX`, em que `X` é o número da equipe conforme o formulário do Moodle.

É importante variar o número de clientes para que o impacto na rede fique visível.

### Topologia exigida

```text
s2     s1     s0
|      |      |
===================== AP
       LAN 10.1.1.0
       *  *  *  *  *
       |  |  |  |  |
      c0 c1 c2 c3 cn
```

O cenário possui:

- Uma rede cabeada `LAN 10.1.1.0`;
- Um servidor conectado à rede cabeada;
- Um Access Point;
- Clientes conectados ao AP por Wi-Fi;
- Uma rede sem fio `192.168.0.0` no exemplo do enunciado.

## Variações obrigatórias de cenário

Devem ser considerados os seguintes cenários:

1. Nós sem fio (clientes) sem mobilidade.
2. Nós sem fio (clientes) com mobilidade, considerando pessoas caminhando aleatoriamente em uma região.
3. Aplicação usando o protocolo de transporte UDP.
4. Aplicação usando o protocolo de transporte TCP.
5. Cenário em que 50% dos nós usam UDP e 50% usam TCP.
6. Em todos os casos, variar o número de clientes entre:

   ```text
   1, 2, 4, 8, 16 e 32
   ```

Um número maior de clientes pode ser usado para evidenciar o impacto na rede.

## Avaliação

A avaliação considera conjuntamente o relatório e as tarefas práticas realizadas. Serão avaliados tanto o relatório entregue quanto o desenvolvimento, por meio dos códigos.

| Item | Peso |
|---|---:|
| Introdução e descrição do exercício proposto | 10% |
| Avaliação de desempenho | 20% |
| Resultados obtidos | 30% |
| Discussão dos resultados | 30% |
| Conclusão | 10% |

## Considerações finais

- Revisar a documentação oficial do ns-3 para resolver problemas. Fóruns online também podem ser úteis.
- Estabelecer metas iniciais e etapas para avançar no projeto.
- Organizar o uso do tempo, pois a tarefa pode demorar mais do que o esperado.
- Não começar o projeto poucos dias antes da submissão.
- Planejar a entrega e fazer avanços ao longo do período.

