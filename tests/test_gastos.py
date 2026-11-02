import json
import tempfile
import unittest
from pathlib import Path

from gastos import main, read_expenses, summarize


class ExpenseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "input.csv"

    def write(self, rows):
        self.path.write_text("data;categoria;descricao;valor\n" + rows, encoding="utf-8")
        return self.path

    def test_decimal_totals_are_exact(self):
        self.write("2026-11-01;Comida;A;0,10\n2026-11-02;COMIDA;B;0.20\n")
        report = summarize(read_expenses(self.path))
        self.assertEqual(report["total"], "0.30")
        self.assertEqual(report["por_categoria"], {"comida": "0.30"})

    def test_filter_by_month(self):
        self.write("2026-10-31;A;B;10,00\n2026-11-01;A;B;20,00\n")
        report = summarize(read_expenses(self.path), "2026-11")
        self.assertEqual(report["quantidade"], 1)
        self.assertEqual(report["total"], "20.00")

    def test_invalid_values_have_line_number(self):
        for value in ["-1,00", "0,00", "NaN", "Infinity", "1.234,00", "1,234", "1e2", "abc", "1234567890123,00"]:
            self.write(f"2026-11-01;A;B;{value}\n")
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "Linha 2"):
                read_expenses(self.path)

    def test_invalid_date_empty_category_and_column_count(self):
        for row in ["2026-02-30;A;B;1,00", "20261101;A;B;1,00", "2026-11-01; ;B;1,00", "2026-11-01;A;B", "2026-11-01;A;B;1,00;extra"]:
            self.write(row + "\n")
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "Linha 2"):
                read_expenses(self.path)

    def test_header_only_is_valid_and_wrong_header_is_not(self):
        self.write("")
        self.assertEqual(summarize(read_expenses(self.path))["total"], "0.00")
        self.path.write_text("a;b;c;d\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Cabeçalho"):
            read_expenses(self.path)

    def test_invalid_month(self):
        for month in ["2026-13", "2026-1", "novembro"]:
            with self.subTest(month=month), self.assertRaises(ValueError):
                summarize([], month)

    def test_cli_writes_json_with_unicode(self):
        self.write("2026-11-01;Educação;Livro;49,90\n")
        target = Path(self.directory.name) / "report.json"
        self.assertEqual(main([str(self.path), "--json", str(target)]), 0)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["por_categoria"], {"educação": "49.90"})

    def test_cli_cannot_overwrite_source(self):
        self.write("2026-11-01;A;B;1,00\n")
        before = self.path.read_bytes()
        self.assertEqual(main([str(self.path), "--json", str(self.path)]), 1)
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
