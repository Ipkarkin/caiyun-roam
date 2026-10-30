"""Weather entity for Caiyun Roam."""

from __future__ import annotations

from typing import Any

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, SKYCON_MAP

PARALLEL_UPDATES = 0


def _num(data: dict, *keys: str, default=None):
    """Safely fetch a numeric value from a nested dict."""
    cur: Any = data
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if isinstance(cur, (int, float)) else default


def _pct(value) -> float | None:
    """Caiyun returns humidity/cloudrate as 0~1 fractions."""
    if not isinstance(value, (int, float)):
        return None
    return round(value * 100, 1) if 0 < value <= 1 else round(value, 1)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CaiyunRoamWeather(data["coordinator"], data["name"], entry)])


class CaiyunRoamWeather(CoordinatorEntity, WeatherEntity):
    """Weather at the tracked device's location."""

    _attr_attribution = ATTRIBUTION
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_precipitation_unit = UnitOfLength.MILLIMETERS
    _attr_supported_features = 0

    def __init__(self, coordinator, name: str, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}"

    @property
    def _result(self) -> dict:
        return (self.coordinator.data or {}) if self.coordinator else {}

    @property
    def _realtime(self) -> dict:
        return self._result.get("realtime") or {}

    @property
    def condition(self) -> str | None:
        skycon = self._realtime.get("skycon")
        if skycon:
            return SKYCON_MAP.get(skycon, "cloudy")
        return SKYCON_MAP.get(self._result.get("skycon"), None)

    @property
    def native_temperature(self) -> float | None:
        return _num(self._realtime, "temperature")

    @property
    def native_apparent_temperature(self) -> float | None:
        return _num(self._realtime, "apparent_temperature")

    @property
    def humidity(self) -> float | None:
        return _pct(_num(self._realtime, "humidity"))

    @property
    def native_pressure(self) -> float | None:
        # v2.5 returns Pa; convert to hPa when needed
        p = _num(self._realtime, "pressure")
        if p is None:
            return None
        return round(p / 100, 2) if p > 2000 else round(p, 2)

    @property
    def wind_bearing(self) -> float | None:
        return _num(self._realtime, "wind", "direction")

    @property
    def native_wind_speed(self) -> float | None:
        return _num(self._realtime, "wind", "speed")

    @property
    def native_visibility(self) -> float | None:
        return _num(self._realtime, "visibility")

    @property
    def cloud_coverage(self) -> float | None:
        return _pct(_num(self._realtime, "cloudrate"))

    @property
    def uv_index(self) -> float | None:
        return _num(self._realtime, "ultraviolet", "index") or _num(
            self._realtime, "uv_index"
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        r = self._result
        rt = self._realtime
        minutely = r.get("minutely") or {}
        aq = rt.get("air_quality") or {}
        aqi = aq.get("aqi") or {}
        prob = minutely.get("probability") or []
        probability = [round(float(x) * 100, 1) if 0 < x <= 1 else float(x)
                       for x in prob if isinstance(x, (int, float))]
        alert = r.get("alert") or {}
        coords = r.get("_coords") or {}
        return {
            "forecast_keypoint": r.get("forecast_keypoint") or "",
            "forecast_minutely": minutely.get("description") or "",
            "forecast_probability": probability,
            "forecast_alert": alert,
            "skycon": rt.get("skycon"),
            "apparent_temperature": _num(rt, "apparent_temperature"),
            "pm25": _num(aq, "pm25"),
            "pm10": _num(aq, "pm10"),
            "o3": _num(aq, "o3"),
            "no2": _num(aq, "no2"),
            "so2": _num(aq, "so2"),
            "co": _num(aq, "co"),
            "aqi": _num(aqi, "chn"),
            "aqi_description": (aq.get("description") or {}).get("chn"),
            "aqi_usa": _num(aqi, "usa"),
            "latitude": coords.get("latitude"),
            "longitude": coords.get("longitude"),
        }
