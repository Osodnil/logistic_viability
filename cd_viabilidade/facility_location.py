"""Modelo de localização de instalações com otimização linear inteira mista (MILP)."""

from dataclasses import dataclass
from typing import Dict, Iterable, List

import pandas as pd
import pulp

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


@dataclass(frozen=True)
class SolutionResult:
    """Resultado tipado da otimização de localização de CDs."""

    open_facilities: List[str]
    total_cost: float
    fixed_cost: float
    variable_cost: float
    allocation: Dict[str, str]


def solve_facility_location(
    cost_matrix: pd.DataFrame,
    fixed_costs: pd.DataFrame,
    max_new_facilities: int | None = None,
    capacity_by_facility: Dict[str, float] | None = None,
    demand_by_client: Dict[str, float] | None = None,
    forced_open_facilities: Iterable[str] | None = None,
    candidate_facilities: Iterable[str] | None = None,
    min_total_open_facilities: int | None = None,
 ) -> SolutionResult:
     """Resolve o problema de localização de instalações com atribuição única por demanda.
+
+    # Normaliza/valida interseção entre instalações forçadas abertas e candidatas
+    if forced_open_facilities is not None and candidate_facilities is not None:
+        forced_open_set = set(forced_open_facilities)
+        candidate_set = set(candidate_facilities)
+        intersection = forced_open_set & candidate_set
+
+        if intersection:
+            # Se o número máximo de novas instalações for menor que a interseção,
+            # o modelo ficaria inviável pela combinação das restrições.
+            if max_new_facilities is not None and len(intersection) > max_new_facilities:
+                raise ValueError(
+                    "Configuração inválida: existem instalações em comum entre "
+                    "`forced_open_facilities` e `candidate_facilities` cujo número "
+                    "excede `max_new_facilities`, o que tornaria o problema inviável. "
+                    f"Instalações em conflito: {sorted(intersection)}"
+                )
+
+            # Remove as instalações já forçadas abertas do conjunto de candidatas
+            candidate_facilities = [f for f in candidate_facilities if f not in forced_open_set]

    Espera as colunas:
    - ``cost_matrix``: ``facility_id``, ``client_id``, ``unit_cost`` ou ``freight_cost``.
    - ``fixed_costs``: ``facility_id``, ``fixed_cost``.
    """
    facilities = fixed_costs["facility_id"].astype(str).tolist()
    clients = sorted(cost_matrix["client_id"].astype(str).unique().tolist())

    cost_column = "unit_cost" if "unit_cost" in cost_matrix.columns else "freight_cost"
    variable_cost = {
        (str(row.facility_id), str(row.client_id)): float(getattr(row, cost_column))
        for row in cost_matrix.dropna(subset=[cost_column]).itertuples(index=False)
    }
    fixed_cost = {
        str(row.facility_id): float(row.fixed_cost)
        for row in fixed_costs.itertuples(index=False)
    }

    forced_open = {str(f) for f in (forced_open_facilities or [])}
    unknown_forced = sorted(forced_open - set(facilities))
    if unknown_forced:
        raise ValueError(f"Facilities forçadas ausentes em fixed_costs: {unknown_forced}")

    if candidate_facilities is None:
        candidate_set = set(facilities) - forced_open
    else:
        candidate_set = {str(f) for f in candidate_facilities}
        unknown_candidates = sorted(candidate_set - set(facilities))
        if unknown_candidates:
            raise ValueError(f"Facilities candidatas ausentes em fixed_costs: {unknown_candidates}")

    if "demanda" in cost_matrix.columns:
        inferred_demand = (
            cost_matrix[["client_id", "demanda"]]
            .drop_duplicates(subset=["client_id"])
            .set_index("client_id")["demanda"]
            .astype(float)
            .to_dict()
        )
    else:
        inferred_demand = {}

    client_demand = {client: float(inferred_demand.get(client, 1.0)) for client in clients}
    if demand_by_client is not None:
        client_demand.update({str(k): float(v) for k, v in demand_by_client.items()})

    model = pulp.LpProblem("facility_location", pulp.LpMinimize)

    y = pulp.LpVariable.dicts("y", facilities, 0, 1, pulp.LpBinary)
    x = pulp.LpVariable.dicts("x", (clients, facilities), 0, 1, pulp.LpBinary)

    for client in clients:
        for facility in facilities:
            if (facility, client) not in variable_cost:
                raise ValueError(f"Custo ausente para facility_id={facility}, client_id={client}")

    model += (
        pulp.lpSum(variable_cost[(facility, client)] * x[client][facility] for client in clients for facility in facilities)
        + pulp.lpSum(fixed_cost[facility] * y[facility] for facility in facilities)
    )

    for client in clients:
        model += pulp.lpSum(x[client][facility] for facility in facilities) == 1

    for client in clients:
        for facility in facilities:
            model += x[client][facility] <= y[facility]

    for facility in forced_open:
        model += y[facility] == 1

    if capacity_by_facility is not None:
        for facility in facilities:
            capacity = float(capacity_by_facility[facility])
            model += (
                pulp.lpSum(client_demand[client] * x[client][facility] for client in clients)
                <= capacity
            )

    if max_new_facilities is not None:
        model += pulp.lpSum(y[facility] for facility in candidate_set) <= max_new_facilities

    if min_total_open_facilities is not None:
        model += pulp.lpSum(y[facility] for facility in facilities) >= int(min_total_open_facilities)

    status = model.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"Solver não encontrou solução ótima. Status: {pulp.LpStatus[status]}")

    open_facilities = [facility for facility in facilities if pulp.value(y[facility]) > 0.5]
    allocation = {
        client: facility
        for client in clients
        for facility in facilities
        if pulp.value(x[client][facility]) > 0.5
    }

    total_cost = float(pulp.value(model.objective))
    total_fixed_cost = float(sum(fixed_cost[facility] for facility in open_facilities))
    total_variable_cost = float(
        sum(variable_cost[(facility, client)] for client, facility in allocation.items())
    )

    logger.info("Otimização concluída com %d instalações abertas", len(open_facilities))
    return SolutionResult(
        open_facilities=open_facilities,
        total_cost=total_cost,
        fixed_cost=total_fixed_cost,
        variable_cost=total_variable_cost,
        allocation=allocation,
    )
