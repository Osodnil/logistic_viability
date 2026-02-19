from cd_viabilidade.financials import FinancialSummary
from cd_viabilidade.reporting import write_markdown_report


def test_write_markdown_report(tmp_path):
    summary = FinancialSummary(100, 40, 20, 40)
    path = write_markdown_report(tmp_path / "report.md", ["F1"], summary, 60)
    assert path.exists()
