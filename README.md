# api-hub-cartorios

Hub via webservice em Python (FastAPI) para centralização, auditoria e gestão de 
volumetria de atos cartoriais.  
**Projeto de TCC — MBA em Engenharia de Software (USP/Esalq)**

---

## Sobre o Projeto

Este repositório contém o código-fonte do protótipo desenvolvido como Trabalho de 
Conclusão de Curso (TCC) para o MBA em Engenharia de Software da USP/Esalq.

O projeto consiste em uma **API Centralizadora (Hub)** desenvolvida para sanar a
deficiência de rastreabilidade em integrações de sistemas cartoriais com plataformas
governamentais (e-Notariado, CRC, SIRC e ONR). O cartório realiza o envio diretamente
aos órgãos com suas próprias credenciais institucionais e, após receber o retorno,
notifica o Hub com o resultado. O microsserviço centraliza os logs de auditoria,
expõe métricas gerenciais em tempo real e disponibiliza um painel visual interativo.

---

## Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12 + FastAPI 0.115 |
| Validação | Pydantic v2 |
| ORM | SQLAlchemy 2.0 |
| Banco de Dados | PostgreSQL 15 |
| Infraestrutura | Docker + Docker Compose |
| Testes de Rota | Postman |

---

## Como Executar o Projeto Localmente

### Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose instalados
- Python 3.10+ instalado

### Passo a passo

**1. Clone o repositório**
```bash
git clone https://github.com/Wart3mis/api-hub-cartorios.git
cd api-hub-cartorios
```

**2. Configure as variáveis de ambiente**
```bash
cp .env.example .env
```

**3. Suba o banco de dados via Docker**
```bash
docker-compose up -d
```

**4. Crie o ambiente virtual e instale as dependências**
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

**5. Inicie a API**
```bash
uvicorn main:app --reload
```

A API estará disponível em `http://localhost:8000`.

---

## Endpoints Disponíveis

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/relatorios` | Registrar resultado de ato cartorial |
| GET | `/api/v1/relatorios` | Listar logs com filtros |
| GET | `/api/v1/relatorios/{id}` | Detalhe de um log |
| GET | `/api/v1/dashboard/resumo` | Métricas gerenciais |

Documentação interativa (Swagger UI): `http://localhost:8000/docs`

---

## Painel Gerencial

Abra o arquivo `dashboard.html` diretamente no navegador com a API em execução 
para visualizar os KPIs, gráficos de distribuição por tipo de ato e a tabela 
de erros recentes de integração.

---

## Simulador de Dados

O script `simulador.py` foi utilizado na etapa de coleta de dados da pesquisa. 
Ele injeta 100 requisições em lote, alternando entre 7 cartórios e 7 tipos de 
ato, simulando notificações de resultado com distribuição aproximada de 70% de sucesso
e 30% de erro, refletindo uma taxa operacional realista.

```bash
python simulador.py
```

---

## Autor

**William Meireles**  
MBA em Engenharia de Software — USP/Esalq
