"""Funções auxiliares de geocodificação."""

from dataclasses import dataclass
from hashlib import md5

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


@dataclass(frozen=True)
class Coordinate:
    """Representa uma coordenada geográfica."""

    lat: float
    lon: float


def deterministic_geocode(address: str) -> Coordinate:
    """Gera coordenada determinística para endereço (modo toy/offline)."""
    digest = md5(address.encode("utf-8")).hexdigest()
    lat = -34.0 + (int(digest[:6], 16) / 0xFFFFFF) * 39.0
    lon = -74.0 + (int(digest[6:12], 16) / 0xFFFFFF) * 40.0
    coord = Coordinate(lat=round(lat, 6), lon=round(lon, 6))
    logger.info("Endereço '%s' geocodificado para %s", address, coord)
    return coord
