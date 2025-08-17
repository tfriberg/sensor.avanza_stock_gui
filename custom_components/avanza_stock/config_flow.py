"""Config flow for Avanza Stock integration."""
from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol
import aiohttp
import pyavanza

from homeassistant import config_entries
from homeassistant.const import (
    CONF_CURRENCY,
    CONF_ID,
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
)
from homeassistant.core import callback, HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import yaml
from yaml.loader import SafeLoader

from .const import (
    CONF_CONVERSION_CURRENCY,
    CONF_INVERT_CONVERSION_CURRENCY,
    CONF_PURCHASE_DATE,
    CONF_PURCHASE_PRICE,
    CONF_SHARES,
    CONF_SHOW_TRENDING_ICON,
    CONF_STOCK,
    CONF_SEARCH,
    CONF_INSTRUMENT_TYPE,
    DEFAULT_NAME,
    DEFAULT_SHOW_TRENDING_ICON,
    DOMAIN,
    MONITORED_CONDITIONS,
    INSTRUMENT_TYPES,
    CURRENCY_MAP,
    REVERSE_CURRENCY_MAP,
    get_currency_config,
)

_LOGGER = logging.getLogger(__name__)


class AvanzaStockOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Avanza Stock integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_MONITORED_CONDITIONS,
                    default=self.config_entry.options.get(
                        CONF_MONITORED_CONDITIONS, list(MONITORED_CONDITIONS)
                    ),
                ): cv.multi_select(MONITORED_CONDITIONS),
                vol.Optional(
                    CONF_SHOW_TRENDING_ICON,
                    default=self.config_entry.options.get(
                        CONF_SHOW_TRENDING_ICON, DEFAULT_SHOW_TRENDING_ICON
                    ),
                ): cv.boolean,
            })
        )


class AvanzaStockConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Avanza Stock."""


    def __init__(self) -> None:
        """Initialize the config flow."""
        self._search_results = []
        super().__init__()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["migrate_yaml", "search_instrument", "manual_entry"]
        )

    async def async_step_migrate_yaml(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle migration from YAML."""
    # ...existing code...
        
        errors = {}
        existing_entries = []
        
        try:
            # Check main configuration.yaml
            config_path = self.hass.config.path("configuration.yaml")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                if config and "sensor" in config:
                    for sensor in config["sensor"]:
                        if isinstance(sensor, dict) and sensor.get("platform") == "avanza_stock":
                            existing_entries.append(sensor)

            # Check includes directory for additional configs
            includes_dir = self.hass.config.path("includes")
            if os.path.exists(includes_dir):
                for filename in os.listdir(includes_dir):
                    if filename.endswith(".yaml"):
                        file_path = os.path.join(includes_dir, filename)
                        try:
                            with open(file_path, "r") as f:
                                include_config = yaml.safe_load(f)
                            if include_config and "sensor" in include_config:
                                for sensor in include_config["sensor"]:
                                    if isinstance(sensor, dict) and sensor.get("platform") == "avanza_stock":
                                        existing_entries.append(sensor)
                        except yaml.YAMLError:
                            continue

            if not existing_entries:
                return self.async_abort(reason="no_existing_config")

            # Store found configurations for the confirmation step
            self._found_configs = []
            
            # Process and validate each entry
            for entry in existing_entries:
                if "stock" in entry:
                    stock_config = entry["stock"]
                    if isinstance(stock_config, int):
                        # Single stock configuration
                        self._found_configs.append({
                            CONF_ID: str(stock_config),
                            CONF_NAME: entry.get("name", f"{DEFAULT_NAME} {stock_config}"),
                            CONF_SHARES: entry.get("shares", 0),
                            CONF_PURCHASE_DATE: entry.get("purchase_date", ""),
                            CONF_PURCHASE_PRICE: entry.get("purchase_price", 0),
                            CONF_CURRENCY: entry.get("currency"),
                            CONF_CONVERSION_CURRENCY: entry.get("conversion_currency"),
                            CONF_INVERT_CONVERSION_CURRENCY: entry.get("invert_conversion_currency", False),
                            CONF_MONITORED_CONDITIONS: entry.get("monitored_conditions", list(MONITORED_CONDITIONS)),
                            CONF_SHOW_TRENDING_ICON: entry.get("show_trending_icon", DEFAULT_SHOW_TRENDING_ICON),
                        })
                    elif isinstance(stock_config, list):
                        # Multiple stocks configuration
                        for stock in stock_config:
                            if isinstance(stock, dict):
                                self._found_configs.append({
                                    CONF_ID: str(stock["id"]),
                                    CONF_NAME: stock.get("name", f"{DEFAULT_NAME} {stock['id']}"),
                                    CONF_SHARES: stock.get("shares", 0),
                                    CONF_PURCHASE_DATE: stock.get("purchase_date", ""),
                                    CONF_PURCHASE_PRICE: stock.get("purchase_price", 0),
                                    CONF_CURRENCY: stock.get("currency"),
                                    CONF_CONVERSION_CURRENCY: stock.get("conversion_currency"),
                                    CONF_INVERT_CONVERSION_CURRENCY: stock.get("invert_conversion_currency", False),
                                    CONF_MONITORED_CONDITIONS: entry.get("monitored_conditions", list(MONITORED_CONDITIONS)),
                                    CONF_SHOW_TRENDING_ICON: entry.get("show_trending_icon", DEFAULT_SHOW_TRENDING_ICON),
                                })

            # Move to confirmation step
            return await self.async_step_confirm_migration()

        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.exception("Error migrating YAML configuration: %s", ex)
            errors["base"] = "migration_error"

        # If we get here, something went wrong
        return self.async_show_form(
            step_id="migrate_yaml",
            errors=errors,
        )

    async def async_step_search_instrument(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the search step."""
        errors = {}
        
        if user_input is not None:
            if CONF_ID in user_input:  # User selected an instrument
                self._selected_instrument = next(
                    (item for item in self._search_results if str(item["id"]) == user_input[CONF_ID]),
                    None
                )
                if self._selected_instrument:
                    return await self.async_step_configure({
                        CONF_ID: self._selected_instrument["id"],
                        CONF_NAME: self._selected_instrument["name"]
                    })
            else:  # User entered a search term
                try:
                    session = async_get_clientsession(self.hass)
                    instrument_type = user_input.get(CONF_INSTRUMENT_TYPE, "all")
                    self._search_results = await pyavanza.search(
                        session,
                        user_input[CONF_SEARCH],
                        INSTRUMENT_TYPES.get(instrument_type, "Alla")
                    )
                except aiohttp.ClientError:
                    errors["base"] = "cannot_connect"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected error occurred")
                    errors["base"] = "unknown"

        instruments = {
            str(item["id"]): f"{item['name']} ({item['currency']})" 
            for item in self._search_results
        } if self._search_results else {}

        return self.async_show_form(
            step_id="search_instrument",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INSTRUMENT_TYPE, default="all"): vol.In(
                        {k: v for k, v in INSTRUMENT_TYPES.items()}
                    ),
                    vol.Required(CONF_ID): vol.In(instruments) if instruments else str,
                }
            ),
            errors=errors,
            description_placeholders={
                "instruments": ", ".join(instruments.values()) if instruments else "Type to search"
            }
        )

    async def async_step_select_instrument(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle instrument selection."""
        errors = {}

        if user_input is not None:
            selected = next(
                (item for item in self._search_results if str(item["id"]) == user_input[CONF_ID]),
                None,
            )
            if selected:
                return await self.async_step_configure({
                    CONF_ID: selected["id"],
                    CONF_NAME: selected["name"]
                })

        instrument_list = {
            str(item["id"]): f"{item['name']} ({item['currency']})" 
            for item in self._search_results
        }

        return self.async_show_form(
            step_id="select_instrument",
            data_schema=vol.Schema({
                vol.Required(CONF_ID): vol.In(instrument_list)
            }),
            errors=errors,
        )

    async def async_step_manual_entry(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual ID entry."""
        errors = {}

        if user_input is not None:
            try:
                session = self.hass.helpers.aiohttp_client.async_get_clientsession()
                # Validate the ID exists
                await session.get(
                    f"https://www.avanza.se/_mobile/market/stock/{user_input[CONF_ID]}"
                )
                return await self.async_step_configure(user_input)
                
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "invalid_stock_id"

        return self.async_show_form(
            step_id="manual_entry",
            data_schema=vol.Schema({
                vol.Required(CONF_ID): cv.string,
                vol.Optional(CONF_NAME): cv.string,
            }),
            errors=errors,
        )

    async def async_step_configure(
        self, instrument_info: dict[str, Any], user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure the selected instrument."""
        errors = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                # Get instrument details including currency
                stock_data = await pyavanza.get_stock_info(session, instrument_info[CONF_ID])
                # Get the currency and set the appropriate conversion if not SEK
                currency = stock_data.get("currency", "SEK")
                if currency != "SEK" and currency in CURRENCY_MAP:
                    instrument_info[CONF_CONVERSION_CURRENCY] = CURRENCY_MAP[currency]
                user_input.update(instrument_info)  # Merge instrument info with user input
                title = user_input.get(CONF_NAME, f"{DEFAULT_NAME} {instrument_info[CONF_ID]}")
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_NAME: title,
                        CONF_ID: instrument_info[CONF_ID],
                        CONF_SHARES: user_input.get(CONF_SHARES, 0),
                        CONF_PURCHASE_PRICE: user_input.get(CONF_PURCHASE_PRICE, 0),
                        CONF_PURCHASE_DATE: user_input.get(CONF_PURCHASE_DATE, ""),
                        CONF_CURRENCY: user_input.get(CONF_CURRENCY),
                        CONF_CONVERSION_CURRENCY: user_input.get(CONF_CONVERSION_CURRENCY),
                        CONF_INVERT_CONVERSION_CURRENCY: user_input.get(
                            CONF_INVERT_CONVERSION_CURRENCY, False
                        ),
                        CONF_MONITORED_CONDITIONS: user_input.get(
                            CONF_MONITORED_CONDITIONS, list(MONITORED_CONDITIONS)
                        ),
                        CONF_SHOW_TRENDING_ICON: user_input.get(
                            CONF_SHOW_TRENDING_ICON, DEFAULT_SHOW_TRENDING_ICON
                        ),
                    },
                )
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
                _LOGGER.error("Failed to connect to Avanza")
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"
                _LOGGER.exception("Unexpected error occurred")

        # Show the configuration form
        return self.async_show_form(
            step_id="configure",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME, default=instrument_info.get(CONF_NAME)): cv.string,
                    vol.Optional(CONF_SHARES, default=0): vol.Coerce(float),
                    vol.Optional(CONF_PURCHASE_PRICE, default=0): vol.Coerce(float),
                    vol.Optional(CONF_PURCHASE_DATE, default=""): cv.string,
                    vol.Optional(CONF_CURRENCY): cv.string,
                    vol.Optional(CONF_CONVERSION_CURRENCY): cv.string,
                    vol.Optional(CONF_INVERT_CONVERSION_CURRENCY, default=False): cv.boolean,
                    vol.Optional(
                        CONF_MONITORED_CONDITIONS,
                        default=list(MONITORED_CONDITIONS),
                    ): cv.multi_select(MONITORED_CONDITIONS),
                    vol.Optional(
                        CONF_SHOW_TRENDING_ICON,
                        default=DEFAULT_SHOW_TRENDING_ICON,
                    ): cv.boolean,
                }
            ),
            errors=errors,
        )

        user_input.update(instrument_info)  # Merge instrument info with user input
        title = user_input.get(CONF_NAME, f"{DEFAULT_NAME} {user_input[CONF_ID]}")
        
        return self.async_create_entry(
            title=title,
            data={
                CONF_NAME: title,
                CONF_ID: user_input[CONF_ID],
                CONF_SHARES: user_input.get(CONF_SHARES, 0),
                CONF_PURCHASE_PRICE: user_input.get(CONF_PURCHASE_PRICE, 0),
                CONF_PURCHASE_DATE: user_input.get(CONF_PURCHASE_DATE, ""),
                CONF_CURRENCY: user_input.get(CONF_CURRENCY),
                CONF_CONVERSION_CURRENCY: user_input.get(CONF_CONVERSION_CURRENCY),
                CONF_INVERT_CONVERSION_CURRENCY: user_input.get(
                    CONF_INVERT_CONVERSION_CURRENCY, False
                ),
                CONF_MONITORED_CONDITIONS: user_input.get(
                    CONF_MONITORED_CONDITIONS, list(MONITORED_CONDITIONS)
                ),
                CONF_SHOW_TRENDING_ICON: user_input.get(
                    CONF_SHOW_TRENDING_ICON, DEFAULT_SHOW_TRENDING_ICON
                ),
            },
        )

        if user_input is not None:
            # Validate stock ID exists by trying to fetch it
            try:
                session = self.hass.helpers.aiohttp_client.async_get_clientsession()
                await session.get(
                    f"https://www.avanza.se/_mobile/market/stock/{user_input[CONF_ID]}"
                )
                
                title = user_input.get(CONF_NAME, f"{DEFAULT_NAME} {user_input[CONF_ID]}")
                
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_NAME: title,
                        CONF_ID: user_input[CONF_ID],
                        CONF_SHARES: user_input.get(CONF_SHARES, 0),
                        CONF_PURCHASE_PRICE: user_input.get(CONF_PURCHASE_PRICE, 0),
                        CONF_PURCHASE_DATE: user_input.get(CONF_PURCHASE_DATE, ""),
                        CONF_CURRENCY: user_input.get(CONF_CURRENCY),
                        CONF_CONVERSION_CURRENCY: user_input.get(CONF_CONVERSION_CURRENCY),
                        CONF_INVERT_CONVERSION_CURRENCY: user_input.get(
                            CONF_INVERT_CONVERSION_CURRENCY, False
                        ),
                        CONF_MONITORED_CONDITIONS: user_input.get(
                            CONF_MONITORED_CONDITIONS, list(MONITORED_CONDITIONS)
                        ),
                        CONF_SHOW_TRENDING_ICON: user_input.get(
                            CONF_SHOW_TRENDING_ICON, DEFAULT_SHOW_TRENDING_ICON
                        ),
                    },
                )
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ID): cv.string,
                    vol.Optional(CONF_NAME): cv.string,
                    vol.Optional(CONF_SHARES, default=0): vol.Coerce(float),
                    vol.Optional(CONF_PURCHASE_PRICE, default=0): vol.Coerce(float),
                    vol.Optional(CONF_PURCHASE_DATE, default=""): cv.string,
                    vol.Optional(CONF_CURRENCY): cv.string,
                    vol.Optional(CONF_CONVERSION_CURRENCY): cv.string,
                    vol.Optional(CONF_INVERT_CONVERSION_CURRENCY, default=False): cv.boolean,
                    vol.Optional(
                        CONF_MONITORED_CONDITIONS,
                        default=list(MONITORED_CONDITIONS),
                    ): cv.multi_select(MONITORED_CONDITIONS),
                    vol.Optional(
                        CONF_SHOW_TRENDING_ICON, default=DEFAULT_SHOW_TRENDING_ICON
                    ): cv.boolean,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Handle import from YAML config."""
        return await self.async_step_user(user_input)


class AvanzaStockOptionsFlow(config_entries.OptionsFlow):
    """Handle Avanza Stock options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SHARES,
                        default=self.config_entry.options.get(
                            CONF_SHARES,
                            self.config_entry.data.get(CONF_SHARES, 0),
                        ),
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_PURCHASE_PRICE,
                        default=self.config_entry.options.get(
                            CONF_PURCHASE_PRICE,
                            self.config_entry.data.get(CONF_PURCHASE_PRICE, 0),
                        ),
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_PURCHASE_DATE,
                        default=self.config_entry.options.get(
                            CONF_PURCHASE_DATE,
                            self.config_entry.data.get(CONF_PURCHASE_DATE, ""),
                        ),
                    ): cv.string,
                    vol.Optional(
                        CONF_CURRENCY,
                        default=self.config_entry.options.get(
                            CONF_CURRENCY,
                            self.config_entry.data.get(CONF_CURRENCY),
                        ),
                    ): cv.string,
                    vol.Optional(
                        CONF_CONVERSION_CURRENCY,
                        default=self.config_entry.options.get(
                            CONF_CONVERSION_CURRENCY,
                            self.config_entry.data.get(CONF_CONVERSION_CURRENCY),
                        ),
                    ): cv.string,
                    vol.Optional(
                        CONF_INVERT_CONVERSION_CURRENCY,
                        default=self.config_entry.options.get(
                            CONF_INVERT_CONVERSION_CURRENCY,
                            self.config_entry.data.get(CONF_INVERT_CONVERSION_CURRENCY, False),
                        ),
                    ): cv.boolean,
                    vol.Optional(
                        CONF_MONITORED_CONDITIONS,
                        default=self.config_entry.options.get(
                            CONF_MONITORED_CONDITIONS,
                            self.config_entry.data.get(CONF_MONITORED_CONDITIONS, list(MONITORED_CONDITIONS)),
                        ),
                    ): cv.multi_select(MONITORED_CONDITIONS),
                    vol.Optional(
                        CONF_SHOW_TRENDING_ICON,
                        default=self.config_entry.options.get(
                            CONF_SHOW_TRENDING_ICON,
                            self.config_entry.data.get(CONF_SHOW_TRENDING_ICON, DEFAULT_SHOW_TRENDING_ICON),
                        ),
                    ): cv.boolean,
                }
            ),
        )
