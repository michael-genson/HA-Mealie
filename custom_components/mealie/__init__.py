"""Custom integration to integrate Mealie with Home Assistant.

For more details about this integration, please refer to
https://github.com/andrew-codechimp/HA-Mealie
"""

from __future__ import annotations

from awesomeversion.awesomeversion import AwesomeVersion

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.const import __version__ as HA_VERSION  # noqa: N812

from homeassistant.const import (
    CONF_HOST,
    CONF_TOKEN,
)

from .const import (
    DOMAIN,
    LOGGER,
    MIN_HA_VERSION,
    DOMAIN_CONFIG,
    COORDINATOR,
    CONF_GROUP_ID,
    CONF_BREAKFAST_START,
    CONF_BREAKFAST_END,
    CONF_LUNCH_START,
    CONF_LUNCH_END,
    CONF_DINNER_START,
    CONF_DINNER_END,
)

from .api import MealieApiClient
from .coordinator import MealieDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.TODO,
    Platform.CALENDAR,
    Platform.SENSOR,
    Platform.IMAGE,
]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            vol.Schema(
                {
                    vol.Optional(CONF_BREAKFAST_START, default="07:00"): cv.string,
                    vol.Optional(CONF_BREAKFAST_END, default="11:00"): cv.string,
                    vol.Optional(CONF_LUNCH_START, default="11:30"): cv.string,
                    vol.Optional(CONF_LUNCH_END, default="14:00"): cv.string,
                    vol.Optional(CONF_DINNER_START, default="16:00"): cv.string,
                    vol.Optional(CONF_DINNER_END, default="21:00"): cv.string,
                },
            ),
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(
    hass: HomeAssistant,  # pylint: disable=unused-argument
    config: ConfigType,  # pylint: disable=unused-argument
) -> bool:
    """Integration setup."""

    if AwesomeVersion(HA_VERSION) < AwesomeVersion(MIN_HA_VERSION):  # pragma: no cover
        msg = (
            "This integration requires at least HomeAssistant version "
            f" {MIN_HA_VERSION}, you are running version {HA_VERSION}."
            " Please upgrade HomeAssistant to continue use this integration."
        )
        LOGGER.critical(msg)
        return False

    domain_config: ConfigType = config.get(DOMAIN) or {
        CONF_BREAKFAST_START: "07:00",
        CONF_BREAKFAST_END: "11:00",
        CONF_LUNCH_START: "11:30",
        CONF_LUNCH_END: "14:00",
        CONF_DINNER_START: "16:00",
        CONF_DINNER_END: "21:00",
    }

    hass.data[DOMAIN] = {
        DOMAIN_CONFIG: domain_config,
    }

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""

    session = async_get_clientsession(hass)

    if CONF_HOST not in entry.data or CONF_TOKEN not in entry.data:
        raise ConfigEntryAuthFailed("Unable to login, please re-login.") from None

    if entry.data[CONF_HOST] == "" or entry.data[CONF_TOKEN] == "":
        raise ConfigEntryAuthFailed("Unable to login, please re-login.") from None

    api = MealieApiClient(
        host=entry.data[CONF_HOST],
        token=entry.data[CONF_TOKEN],
        session=session,
    )

    hass.data[DOMAIN][COORDINATOR] = coordinator = MealieDataUpdateCoordinator(
        hass=hass, api=api, group_id=entry.data[CONF_GROUP_ID]
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


@callback
async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
