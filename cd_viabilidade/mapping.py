"""Geração de mapas para visualização de pontos logísticos."""

from pathlib import Path

import folium
import pandas as pd

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


def _row_value(row: pd.Series, primary: str, fallback: str | None = None) -> str:
    if primary in row and pd.notna(row[primary]):
        return str(row[primary])
    if fallback and fallback in row and pd.notna(row[fallback]):
        return str(row[fallback])
    return "N/A"


def build_map(
    facilities: pd.DataFrame,
    clients: pd.DataFrame,
    output_html: Path,
    selected_facilities: list[str] | None = None,
    assignments: pd.DataFrame | None = None,
) -> Path:
    """Cria mapa com demanda, candidatos, CDs selecionados e linhas de atendimento."""
    selected = set(selected_facilities or [])
    center = [clients["lat"].mean(), clients["lon"].mean()]
    fmap = folium.Map(location=center, zoom_start=5)

    for _, row in facilities.iterrows():
        facility_id = _row_value(row, "facility_id", "id")
        is_selected = facility_id in selected
        folium.Marker(
            [row["lat"], row["lon"]],
            tooltip=f"Candidato {facility_id}",
            icon=folium.Icon(color="red" if is_selected else "blue", icon="home" if is_selected else "flag"),
        ).add_to(fmap)

    for _, row in clients.iterrows():
        client_id = _row_value(row, "client_id", "id")
        folium.CircleMarker(
            [row["lat"], row["lon"]],
            radius=4,
            tooltip=f"Demanda {client_id}",
            color="green",
            fill=True,
            fill_opacity=0.8,
        ).add_to(fmap)

    if assignments is not None and not assignments.empty:
        client_index = clients.set_index(clients.get("client_id", clients.get("id")))
        facility_index = facilities.set_index(facilities.get("facility_id", facilities.get("id")))
        for _, row in assignments.iterrows():
            client_id = str(row["client_id"])
            facility_id = str(row["facility_id"])
            if client_id not in client_index.index or facility_id not in facility_index.index:
                continue
            c = client_index.loc[client_id]
            f = facility_index.loc[facility_id]
            folium.PolyLine(
                [(c["lat"], c["lon"]), (f["lat"], f["lon"])],
                color="orange" if facility_id in selected else "gray",
                weight=2,
                opacity=0.7,
            ).add_to(fmap)

    output_html.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(output_html))
    logger.info("Mapa salvo em %s", output_html)
    return output_html
