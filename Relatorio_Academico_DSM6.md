# RELATÓRIO TÉCNICO-CIENTÍFICO DE MINERAÇÃO DE DADOS
## ATIVIDADE PRÁTICA AMPLIADA: GESTÃO OPERACIONAL DE EXAMES LABORATORIAIS
**Laboratório Fictício Vida & Dados**

---

**Instituição:** Faculdade de Tecnologia de São Paulo (FATEC)  
**Curso:** Superior de Tecnologia em Desenvolvimento de Software Multiplataforma (DSM)  
**Semestre:** 6º Semestre (DSM6)  
**Componente Curricular:** Mineração de Dados  
**Ambiente de Execução:** Python 3 (Biblioteca Padrão: `csv`, `collections`, `statistics`, `datetime`, `os`, `sys`)  

---

## 1. INTRODUÇÃO E MODELAGEM METODOLÓGICA (KDD E CRISP-DM)

A gestão operacional em serviços de apoio diagnóstico em saúde exige a constante otimização de fluxos produtivos e a garantia rigorosa de prazos contratuais de atendimento (*Service Level Agreements* - SLA). No contexto do laboratório *Vida & Dados*, o objetivo deste trabalho é processar e extrair conhecimento operacional a partir de um conjunto de 252 registros brutos de exames laboratoriais distribuídos entre quatro unidades regionais (Iguape, Jacupiranga, Pariquera-Açu e Registro).

Conforme preconizado na literatura clássica da disciplina (FAYYAD; PIATETSKY-SHAPIRO; SMYTH, 1996; CASTRO; FERRARI, 2016), a Mineração de Dados não atua de forma isolada, mas sim como o núcleo analítico de um processo metodológico mais abrangente denominado **KDD** (*Knowledge Discovery in Databases* - Descoberta de Conhecimento em Bases de Dados). A atividade foi estruturada estritamente nas cinco etapas canônicas do KDD:

```
[1. Seleção] ──> [2. Pré-processamento/Limpeza] ──> [3. Transformação] ──> [4. Mineração/EDA] ──> [5. Avaliação/Interpretação]
```

1. **Seleção:** Carga e filtragem de escopo a partir da base estruturada `Pratica_DSM6_Exames_Laboratoriais.csv` (252 linhas brutas).
2. **Pré-processamento e Limpeza:** Identificação de duplicidades, expurgo de registros redundantes e harmonização sintático-léxica de nomes de unidades.
3. **Transformação:** Conversão de tipos de dados (*casting* de datas e ponto flutuante) e isolamento controlado de valores nulos (*missing values*).
4. **Mineração de Dados / Análise Exploratória (EDA):** Extração de frequências absolutas e relativas, medidas de tendência central e variabilidade (TUKEY, 1977).
5. **Interpretação e Avaliação:** Estruturação da Matriz de Confusão 2x2, mensuração de Precisão (*Precision*) e Revocação (*Recall*), e elaboração de parecer decisório gerencial.

---

## 2. METODOLOGIA DE PRÉ-PROCESSAMENTO E LIMPEZA DE DADOS (ETL)

### 2.1 Justificativa Teórica sobre a Distorção Provocada por Registros Duplicados
Na etapa de auditoria dos dados, identificou-se a presença de 12 registros redundantes com chaves de identificação (`id_exame`) repetidas na base bruta, totalizando 240 exames unívocos após a deduplicação.

A persistência de dados duplicados introduz distorções estatísticas e algorítmicas severas (MD_Aula05):
* **Viés de Amostragem e Frequência:** Em modelos descritivos e inferenciais, assume-se a premissa de que cada linha corresponde a uma observação estocástica independente. A duplicação super-representa artificialmente determinadas unidades, categorias de exame ou rotinas operacionais, falseando a probabilidade a priori das classes.
* **Inflação Artificial de Suporte e Associação:** Caso fossem aplicados algoritmos baseados em regras de associação (como *Apriori* ou *FP-Growth*), os padrões redundantes apresentariam suporte inflacionado, induzindo o minerador a assumir regras espúrias que não espelham a dinâmica real do negócio.
* **Distorção em Medidas de Tendência Central:** A duplicação de tempos de processamento e faturamentos afeta a média aritmética e a variância, deslocando o centro da distribuição.

