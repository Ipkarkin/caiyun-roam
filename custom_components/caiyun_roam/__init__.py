"""Caiyun Roam — Caiyun (彩云) weather that follows a tracked device's GPS."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE,
    CONF_PRESENCE,
    CONF_TRACKER,
    DEFAULT_INTERVAL,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.WEATHER]


class CaiyunRoamCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll Caiyun at the tracker's current coordinates."""

    def __init__(
        self,
        hass: HomeAssistant,
        session,
        api_key: str,
        tracker: str,
        interval: int,
        presence_entity: str | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=max(1, interval)),
        )
        self.session = session
        self.api_key = api_key
        self.tracker = tracker
        self.presence_entity = presence_entity
        self._last_lat: float | None = None
        self._last_lon: float | None = None
        self._last_queried: tuple[float, float] | None = None

    def _current_coords(self) -> tuple[float, float]:
        """Prefer the tracker's GPS; fall back to HA home coordinates."""
        state = self.hass.states.get(self.tracker)
        attrs = state.attributes if state else {}
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")
        if lat is None or lon is None:
            lat, lon = self._last_lat, self._last_lon
        else:
            self._last_lat, self._last_lon = lat, lon
        if lat is None or lon is None:
            lat = self.hass.config.latitude
            lon = self.hass.config.longitude
        return float(lat), float(lon)

    async def _async_update_data(self) -> dict[str, Any]:
        lat, lon = self._current_coords()

        # Quota guard: skip the API call when nothing can change.
        # 1) Person is home -> the home-coordinates integration already covers it.
        # 2) Coordinates unchanged since the last successful query -> same weather.
        if self.data:
            presence = (
                self.hass.states.get(self.presence_entity) if self.presence_entity else None
            )
            if presence and presence.state == "on":
                _LOGGER.debug("At home per %s, skipping Caiyun call", self.presence_entity)
                return self.data
            if self._last_queried == (lat, lon):
                _LOGGER.debug("Coordinates unchanged, skipping Caiyun call")
                return self.data

        url = (
            f"{API_BASE}/{self.api_key}/{lon:.4f},{lat:.4f}/weather.json"
            "?alert=true&dailysteps=3&hourlysteps=12"
        )
        try:
            async with self.session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"Caiyun HTTP {resp.status}")
                data = await resp.json(content_type=None)
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Caiyun request failed: {err}") from err
        if data.get("status") != "ok":
            raise UpdateFailed(f"Caiyun status: {data.get('status')}")
        self._last_queried = (lat, lon)
        result = data.get("result") or {}
        result["_coords"] = {"latitude": lat, "longitude": lon}
        return result


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Caiyun Roam from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    api_key = entry.options.get(CONF_API_KEY) or entry.data[CONF_API_KEY]
    tracker = entry.options.get(CONF_TRACKER) or entry.data[CONF_TRACKER]
    interval = int(
        entry.options.get("interval")
        or entry.data.get("interval")
        or DEFAULT_INTERVAL
    )
    presence = (
        entry.options.get(CONF_PRESENCE)
        or entry.data.get(CONF_PRESENCE)
        or None
    )
    coordinator = CaiyunRoamCoordinator(
        hass, async_get_clientsession(hass), api_key, tracker, interval, presence
    )
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(_update_listener))
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "name": entry.data.get(CONF_NAME, DEFAULT_NAME),
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


@callback
def _fallback_coords(hass: HomeAssistant) -> dict[str, float]:
    return {CONF_LATITUDE: hass.config.latitude, CONF_LONGITUDE: hass.config.longitude}
