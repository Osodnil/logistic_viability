"""Geração de mapas para visualização de pontos logísticos."""

from pathlib import Path

import folium
import pandas as pd

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


def build_map(facilities: pd.DataFrame, clients: pd.DataFrame, output_html: Path) -> Path:
    """Cria um mapa com instalações e clientes."""
    center = [clients["lat"].mean(), clients["lon"].mean()]
    fmap = folium.Map(location=center, zoom_start=5)

    for row in facilities.itertuples():
        folium.Marker([row.lat, row.lon], tooltip=f"Facility {row.facility_id}", icon=folium.Icon(color="blue")).add_to(fmap)

    for row in clients.itertuples():
        folium.CircleMarker([row.lat, row.lon], radius=4, tooltip=f"Client {row.client_id}", color="green").add_to(fmap)

    output_html.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(output_html))
    logger.info("Mapa salvo em %s", output_html)
    return output_html
