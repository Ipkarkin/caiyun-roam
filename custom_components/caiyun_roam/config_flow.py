"""Config flow for Caiyun Roam (Caiyun weather that follows a tracker's GPS)."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import CONF_TRACKER, DEFAULT_INTERVAL, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_TRACKER): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["device_tracker", "person"])
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional("interval", default=DEFAULT_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=120)
        ),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_TRACKER): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["device_tracker", "person"])
        ),
        vol.Optional("interval", default=DEFAULT_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=120)
        ),
    }
)


async def _validate(hass: HomeAssistant, api_key: str) -> str | None:
    """Return an error key or None when the key works."""
    import aiohttp

    url = f"https://api.caiyunapp.com/v2.5/{api_key}/113.54,22.2707/weather.json"
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as resp:
                if resp.status == 429:
                    return "rate_limited"
                if resp.status != 200:
                    return "cannot_connect"
                data = await resp.json(content_type=None)
    except Exception:  # noqa: BLE001
        return "cannot_connect"
    if data.get("status") != "ok":
        return "invalid_auth"
    return None


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Caiyun Roam."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_TRACKER])
            self._abort_if_unique_id_configured()
            err = await _validate(self.hass, user_input[CONF_API_KEY])
            if err is None:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME), data=user_input
                )
            errors["base"] = err
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow: change API key / tracker / interval without re-adding."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            err = await _validate(self.hass, user_input[CONF_API_KEY])
            if err is None:
                return self.async_create_entry(title="", data=user_input)
            errors["base"] = err
        cur = self._entry.data
        schema = self.add_suggested_values_to_schema(
            OPTIONS_SCHEMA,
            {
                CONF_API_KEY: cur.get(CONF_API_KEY, ""),
                CONF_TRACKER: cur.get(CONF_TRACKER),
                "interval": self._entry.options.get(
                    "interval", cur.get("interval", DEFAULT_INTERVAL)
                ),
            },
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