**Tratamento Adotado:** O algoritmo implementado adota uma deduplicação determinística baseada na chave primária `id_exame`, preservando estritamente a primeira ocorrência observada (*first-seen* / *first-in*), assegurando a integridade referencial da série temporal de coletas.

---

### 2.2 Justificativa Teórica sobre o Tratamento de Valores Ausentes (*Missing Values*)
A auditoria acusou ausências em três atributos da base deduplicada:
* `tempo_processamento_h`: 4 registros nulos (1,67% do total);
* `valor_rs`: 2 registros nulos (0,83% do total);
* `turno`: 2 registros nulos (0,83% do total).

Segundo a taxonomia de Little e Rubin (1987), citada em aula (MD_Aula04), as ausências foram classificadas como **MCAR** (*Missing Completely at Random* - Ausentes Completamente ao Acaso), uma vez que a proporção é diminuta (< 2%) e encontra-se espalhada aleatoriamente sem correlação com o tipo de exame ou a unidade de atendimento.

#### Por que NÃO substituir valores ausentes por zero?
A substituição cega de dados ausentes por zero (*zero-imputation*) é categoricamente desaconselhada pelas seguintes razões:
1. **Inconsistência Semântica e Física:** No domínio da biomedicina laboratorial, um tempo de processamento igual a $0{,}00\text{ h}$ ou um valor de cobrança de $R\$\,0{,}00$ constitui uma aberração conceitual; todo exame consome tempo de bancada e insumos reagentes.
2. **Distorção Gravíssima de Médias e Variâncias:** Matematicamente, a inclusão de valores nulos codificados como zero no denominador da média aritmética atua como um atrator descendente espúrio. Por exemplo, calcular a média de tempo de processamento inserindo zeros em 4 exames reduziria a média global arbitrariamente, mascarando atrasos reais e simulando uma produtividade artificial.
3. **Introdução de Picos Artificiais na Distribuição:** Atribuir zero altera radicalmente a assimetria (*skewness*) e curtose da amostra, arruinando posteriores análises de normalidade ou modelos de regressão.

#### Estratégias de Tratamento Adotadas:
* **Exclusão Emparelhada (*Pairwise Deletion*):** Para os atributos quantitativos contínuos (`tempo_processamento_h` e `valor_rs`), preservou-se o registro global com valor `None`. As agregações matemáticas (média, mediana e soma) desconsideram pontualmente apenas os valores nulos do respectivo atributo, explicitando em cada relatório o tamanho efetivo da amostra observada ($n$).
* **Categorização de Ausência Informativa (*Informative Missingness*):** Para a variável qualitativa nominal `turno`, o campo vazio foi convertido explicitamente para a classe `"Nao informado"`. Essa abordagem evita a perda de registros válidos nas demais colunas e documenta formalmente a falha de preenchimento na recepção/triagem.

---

### 2.3 Padronização Sintática e Tipagem Estrita
Os nomes das unidades apresentavam anomalias léxicas (espaços em branco nas bordas e entre palavras, bem como inconsistências de caixa: `"REGISTRO"`, `" jacupiranga "`, `"Pariquera-Açu"`). Aplicou-se a função de saneamento `padronizar_unidade`, que isola tokens via `.split()` e recombina em formato *Title Case*, garantindo que as quatro unidades regionais fossem perfeitamente consolidadas. O campo `data_coleta` foi convertido para objetos `datetime.date`, viabilizando ordenações cronológicas confiáveis.

---

## 3. APRESENTAÇÃO E DISCUSSÃO DOS RELATÓRIOS (R01 A R12)

### 3.1 Bloco A: Relatórios de Qualidade de Dados e Produção
* **[R01] Volume Bruto:** 252 linhas importadas.
* **[R02] Deduplicação:** 12 registros redundantes descartados; base final composta por **240 exames únicos**.
* **[R03] Dados Ausentes:** `tempo_processamento_h` (4; 1,67%), `valor_rs` (2; 0,83%), `turno` (2; 0,83%).
* **[R04] Distribuição por Unidade (Ordem Alfabética):**
  * Iguape: 62 exames (25,83%)
  * Jacupiranga: 65 exames (27,08%)
  * Pariquera-Açu: 58 exames (24,17%)
  * Registro: 55 exames (22,92%)  
  *Observação:* A distribuição espacial de atendimento apresenta equilíbrio notável, oscilando entre 22,9% e 27,1%.
