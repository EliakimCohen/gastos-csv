"""Valida despesas CSV e gera resumos exatos com Decimal."""

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class Expense:
    day: date
    category: str
    description: str
    amount: Decimal


def read_expenses(path):
    expenses = []
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";", strict=True)
        expected = ["data", "categoria", "descricao", "valor"]
        if reader.fieldnames != expected:
            raise ValueError("Cabeçalho esperado: data;categoria;descricao;valor")
        for number, row in enumerate(reader, start=2):
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("quantidade de colunas incorreta")
                raw = row["valor"].strip()
                if not re.fullmatch(r"[0-9]{1,12}[.,][0-9]{2}", raw):
                    raise ValueError("valor deve ter até 12 dígitos inteiros, sem milhares e com duas casas decimais")
                amount = Decimal(raw.replace(",", "."))
                if amount <= 0:
                    raise ValueError("valor deve ser maior que zero")
                category, description = row["categoria"].strip(), row["descricao"].strip()
                if not category or not description:
                    raise ValueError("categoria e descrição são obrigatórias")
                if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", row["data"]):
                    raise ValueError("data deve usar AAAA-MM-DD")
                day = date.fromisoformat(row["data"])
                expenses.append(Expense(day, category.casefold(), description, amount))
            except ValueError as error:
                raise ValueError(f"Linha {number}: {error}") from error
    return expenses


def summarize(expenses, month=None):
    if month is not None:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", month):
            raise ValueError("Mês deve usar AAAA-MM.")
        date.fromisoformat(month + "-01")
    selected = [expense for expense in expenses if month is None or expense.day.isoformat().startswith(month)]
    totals = {}
    for expense in selected:
        totals[expense.category] = totals.get(expense.category, Decimal("0.00")) + expense.amount
    return {
        "mes": month,
        "quantidade": len(selected),
        "total": format(sum((item.amount for item in selected), Decimal("0.00")), ".2f"),
        "por_categoria": {key: format(totals[key], ".2f") for key in sorted(totals)},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arquivo", help="CSV UTF-8 separado por ponto e vírgula")
    parser.add_argument("--mes", help="Filtrar por AAAA-MM")
    parser.add_argument("--json", dest="output", help="Salvar relatório JSON")
    args = parser.parse_args(argv)
    try:
        report = summarize(read_expenses(args.arquivo), args.mes)
        if args.output:
            # Evita destruir o CSV de entrada por engano.
            target, source = Path(args.output), Path(args.arquivo)
            if target.resolve() == source.resolve() or (target.exists() and target.samefile(source)):
                raise ValueError("A saída deve ser diferente do CSV de entrada.")
            Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Despesas: {report['quantidade']} | Total: R$ {report['total']}")
        for category, total in report["por_categoria"].items():
            print(f"{category}: R$ {total}")
    except (ValueError, OSError, csv.Error) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
