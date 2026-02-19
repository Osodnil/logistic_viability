# Logistic Viability

Projeto de referência para estudo de viabilidade logística de Centros de Distribuição (CDs), com pipeline analítico, API FastAPI e geração de mapas/relatórios.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Datasets esperados

No diretório `data/`:

- `clients.csv`: `client_id, city, demand|demanda, lat, lon`
- `facilities.csv`: `facility_id, name, city, uf, lat, lon, ocupacao, capacidade_m2`
- `fixed_costs.csv`: `facility_id, fixed_cost` (**opcional se usar estimativa automática**)
- `regional_costs.csv` (opcional, usado para calcular custo fixo automaticamente):
  - `uf, labor_cost_index, real_estate_cost_m2, tax_factor, transport_factor`

### Estimativa automática de custos fixos

Se `fixed_costs.csv` **não existir**, o pipeline passa a estimar os custos fixos por CD a partir de:

- índice de mão de obra regional;
- custo imobiliário regional por m²;
- fator tributário por UF;
- fator de transporte (proxy de custo inbound);
- ocupação/capacidade da instalação.

Resultado salvo em: `outputs/fixed_costs_estimados.csv`.

## CLI

Comandos principais:

```bash
python -m cd_viabilidade.cli run-pipeline --scenario base
python -m cd_viabilidade.cli run-scenarios
python -m cd_viabilidade.cli generate-report
python -m cd_viabilidade.cli serve-api
```

Parâmetros globais opcionais:

- `--data-dir`
- `--output-dir`
- `--facility-limit`
- `--unit-revenue`

### O que cada comando faz

- `run-pipeline --scenario <nome>`: executa cenário único e salva:
  - `outputs/assignments_<cenario>.csv`
  - `outputs/relatorio_<cenario>.md`
  - `outputs/mapa_<cenario>.html`
- `run-scenarios`: roda lote de cenários e salva `outputs/comparativo_cenarios.csv`.
- `generate-report`: gera `outputs/relatorio_executivo.md` comparando `base`, `1_novo_cd` e `2_novos_cds`.
- `serve-api`: imprime comando `uvicorn` para subir a API.

## API FastAPI

Suba a API com:

```bash
uvicorn cd_viabilidade.api:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints:

- `GET /health`
- `POST /optimize`
- `GET /report`

Exemplo de chamada para `/optimize`:

```bash
curl -X POST "http://localhost:8000/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "stress_tributario",
    "crescimento_demanda": 0.1,
    "fator_tributario": 0.05,
    "fator_salarial": 1.1,
    "limite_novos_cds": 2
  }'
```

## Testes com pytest

```bash
pytest
```

## Execução ponta a ponta

```bash
python -m cd_viabilidade.cli run-pipeline --scenario base
python -m cd_viabilidade.cli run-pipeline --scenario 1_novo_cd
python -m cd_viabilidade.cli run-pipeline --scenario 2_novos_cds
python -m cd_viabilidade.cli generate-report
```

Também é possível rodar o notebook:

- `notebooks/demo_viabilidade.ipynb`

Ele executa o fluxo completo e salva artefatos em `outputs/`.
