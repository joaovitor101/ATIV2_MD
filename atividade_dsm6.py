import csv
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime


class DualOutputLogger:
    """Direciona a saida para o console e salva o arquivo de texto."""

    def __init__(self, caminho_arquivo: str):
        self.terminal = sys.stdout
        self.arquivo = open(caminho_arquivo, mode="w", encoding="utf-8")

    def write(self, mensagem: str) -> None:
        self.terminal.write(mensagem)
        self.arquivo.write(mensagem)

    def flush(self) -> None:
        self.terminal.flush()
        self.arquivo.flush()

    def fechar(self) -> None:
        self.arquivo.close()


def padronizar_unidade(texto: str) -> str:
    """Remove espacos extras e padroniza maiusculas/minusculas."""
    return " ".join(texto.strip().split()).title()


def carregar_dados(caminho_csv: str) -> tuple[int, int, list[dict]]:
    """Le o CSV, deduplica por id_exame e converte tipos de dados."""
    with open(caminho_csv, mode="r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        linhas = list(leitor)

    total_importado = len(linhas)
    ids_vistos = set()
    total_duplicados = 0
    registros = []

    for linha in linhas:
        id_exame = linha["id_exame"].strip()
        if id_exame in ids_vistos:
            total_duplicados += 1
            continue
        ids_vistos.add(id_exame)

        # Conversao e padronizacao dos campos
        data_coleta = datetime.strptime(linha["data_coleta"].strip(), "%d/%m/%Y").date()
        unidade = padronizar_unidade(linha["unidade"])
        tipo_exame = linha["tipo_exame"].strip()
        prioridade = linha["prioridade"].strip()
        atraso = linha["atraso"].strip()
        recoleta = linha["recoleta"].strip()
        amostra = linha["amostra"].strip()

        # Turno ausente tratado como categoria explicita
        turno = linha["turno"].strip() or "Nao informado"

        # Numericos ausentes mantidos como None (sem imputacao por zero)
        tempo_str = linha["tempo_processamento_h"].strip()
        tempo_h = float(tempo_str) if tempo_str else None

        prazo_h = float(linha["prazo_h"].strip())

        valor_str = linha["valor_rs"].strip()
        valor_rs = float(valor_str) if valor_str else None

        registros.append(
            {
                "id_exame": id_exame,
                "data_coleta": data_coleta,
                "unidade": unidade,
                "tipo_exame": tipo_exame,
                "prioridade": prioridade,
                "tempo_processamento_h": tempo_h,
                "prazo_h": prazo_h,
                "atraso": atraso,
                "recoleta": recoleta,
                "valor_rs": valor_rs,
                "turno": turno,
                "amostra": amostra,
            }
        )

    return total_importado, total_duplicados, registros


def relatorios_bloco_a(total_importado: int, total_duplicados: int, registros: list[dict]) -> None:
    """Relatorios R01 a R08 - Qualidade e producao."""
    print("=" * 72)
    print("BLOCO A - RELATORIOS DE QUALIDADE E PRODUCAO")
    print("=" * 72)

    # R01
    print("\n[R01] Quantidade total de linhas importadas:")
    print(f"  - Total de linhas brutas: {total_importado}")

    # R02
    total_unicos = len(registros)
    print("\n[R02] Registros duplicados e exames unicos:")
    print(f"  - Duplicados descartados: {total_duplicados}")
    print(f"  - Total de exames unicos: {total_unicos}")

    # R03
    ausentes_tempo = sum(1 for r in registros if r["tempo_processamento_h"] is None)
    ausentes_valor = sum(1 for r in registros if r["valor_rs"] is None)
    ausentes_turno = sum(1 for r in registros if r["turno"] == "Nao informado")
    print("\n[R03] Quantidade de valores ausentes:")
    print(f"  - tempo_processamento_h: {ausentes_tempo}")
    print(f"  - valor_rs:              {ausentes_valor}")
    print(f"  - turno:                 {ausentes_turno}")

    # R04
    contagem_unidade = Counter(r["unidade"] for r in registros)
    print("\n[R04] Quantidade de exames por unidade (ordem alfabetica):")
    for unidade in sorted(contagem_unidade):
        print(f"  - {unidade:<15}: {contagem_unidade[unidade]}")

    # R05
    contagem_tipo = Counter(r["tipo_exame"] for r in registros)
    print("\n[R05] Quantidade de exames por tipo_exame (ordem alfabetica):")
    for tipo in sorted(contagem_tipo):
        print(f"  - {tipo:<15}: {contagem_tipo[tipo]}")

    # R06
    contagem_prioridade = Counter(r["prioridade"] for r in registros)
    print("\n[R06] Quantidade de exames por prioridade:")
    for prioridade in ("Rotina", "Urgente"):
        print(f"  - {prioridade:<15}: {contagem_prioridade[prioridade]}")

    # R07
    contagem_turno = Counter(r["turno"] for r in registros)
    print("\n[R07] Quantidade de exames por turno:")
    for turno in ("Manha", "Tarde", "Noite", "Nao informado"):
        print(f"  - {turno:<15}: {contagem_turno[turno]}")

    # R08
    recoletas = defaultdict(lambda: [0, 0])
    for r in registros:
        recoletas[r["unidade"]][1] += 1
        if r["recoleta"] == "Sim":
            recoletas[r["unidade"]][0] += 1

    print("\n[R08] Percentual de recoleta por unidade:")
    for unidade in sorted(recoletas):
        sim, total = recoletas[unidade]
        perc = (sim / total) * 100 if total > 0 else 0.0
        print(f"  - {unidade:<15}: {perc:6.2f}% ({sim}/{total})")


def relatorios_bloco_b(registros: list[dict]) -> None:
    """Relatorios R09 a R12 - Analise financeira e operacional."""
    print("\n" + "=" * 72)
    print("BLOCO B - RELATORIOS ANALITICOS E CLASSIFICACAO")
    print("=" * 72)

    # R09
    valores_tipo = defaultdict(list)
    for r in registros:
        if r["valor_rs"] is not None:
            valores_tipo[r["tipo_exame"]].append(r["valor_rs"])

    print("\n[R09] Valor total e medio por tipo de exame (ignorando ausentes):")
    for tipo in sorted({r["tipo_exame"] for r in registros}):
        valores = valores_tipo[tipo]
        n_obs = len(valores)
        total_rs = sum(valores)
        media_rs = statistics.mean(valores) if n_obs > 0 else 0.0
        print(
            f"  - {tipo:<15}: Total = R$ {total_rs:8.2f} | "
            f"Media = R$ {media_rs:6.2f} (n = {n_obs} exames)"
        )

    # R10
    tempos_prio = defaultdict(list)
    for r in registros:
        if r["tempo_processamento_h"] is not None:
            tempos_prio[r["prioridade"]].append(r["tempo_processamento_h"])

    print("\n[R10] Tempo medio e mediana de processamento por prioridade:")
    for prio in ("Rotina", "Urgente"):
        tempos = tempos_prio[prio]
        n_obs = len(tempos)
        media_h = statistics.mean(tempos)
        mediana_h = statistics.median(tempos)
        print(
            f"  - {prio:<15}: Media = {media_h:5.2f} h | "
            f"Mediana = {mediana_h:5.2f} h (n = {n_obs} exames)"
        )

    # R11
    atrasos = defaultdict(lambda: [0, 0])
    for r in registros:
        atrasos[r["unidade"]][1] += 1
        if r["atraso"] == "Sim":
            atrasos[r["unidade"]][0] += 1

    print("\n[R11] Percentual de atraso real por unidade:")
    for unidade in sorted(atrasos):
        sim, total = atrasos[unidade]
        perc = (sim / total) * 100 if total > 0 else 0.0
        print(f"  - {unidade:<15}: {perc:6.2f}% ({sim}/{total})")

    # R12
    contagem_tipo = Counter(r["tipo_exame"] for r in registros)
    print("\n[R12] Tres tipos de exame mais frequentes:")
    for pos, (tipo, qtd) in enumerate(contagem_tipo.most_common(3), start=1):
        print(f"  {pos}o. {tipo:<15}: {qtd} exames")


def relatorios_bloco_c(registros: list[dict]) -> None:
    """Relatorios R13 a R15 - Classificacao, matriz e metricas."""
    # R13
    tp = fp = fn = tn = excluidos = 0

    for r in registros:
        tempo = r["tempo_processamento_h"]
        if tempo is None:
            excluidos += 1
            continue

        alerta = (tempo >= 20.0) if r["prioridade"] == "Rotina" else (tempo >= 3.0)
        atrasou = r["atraso"] == "Sim"

        if alerta and atrasou:
            tp += 1
        elif alerta and not atrasou:
            fp += 1
        elif not alerta and atrasou:
            fn += 1
        else:
            tn += 1

    total_avaliado = tp + fp + fn + tn

    print("\n[R13] Matriz de confusao do alerta operacional:")
    print(f"  - Registros avaliados: {total_avaliado} (excluidos sem tempo: {excluidos})")
    print("  +--------------------------+--------------------+--------------------+")
    print("  | Real \\ Predicao          | Predito POSITIVO   | Predito NEGATIVO   |")
    print("  +--------------------------+--------------------+--------------------+")
    print(f"  | Real POSITIVO (Atraso)   | TP = {tp:<14} | FN = {fn:<14} |")
    print(f"  | Real NEGATIVO (No Prazo) | FP = {fp:<14} | TN = {tn:<14} |")
    print("  +--------------------------+--------------------+--------------------+")
    print(f"  - TP (Verdadeiro Positivo): {tp}")
    print(f"  - FP (Falso Positivo):      {fp}")
    print(f"  - FN (Falso Negativo):      {fn}")
    print(f"  - TN (Verdadeiro Negativo): {tn}")

    # R14
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    print("\n[R14] Metricas de avaliacao do alerta:")
    print(f"  - Precisao (Precision): {precision:.4f}")
    print(f"  - Revocacao (Recall):   {recall:.4f}")

    # R15
    print("\n[R15] Interpretacao gerencial e limitacao da regra:")
    print(
        "  Como decisao gerencial, a diretoria pode adotar o alerta para contingencia e\n"
        "  priorizacao de bancada, pois a revocacao de 1.0000 elimina falsos negativos e\n"
        "  evita estouros de SLA. Em contrapartida, a limitacao e a baixa precisao (0.6222),\n"
        "  que gera 51 alarmes falsos decorrentes do corte temporal estatico antecipado,\n"
        "  provocando retrabalho e risco de fadiga de alertas na equipe tecnica."
    )
    print("\n" + "=" * 72)


def main() -> None:
    pasta = os.path.dirname(os.path.abspath(__file__))
    caminho_csv = os.path.join(pasta, "Pratica_DSM6_Exames_Laboratoriais.csv")
    caminho_txt = os.path.join(pasta, "saida_execucao.txt")

    logger = DualOutputLogger(caminho_txt)
    sys.stdout = logger

    try:
        total_importado, total_duplicados, registros = carregar_dados(caminho_csv)
        relatorios_bloco_a(total_importado, total_duplicados, registros)
        relatorios_bloco_b(registros)
        relatorios_bloco_c(registros)
    finally:
        sys.stdout = logger.terminal
        logger.fechar()


if __name__ == "__main__":
    main()
