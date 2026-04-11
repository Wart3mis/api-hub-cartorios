"""
simulador.py — Gerador de massa de dados para o Cartório Hub API
Dispara 20 requisições com payloads realistas, alternando cartórios,
tipos de ato e cenários (payload completo, campo ausente, etc.)
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

NOMES     = ["Ana Lima", "Carlos Souza", "Beatriz Melo", "Pedro Alves", "Juliana Costa",
             "Rafael Cunha", "Simone Barros", "Antônio Braga", "Rosa Neves", "Lucas Ferreira"]
HOSPITAIS = ["Hospital São Lucas", "UPA Central", "Maternidade Esperança", "Hospital das Clínicas"]
REGIMES   = ["COMUNHAO_PARCIAL", "SEPARACAO_TOTAL", "COMUNHAO_UNIVERSAL"]
IMOVEIS   = ["Apartamento", "Casa", "Terreno", "Sala Comercial", "Galpão"]
PODERES   = ["Amplos e gerais", "Específicos para venda de imóvel", "Representação judicial"]
EMPRESAS  = ["Gamma", "Delta", "Sigma", "Omega", "Alpha", "Beta"]
RUAS      = ["das Flores", "Sete de Setembro", "Dom Pedro I", "XV de Novembro", "Marechal Deodoro"]
MUNICIPIOS= ["São Paulo", "Curitiba", "Belo Horizonte", "Porto Alegre", "Salvador"]


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
        "conjuge_1":        random.choice(NOMES),
        "conjuge_2":        random.choice(NOMES),
        "regime_bens":      random.choice(REGIMES),
        "data_celebracao":  data_aleatoria(),
        "testemunha_1":     random.choice(NOMES),
    },
    "OBITO": lambda: {
        "nome_falecido":  random.choice(NOMES),
        "data_obito":     data_aleatoria(),
        "causa_mortis":   random.choice(["Causas naturais", "AVC", "Insuficiência cardíaca"]),
        "local_obito":    random.choice(["Residência", "Hospital Municipal", "UPA"]),
    },
    "ESCRITURA": lambda: {
        "tipo_imovel":       random.choice(IMOVEIS),
        "valor_declarado":   round(random.uniform(150_000, 2_000_000), 2),
        "vendedor":          random.choice(NOMES),
        "comprador":         random.choice(NOMES),
        "matricula_imovel":  str(random.randint(10_000, 99_999)),
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


# ---------------------------------------------------------------------------
# Cenários de simulação — enriquece a massa de dados
# ---------------------------------------------------------------------------

def _cenario(tipo_ato: str, cartorio_id: str) -> dict:
    """
    Retorna o body da requisição.
    10% das vezes injeta um campo extra para simular variação de payload.
    """
    payload = PAYLOADS[tipo_ato]()
    if random.random() < 0.10:
        payload["_obs"] = "Registro com ressalva — conferir documentação original."
    return {"cartorio_id": cartorio_id, "tipo_ato": tipo_ato, "payload": payload}


# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------

TOTAL = 100

def main():
    print("=" * 62)
    print("  SIMULADOR v2 — Cartório Hub API")
    print(f"  Disparando {TOTAL} requisições com retry simulado no servidor...")
    print("=" * 62)

    sucessos = erros = falhas_conexao = 0

    for i in range(1, TOTAL + 1):
        tipo_ato    = random.choice(TIPOS_ATO)
        cartorio_id = random.choice(CARTORIOS)
        body        = _cenario(tipo_ato, cartorio_id)

        try:
            response    = requests.post(URL, json=body, timeout=TIMEOUT)
            code        = response.status_code
            data        = response.json()

            if code == 201:
                tentativas = data.get("payload_enviado", {}).get("_tentativas", "?")
                print(
                    f"[{i:02d}] ✅ SUCESSO  | {code} | {cartorio_id} | {tipo_ato:<12} "
                    f"| id={data['id']} | tentativas={tentativas}"
                )
                sucessos += 1
            else:
                detalhe   = data.get("detail", {})
                log_id    = detalhe.get("log_id", "?") if isinstance(detalhe, dict) else "?"
                tentativas= detalhe.get("tentativas", "?") if isinstance(detalhe, dict) else "?"
                msg       = detalhe.get("mensagem", detalhe) if isinstance(detalhe, dict) else detalhe
                print(
                    f"[{i:02d}] ❌ ERRO     | {code} | {cartorio_id} | {tipo_ato:<12} "
                    f"| id={log_id} | tentativas={tentativas}\n"
                    f"       ↳ {msg}"
                )
                erros += 1

        except requests.exceptions.ConnectionError:
            print(f"[{i:02d}] 🔴 SEM CONEXÃO — API fora do ar em {URL}")
            falhas_conexao += 1
        except requests.exceptions.Timeout:
            print(f"[{i:02d}] 🔴 TIMEOUT   — API não respondeu em {TIMEOUT}s")
            falhas_conexao += 1

        time.sleep(0.1)   # evita flood no servidor local

    print("=" * 62)
    taxa = round(sucessos / (sucessos + erros) * 100, 1) if (sucessos + erros) > 0 else 0
    print(f"  ✅ Sucesso:        {sucessos}")
    print(f"  ❌ Erro negócio:   {erros}")
    print(f"  🔴 Falha conexão:  {falhas_conexao}")
    print(f"  📊 Taxa de sucesso: {taxa}%")
    print("=" * 62)


if __name__ == "__main__":
    main()
