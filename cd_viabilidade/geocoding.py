"""Funções auxiliares de geocodificação."""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    from geopy.exc import GeocoderTimedOut
    from geopy.geocoders import Nominatim
except ModuleNotFoundError:  # pragma: no cover - fallback para ambientes sem geopy
    class GeocoderTimedOut(Exception):
        """Fallback local para timeout de geocodificação."""

    Nominatim = None

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


@dataclass(frozen=True)
class Coordinate:
    """Representa uma coordenada geográfica."""

    lat: float
    lon: float


@dataclass(frozen=True)
class GeocodeResult:
    """Resultado de uma geocodificação para cidade/UF."""

    cidade: str
    uf: str
    lat: float | None
    lon: float | None
    found: bool
    warning: str | None = None
    source: str = "api"


class GeocodingClient:
    """Cliente de geocodificação com cache local e retries para timeout."""

    def __init__(
        self,
        user_agent: str = "cd-viabilidade",
        cache_path: str | Path = "data/geocode_cache.json",
        timeout: int = 10,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
        sleep_fn: Callable[[float], None] = time.sleep,
        geocoder: Nominatim | None = None,
    ) -> None:
        self.cache_path = Path(cache_path)
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.sleep_fn = sleep_fn
        if geocoder is not None:
            self.geocoder = geocoder
        elif Nominatim is not None:
            self.geocoder = Nominatim(user_agent=user_agent, timeout=timeout)
        else:
            raise RuntimeError("geopy não está instalado e nenhum geocoder foi injetado")
        self._cache = self._load_cache()

    def geocode_city_uf(self, cidade: str, uf: str) -> GeocodeResult:
        """Geocodifica no formato `cidade + uf + Brasil` com fallback resiliente."""
        cache_key = self._cache_key(cidade, uf)
        query = f"{cidade}, {uf}, Brasil"

        if cache_key in self._cache:
            cached_result = self._dict_to_result(self._cache[cache_key], source="cache")
            logger.info("Cache hit para '%s': %s", query, cached_result)
            return cached_result

        for attempt in range(1, self.max_retries + 1):
            try:
                location = self.geocoder.geocode(query)
                if location is None:
                    warning = (
                        f"Não foi possível encontrar coordenada para '{query}'. "
                        "Registro marcado e pipeline seguirá com aviso."
                    )
                    result = GeocodeResult(
                        cidade=cidade,
                        uf=uf,
                        lat=None,
                        lon=None,
                        found=False,
                        warning=warning,
                    )
                    logger.warning(warning)
                else:
                    result = GeocodeResult(
                        cidade=cidade,
                        uf=uf,
                        lat=float(location.latitude),
                        lon=float(location.longitude),
                        found=True,
                    )
                    logger.info("Geocodificação bem sucedida para '%s': %s", query, result)

                self._cache[cache_key] = self._result_to_dict(result)
                self._save_cache()
                return result
            except GeocoderTimedOut:
                logger.warning(
                    "Timeout ao geocodificar '%s' (tentativa %s/%s)",
                    query,
                    attempt,
                    self.max_retries,
                )
                if attempt == self.max_retries:
                    break
                wait_seconds = self.backoff_seconds * (2 ** (attempt - 1))
                self.sleep_fn(wait_seconds)

        warning = (
            f"Falha por timeout ao geocodificar '{query}' após {self.max_retries} tentativas. "
            "Registro marcado e pipeline seguirá com aviso."
        )
        result = GeocodeResult(
            cidade=cidade,
            uf=uf,
            lat=None,
            lon=None,
            found=False,
            warning=warning,
        )
        logger.error(warning)
        self._cache[cache_key] = self._result_to_dict(result)
        self._save_cache()
        return result

    def _cache_key(self, cidade: str, uf: str) -> str:
        return f"{cidade.strip().lower()}|{uf.strip().lower()}"

    def _load_cache(self) -> dict[str, dict[str, str | float | bool | None]]:
        if not self.cache_path.exists():
            return {}

        if self.cache_path.suffix.lower() == ".json":
            with self.cache_path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
            return data if isinstance(data, dict) else {}

        if self.cache_path.suffix.lower() == ".csv":
            cache: dict[str, dict[str, str | float | bool | None]] = {}
            with self.cache_path.open("r", encoding="utf-8", newline="") as fp:
                reader = csv.DictReader(fp)
                for row in reader:
                    if not row.get("cache_key"):
                        continue
                    cache[row["cache_key"]] = {
                        "cidade": row.get("cidade", ""),
                        "uf": row.get("uf", ""),
                        "lat": float(row["lat"]) if row.get("lat") else None,
                        "lon": float(row["lon"]) if row.get("lon") else None,
                        "found": row.get("found") == "True",
                        "warning": row.get("warning") or None,
                    }
            return cache

        raise ValueError("cache_path deve usar extensão .json ou .csv")

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        if self.cache_path.suffix.lower() == ".json":
            with self.cache_path.open("w", encoding="utf-8") as fp:
                json.dump(self._cache, fp, ensure_ascii=False, indent=2)
            return

        if self.cache_path.suffix.lower() == ".csv":
            fieldnames = ["cache_key", "cidade", "uf", "lat", "lon", "found", "warning"]
            with self.cache_path.open("w", encoding="utf-8", newline="") as fp:
                writer = csv.DictWriter(fp, fieldnames=fieldnames)
                writer.writeheader()
                for key, value in self._cache.items():
                    writer.writerow({"cache_key": key, **value})
            return

        raise ValueError("cache_path deve usar extensão .json ou .csv")

    def _dict_to_result(self, value: dict[str, str | float | bool | None], source: str) -> GeocodeResult:
        return GeocodeResult(
            cidade=str(value.get("cidade", "")),
            uf=str(value.get("uf", "")),
            lat=float(value["lat"]) if value.get("lat") is not None else None,
            lon=float(value["lon"]) if value.get("lon") is not None else None,
            found=bool(value.get("found", False)),
            warning=str(value["warning"]) if value.get("warning") else None,
            source=source,
        )

    def _result_to_dict(self, result: GeocodeResult) -> dict[str, str | float | bool | None]:
        return {
            "cidade": result.cidade,
            "uf": result.uf,
            "lat": result.lat,
            "lon": result.lon,
            "found": result.found,
            "warning": result.warning,
        }