* **[R05] Demanda Produtiva por Tipo de Exame (Ordem Alfabética):**
  * Colesterol: 43 exames (17,92%)
  * Glicemia: 29 exames (12,08%)
  * Hemograma: 35 exames (14,58%)
  * TSH: 40 exames (16,67%)
  * Triglicerídeos: 50 exames (20,83%)
  * Urina tipo I: 43 exames (17,92%)
* **[R06] Distribuição por Prioridade:**
  * Rotina: 177 exames (73,75%)
  * Urgente: 63 exames (26,25%)
* **[R07] Distribuição por Turno Operacional:**
  * Manhã: 79 exames (32,92%)
  * Tarde: 80 exames (33,33%)
  * Noite: 79 exames (32,92%)
  * Não informado: 2 exames (0,83%)
* **[R08] Taxa Relativa de Recoleta de Amostras:**
  * Jacupiranga: **20,00%** (13 / 65) — Maior taxa crítica de descarte/recoleta.
  * Registro: 14,55% (8 / 55)
  * Iguape: 14,52% (9 / 62)
  * Pariquera-Açu: 12,07% (7 / 58) — Melhor índice de retenção pré-analítica.

---

### 3.2 Bloco B: Relatórios Analíticos e Desempenho Operacional
* **[R09] Faturamento e Ticket Médio por Tipo de Exame:**
  * **TSH:** Total = R$ 1.664,00 | Média = R$ 41,60 ($n = 40$)
  * **Triglicerídeos:** Total = R$ 1.320,00 | Média = R$ 26,94 ($n = 49$, 1 ausente)
  * **Colesterol:** Total = R$ 1.073,00 | Média = R$ 24,95 ($n = 43$)
  * **Hemograma:** Total = R$ 1.060,00 | Média = R$ 31,18 ($n = 34$, 1 ausente)
  * **Urina tipo I:** Total = R$ 1.009,00 | Média = R$ 23,47 ($n = 43$)
  * **Glicemia:** Total = R$ 507,00 | Média = R$ 17,48 ($n = 29$)  
  *Faturamento Total Apurado:* R$ 6.633,00 com base em 238 registros tarifados.
* **[R10] Tempo Médio e Mediana de Processamento:**
  * **Rotina (Meta SLA = 24 h):** Média = 18,85 h | Mediana = 19,00 h ($n = 175$, 2 ausentes)
  * **Urgente (Meta SLA = 4 h):** Média = **5,41 h** | Mediana = **5,00 h** ($n = 61$, 2 ausentes)  
  *Diagnóstico Operacional Crítico:* Na categoria Urgente, tanto a média (5,41 h) quanto a mediana (5,00 h) encontram-se **acima do SLA regulamentar de 4 horas**, comprovando a existência de um gargalo severo na linha de liberação rápida.
* **[R11] Taxa de Não Conformidade (Atraso Real) por Unidade:**
  * Pariquera-Açu: **39,66%** (23 / 58) — Pior desempenho pontual em cumprimento de prazos.
  * Jacupiranga: 36,92% (24 / 65)
  * Registro: 34,55% (19 / 55)
  * Iguape: 30,65% (19 / 62)
* **[R12] Ranking dos Três Tipos de Exame Mais Frequentes:**
  * **1º Lugar:** Triglicerídeos — 50 exames (20,83%)
  * **2º Lugar:** Colesterol — 43 exames (17,92%) *(Empate estatístico)*
  * **3º Lugar:** Urina tipo I — 43 exames (17,92%) *(Empate estatístico)*  
  *Nota Acadêmica:* Há um empate perfeito na segunda colocação entre Colesterol e Urina tipo I, aspecto relevante para o dimensionamento de insumos laboratoriais.

---

## 4. CLASSIFICAÇÃO OPERACIONAL E AVALIAÇÃO DE DESEMPENHO (R13 A R15)

### 4.1 Heurística e Matriz de Confusão 2x2
A coordenação do laboratório estipulou uma regra preventiva de alerta operacional: sinalizar **Risco de Atraso** quando uma amostra atingir $tempo \ge 20{,}0\text{ h}$ em exames de rotina ou $tempo \ge 3{,}0\text{ h}$ em exames urgentes.

