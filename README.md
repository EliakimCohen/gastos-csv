# Gastos CSV

Analisador de despesas pelo terminal. Lê um CSV, valida os registros e gera totais por categoria, com filtro mensal e exportação JSON.

**Python 3.12+ · CSV · Decimal · dataclasses · unittest · sem dependências externas**

## Execute

Dentro desta pasta:

```bash
python gastos.py examples/despesas.csv --mes 2026-11
python gastos.py examples/despesas.csv --mes 2026-11 --json relatorio.json
```

Resultado esperado:

```text
Despesas: 4 | Total: R$ 199.90
alimentação: R$ 110.00
educação: R$ 79.90
transporte: R$ 10.00
```

## Formato de entrada

CSV UTF-8, separado por `;`, com este cabeçalho exato:

```csv
data;categoria;descricao;valor
2026-11-01;Alimentação;Almoço;25,50
```

Datas usam `AAAA-MM-DD`; valores devem ser maiores que zero, com até 12 dígitos inteiros, sem separadores de milhares e com duas casas decimais. Aceita `25,50` e `25.50`. Categorias são normalizadas para minúsculas; o arquivo original é preservado. Estornos e receitas não fazem parte desta versão.

Se uma linha for inválida, o programa informa o número e termina com código 1 sem gerar um relatório parcial. Um arquivo apenas com cabeçalho gera total zero. O carregamento é em memória, adequado a arquivos pessoais pequenos.

## Testes

```bash
python -m unittest discover -s tests -v
```

Incluem centavos exatos, categorias, filtro de mês, datas inválidas, colunas ausentes, valores inválidos, JSON e proteção contra sobrescrever a entrada.

## Por que Decimal?

Valores monetários precisam preservar centavos. A conversão vai diretamente do texto para `Decimal`, sem passar por `float`. No JSON, totais são strings como `"199.90"` para manter a representação decimal.
