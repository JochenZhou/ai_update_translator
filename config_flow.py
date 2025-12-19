"""Config flow for AI Update Translator integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.components import conversation
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_AI_ENGINE, CONF_PROMPT, DEFAULT_PROMPT

_LOGGER = logging.getLogger(__name__)

def get_ai_engines(hass: HomeAssistant) -> list[str]:
    """Get list of conversation entities."""
    ent_reg = er.async_get(hass)
    return [
        entity_id 
        for entity_id in hass.states.async_entity_ids("conversation")
    ]

class AIUpdateTranslatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Update Translator."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
            
        errors: dict[str, str] = {}
        
        engines = get_ai_engines(self.hass)
        if not engines:
            return self.async_abort(reason="no_ai_engines")

        if user_input is not None:
            return self.async_create_entry(
                title="AI 更新翻译官",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AI_ENGINE): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="conversation")
                    ),
                    vol.Required(CONF_PROMPT, default=DEFAULT_PROMPT): selector.TextSelector(
                        selector.TextSelectorConfig(multiline=True)
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return AIUpdateTranslatorOptionsFlow(config_entry)

class AIUpdateTranslatorOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for AI Update Translator."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Merge options and data to get the most recent values
        current_config = {**self.config_entry.data, **self.config_entry.options}
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_AI_ENGINE,
                        default=current_config.get(CONF_AI_ENGINE),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="conversation")
                    ),
                    vol.Required(
                        CONF_PROMPT,
                        default=current_config.get(CONF_PROMPT, DEFAULT_PROMPT),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(multiline=True)
                    ),
                }
            ),
        )