Conforme as diretrizes da atividade, 4 registros foram excluídos por carência de dados no campo de tempo, resultando em um universo de validação composto por **236 exames**. O cruzamento entre a predição heurística e a verdade de campo (`atraso == 'Sim'`) é apresentado na tabela de contingência a seguir:

| Real \ Predição | Predito POSITIVO (Alerta de Risco) | Predito NEGATIVO (Sem Alerta) | Total Real |
| :--- | :---: | :---: | :---: |
| **Real POSITIVO (Atraso Real)** | **TP = 84** *(Acerto)* | **FN = 0** *(Erro Tipo II)* | **84** |
| **Real NEGATIVO (No Prazo)** | **FP = 51** *(Erro Tipo I)* | **TN = 101** *(Acerto)* | **152** |
| **Total Predito** | **135** | **101** | **236** |

* **TP (Verdadeiro Positivo):** 84 exames foram antecipados pela regra e de fato atrasaram.
* **FP (Falso Positivo - Erro do Tipo I):** 51 exames dispararam o alerta, mas foram liberados dentro do SLA.
* **FN (Falso Negativo - Erro do Tipo II):** 0 exames atrasaram sem que o sistema emitisse aviso preventivo.
* **TN (Verdadeiro Negativo):** 101 exames transcorreram sem alerta e cumpriram rigorosamente o prazo.

---

### 4.2 Métricas Formais de Desempenho
As métricas consolidadas na Aula 15 (MD_Aula15) foram calculadas com quatro casas decimais:

$$\text{Precisão (Precision)} = \frac{TP}{TP + FP} = \frac{84}{84 + 51} = \frac{84}{135} \approx \mathbf{0{,}6222}$$

$$\text{Revocação (Recall / Sensibilidade)} = \frac{TP}{TP + FN} = \frac{84}{84 + 0} = \frac{84}{84} = \mathbf{1{,}0000}$$

---

### 4.3 [R15] Parecer Técnico-Gerencial e Limitações do Modelo (4 a 6 Linhas Formais)

> Como decisão gerencial, a diretoria laboratorial pode adotar a heurística como um protocolo *fail-safe* de prevenção operacional e reordenamento de filas de bancada, visto que o recall perfeito (1,0000) assegura a erradicação total de erros do Tipo II, impedindo que qualquer amostra exceda o SLA sem notificação prévia. Por outro lado, a limitação crítica reside na baixa precisão (0,6222), derivada de cortes temporais estáticos que produzem 51 alarmes falsos (Erro Tipo I), demandando intervenções de bancada desnecessárias e gerando risco de fadiga de alertas na equipe biomédica.

---

## 5. RECOMENDAÇÕES PARA A EVOLUÇÃO DO MODELO
Com base no ciclo iterativo do KDD e nas técnicas lecionadas nas Aulas 12 a 15, recomenda-se substituir a heurística univariada por modelos supervisionados de Aprendizado de Máquina:
1. **Árvores de Decisão (C4.5 / CART; MD_Aula13):** Permitem segmentar os limiares de tempo não apenas pela prioridade, mas também pelo tipo de exame e pela unidade regional, aumentando significativamente a precisão.
2. **Regressão Logística ou Naive Bayes (MD_Aula14):** Capazes de emitir uma probabilidade contínua de atraso ($P(\text{atraso} \mid X)$), possibilitando à equipe definir curvas ROC e calibrar o limiar de decisão de acordo com os custos financeiros e contratuais de cada tipo de falha.

---

## 6. REFERÊNCIAS BIBLIOGRÁFICAS

* CASTRO, Leandro Nunes de; FERRARI, Daniel. **Introdução à Mineração de Dados: Conceitos e Aplicações**. São Paulo: Saraiva, 2016.
* FAYYAD, Usama; PIATETSKY-SHAPIRO, Gregory; SMYTH, Padhraic. From data mining to knowledge discovery in databases. **AI Magazine**, v. 17, n. 3, p. 37-54, 1996.
* LITTLE, Roderick J. A.; RUBIN, Donald B. **Statistical Analysis with Missing Data**. New York: John Wiley & Sons, 1987.
* TUKEY, John W. **Exploratory Data Analysis**. Reading: Addison-Wesley, 1977.

