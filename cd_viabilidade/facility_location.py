"""Modelo de localização de instalações com otimização linear."""

from typing import Dict, List, Tuple

import pandas as pd
import pulp

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


def solve_facility_location(
    cost_matrix: pd.DataFrame,
    fixed_costs: pd.DataFrame,
    max_facilities: int,
) -> Tuple[List[str], pd.DataFrame, float]:
    """Resolve problema de localização de facilidades com atribuição única por cliente."""
    facilities = fixed_costs["facility_id"].tolist()
    clients = sorted(cost_matrix["client_id"].unique().tolist())
    c = {(r.facility_id, r.client_id): r.unit_cost for r in cost_matrix.itertuples()}
    f = dict(zip(fixed_costs["facility_id"], fixed_costs["fixed_cost"]))

    model = pulp.LpProblem("facility_location", pulp.LpMinimize)
    open_var = pulp.LpVariable.dicts("open", facilities, 0, 1, pulp.LpBinary)
    assign_var = pulp.LpVariable.dicts("assign", (facilities, clients), 0, 1, pulp.LpBinary)

    model += (
        pulp.lpSum(f[fac] * open_var[fac] for fac in facilities)
        + pulp.lpSum(c[(fac, cli)] * assign_var[fac][cli] for fac in facilities for cli in clients)
    )

    for cli in clients:
        model += pulp.lpSum(assign_var[fac][cli] for fac in facilities) == 1

    for fac in facilities:
        for cli in clients:
            model += assign_var[fac][cli] <= open_var[fac]

    model += pulp.lpSum(open_var[fac] for fac in facilities) <= max_facilities

    model.solve(pulp.PULP_CBC_CMD(msg=False))

    selected = [fac for fac in facilities if pulp.value(open_var[fac]) > 0.5]
    assignments = []
    for fac in facilities:
        for cli in clients:
            if pulp.value(assign_var[fac][cli]) > 0.5:
                assignments.append({"facility_id": fac, "client_id": cli})

    total_cost = float(pulp.value(model.objective))
    logger.info("Otimização concluída com %d instalações abertas", len(selected))
    return selected, pd.DataFrame(assignments), total_cost
