"""
simulador.py — Gerador de massa de dados para o Cartório Hub API
Simula o sistema do cartório notificando o Hub com o resultado
do envio direto às plataformas governamentais (SUCESSO ou ERRO).
"""
import random
import time
import requests

URL     = "http://localhost:8000/api/v1/relatorios"
TIMEOUT = 5

TIPOS_ATO = [
    "NASCIMENTO", "CASAMENTO", "OBITO",
    "ESCRITURA", "PROCURACAO", "MATRICULA", "REGISTRO",
]

CARTORIOS = ["SP-001", "RJ-042", "MG-017", "BA-008", "RS-033", "PR-021", "SC-009"]

NOMES      = ["Ana Lima", "Carlos Souza", "Beatriz Melo", "Pedro Alves", "Juliana Costa",
              "Rafael Cunha", "Simone Barros", "Antônio Braga", "Rosa Neves", "Lucas Ferreira"]
HOSPITAIS  = ["Hospital São Lucas", "UPA Central", "Maternidade Esperança", "Hospital das Clínicas"]
REGIMES    = ["COMUNHAO_PARCIAL", "SEPARACAO_TOTAL", "COMUNHAO_UNIVERSAL"]
IMOVEIS    = ["Apartamento", "Casa", "Terreno", "Sala Comercial", "Galpão"]
PODERES    = ["Amplos e gerais", "Específicos para venda de imóvel", "Representação judicial"]
EMPRESAS   = ["Gamma", "Delta", "Sigma", "Omega", "Alpha", "Beta"]
RUAS       = ["das Flores", "Sete de Setembro", "Dom Pedro I", "XV de Novembro", "Marechal Deodoro"]
MUNICIPIOS = ["São Paulo", "Curitiba", "Belo Horizonte", "Porto Alegre", "Salvador"]

ERROS_GOV = [
    "Timeout ao conectar com a central (gateway 504).",
    "Serviço da central indisponível (503 Service Unavailable).",
    "Erro de autenticação na central (401 Unauthorized).",
    "Resposta malformada recebida do servidor da central.",
    "Conexão recusada pela central após 30s de espera.",
]

# 70% de sucesso simulando a taxa real de aprovação dos órgãos
SUCCESS_RATE = 0.70


def data_aleatoria() -> str:
    return f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/2024"


PAYLOADS = {
    "NASCIMENTO": lambda: {
        "nome_registrado": random.choice(NOMES),
        "data_nascimento":  data_aleatoria(),
        "nome_mae":         random.choice(NOMES),
        "nome_pai":         random.choice(NOMES),
        "hospital":         random.choice(HOSPITAIS),
    },
    "CASAMENTO": lambda: {
        "conjuge_1":       random.choice(NOMES),
        "conjuge_2":       random.choice(NOMES),
        "regime_bens":     random.choice(REGIMES),
        "data_celebracao": data_aleatoria(),
        "testemunha_1":    random.choice(NOMES),
    },
    "OBITO": lambda: {
        "nome_falecido": random.choice(NOMES),
        "data_obito":    data_aleatoria(),
        "causa_mortis":  random.choice(["Causas naturais", "AVC", "Insuficiência cardíaca"]),
        "local_obito":   random.choice(["Residência", "Hospital Municipal", "UPA"]),
    },
    "ESCRITURA": lambda: {
        "tipo_imovel":      random.choice(IMOVEIS),
        "valor_declarado":  round(random.uniform(150_000, 2_000_000), 2),
        "vendedor":         random.choice(NOMES),
        "comprador":        random.choice(NOMES),
        "matricula_imovel": str(random.randint(10_000, 99_999)),
    },
    "PROCURACAO": lambda: {
        "outorgante": random.choice(NOMES),
        "outorgado":  f"Dr(a). {random.choice(NOMES)}",
        "poderes":    random.choice(PODERES),
        "validade":   random.choice(["1 ano", "2 anos", "Indeterminado"]),
    },
    "MATRICULA": lambda: {
        "numero_matricula": str(random.randint(100_000, 999_999)),
        "proprietario":     random.choice(NOMES),
        "area_m2":          round(random.uniform(40, 800), 2),
        "logradouro":       f"Rua {random.choice(RUAS)}, {random.randint(1, 999)}",
        "municipio":        random.choice(MUNICIPIOS),
    },
    "REGISTRO": lambda: {
        "tipo_registro": random.choice(["Contrato Social", "Alteração Contratual", "Dissolução"]),
        "razao_social":  f"Empresa {random.choice(EMPRESAS)} Ltda.",
        "cnpj":          f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}",
        "data_registro": data_aleatoria(),
    },
}


def montar_notificacao(tipo_ato: str, cartorio_id: str) -> dict:
    """
    Simula o sistema do cartório montando a notificação de resultado
    para enviar ao Hub após comunicação com o órgão governamental.
    """
    sucesso = random.random() < SUCCESS_RATE

    return {
        "cartorio_id":   cartorio_id,
        "tipo_ato":      tipo_ato,
        "status":        "SUCESSO" if sucesso else "ERRO",
        "payload":       PAYLOADS[tipo_ato](),
        "mensagem_erro": None if sucesso else random.choice(ERROS_GOV),
    }


# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------

TOTAL = 20

def main():
    print("=" * 62)
    print("  SIMULADOR — Cartório Hub API")
    print(f"  Disparando {TOTAL} notificações de resultado para o Hub...")
    print("=" * 62)

    sucessos = erros = falhas_conexao = 0

    for i in range(1, TOTAL + 1):
        tipo_ato    = random.choice(TIPOS_ATO)
        cartorio_id = random.choice(CARTORIOS)
        body        = montar_notificacao(tipo_ato, cartorio_id)

        try:
            response = requests.post(URL, json=body, timeout=TIMEOUT)
            code     = response.status_code
            data     = response.json()

            if code == 201:
                label = "✅ SUCESSO" if data["status"] == "SUCESSO" else "❌ ERRO   "
                print(
                    f"[{i:02d}] {label} | {cartorio_id} | {tipo_ato:<12} | log_id={data['id']}"
                )
                if data["status"] == "SUCESSO":
                    sucessos += 1
                else:
                    erros += 1
            else:
                print(f"[{i:02d}] 🔴 FALHA HUB | {code} | {data.get('detail', '')}")
                falhas_conexao += 1

        except requests.exceptions.ConnectionError:
            print(f"[{i:02d}] 🔴 SEM CONEXÃO — API fora do ar em {URL}")
            falhas_conexao += 1
        except requests.exceptions.Timeout:
            print(f"[{i:02d}] 🔴 TIMEOUT   — API não respondeu em {TIMEOUT}s")
            falhas_conexao += 1

        time.sleep(0.1)

    total_hub = sucessos + erros
    taxa = round(sucessos / total_hub * 100, 1) if total_hub > 0 else 0
    print("=" * 62)
    print(f"  ✅ Atos com SUCESSO:   {sucessos}")
    print(f"  ❌ Atos com ERRO:      {erros}")
    print(f"  🔴 Falhas no Hub:      {falhas_conexao}")
    print(f"  📊 Taxa de sucesso:    {taxa}%")
    print("=" * 62)


if __name__ == "__main__":
    main()
