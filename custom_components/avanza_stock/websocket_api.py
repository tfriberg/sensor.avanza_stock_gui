"""WebSocket API for Avanza Stock."""
from __future__ import annotations

import logging
from typing import Any, Callable

import pyavanza
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, INSTRUMENT_TYPES

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup(hass: HomeAssistant) -> None:
    """Set up the Avanza Stock WebSocket API."""
    websocket_api.async_register_command(hass, websocket_search_instruments)


@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/search",
        vol.Required("search_term"): str,
        vol.Optional("instrument_type", default="all"): str,
    }
)
async def websocket_search_instruments(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle search for instruments."""
    search_term = msg["search_term"]
    instrument_type = msg["instrument_type"]

    try:
        session = async_get_clientsession(hass)
        results = await pyavanza.search(
            session, 
            search_term,
            INSTRUMENT_TYPES.get(instrument_type, "Alla")
        )
        connection.send_result(
            msg["id"],
            [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "currency": item.get("currency", ""),
                }
                for item in results
            ],
        )
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error searching instruments: %s", err)
        connection.send_error(
            msg["id"], "search_failed", "Failed to search for instruments"
        )
