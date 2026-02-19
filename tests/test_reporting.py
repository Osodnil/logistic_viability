from cd_viabilidade.financials import FinancialIndicators, FinancialSummary
from cd_viabilidade.reporting import generate_executive_report, write_markdown_report


def test_write_markdown_report(tmp_path):
    summary = FinancialSummary(100, 40, 20, 40)
    path = write_markdown_report(tmp_path / "report.md", ["F1"], summary, 60)
    assert path.exists()


def test_generate_executive_report(tmp_path):
    scenario_costs = {"base": 1000.0, "1_novo_cd": 900.0, "2_novos_cds": 850.0}
    scenario_indicators = {
        "base": FinancialIndicators(npv=30, payback_simple=3.0, payback_discounted=3.4, roi=0.1),
        "1_novo_cd": FinancialIndicators(npv=80, payback_simple=2.5, payback_discounted=2.8, roi=0.2),
        "2_novos_cds": FinancialIndicators(npv=70, payback_simple=2.4, payback_discounted=2.7, roi=0.18),
    }
    path = generate_executive_report(scenario_costs=scenario_costs, scenario_indicators=scenario_indicators, output_dir=tmp_path)
    assert path.exists()
    assert "Recomendação acionável" in path.read_text(encoding="utf-8")
