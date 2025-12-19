"""Data coordinator for AI Update Translator."""
from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant, State, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers import aiohttp_client
from homeassistant.components import conversation
from homeassistant.const import EVENT_STATE_CHANGED, STATE_ON, MATCH_ALL

from .const import DOMAIN, CONF_AI_ENGINE, CONF_PROMPT, DEFAULT_PROMPT

_LOGGER = logging.getLogger(__name__)

class AIUpdateTranslatorCoordinator(DataUpdateCoordinator[dict[str, str]]):
    """Class to manage fetching translation data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self.entry = entry
        self.translations: dict[str, str] = {}
        self.original_texts: dict[str, str] = {}
        self._unsub_listener = None
        _LOGGER.info("AI Update Translator Coordinator initialized")

    @callback
    def async_setup(self):
        """Set up the state change listener."""
        # Listen for ALL state changes and filter by domain inside to be sure we catch everything
        self._unsub_listener = self.hass.bus.async_listen(
            EVENT_STATE_CHANGED, self._handle_state_changed_event
        )
        # Initial check for existing entities
        self.hass.async_create_task(self._initial_check())

    @callback
    def async_teardown(self):
        """Unsubscribe from listeners."""
        if self._unsub_listener:
            self._unsub_listener()

    async def _initial_check(self):
        """Check all update entities on startup."""
        for state in self.hass.states.async_all("update"):
            await self._process_update_entity(state)

    async def _handle_state_changed_event(self, event):
        """Handle state change of any entity."""
        entity_id = event.data.get("entity_id")
        if not entity_id or not entity_id.startswith("update."):
            return

        new_state: State = event.data.get("new_state")
        if new_state is None:
            return

        await self._process_update_entity(new_state)

    async def _process_update_entity(self, state: State):
        """Process an update entity to see if it needs translation."""
        _LOGGER.info("Checking update entity: %s (State: %s)", state.entity_id, state.state)

        # Allow 'on' or any version string (anything that isn't 'off', 'unavailable', or 'unknown')
        if state.state in ("off", "unavailable", "unknown"):
            return

        # Common attributes for update notes/changelogs
        possible_attributes = [
            "summary",
            "release_summary",
            "release_notes",
            "latest_version_notes",
            "changelog",
            "body",
            "notes"
        ]
        
        summary = None
        for attr in possible_attributes:
            val = state.attributes.get(attr)
            if val and isinstance(val, str) and len(val.strip()) > 0:
                summary = val
                break
        
        # If no text summary, check for release_url (common in GitHub-based integrations)
        if not summary:
            release_url = state.attributes.get("release_url")
            if release_url:
                _LOGGER.info("Fetching release notes from URL for %s: %s", state.entity_id, release_url)
                summary = await self._fetch_release_notes_from_url(release_url)
        
        if not summary:
            _LOGGER.info("No update notes found for %s in attributes: %s", state.entity_id, list(state.attributes.keys()))
            return

        # Check if we already translated THIS exact text for THIS entity
        if self.original_texts.get(state.entity_id) == summary:
            # Re-apply translation if it was reverted by the original integration
            if self.entry.data.get(CONF_REPLACE_ORIGINAL, True):
                if state.attributes.get("release_summary") != self.translations.get(state.entity_id):
                    _LOGGER.info("Re-applying translation to %s", state.entity_id)
                    await self._overwrite_original_entity(state, self.translations[state.entity_id])
            return

        # Check if the summary matches what we just translated (to prevent loops when overwriting)
        if self.translations.get(state.entity_id) == summary:
            return

        _LOGGER.debug("Translating update for %s", state.entity_id)
        translated_text = await self._translate_text(summary)
        
        if translated_text:
            self.translations[state.entity_id] = translated_text
            self.original_texts[state.entity_id] = summary
            
            # Always replace the original entity's attributes now as requested
            await self._overwrite_original_entity(state, translated_text)

    async def _overwrite_original_entity(self, state: State, translated_text: str):
        """Overwrite the original entity's release notes with the translated text."""
        # Get the latest state to ensure we have the most up-to-date attributes
        current_state = self.hass.states.get(state.entity_id)
        if not current_state:
            return

        new_attributes = dict(current_state.attributes)
        
        # Force set all common release summary/notes attributes
        # This ensuring the UI picks up our translation regardless of which attribute it prioritizes
        new_attributes["release_summary"] = translated_text
        new_attributes["summary"] = translated_text
        new_attributes["release_notes"] = translated_text
        new_attributes["latest_version_notes"] = translated_text
        
        _LOGGER.info("Overwriting attributes for %s with Chinese translation", state.entity_id)
        self.hass.states.async_set(
            state.entity_id,
            current_state.state,
            new_attributes,
        )

        # 2. Deep patch the entity object for official Card (Advanced)
        try:
            if "update" in self.hass.data:
                component = self.hass.data["update"]
                entity = component.get_entity(state.entity_id)
                if entity:
                    _LOGGER.debug("Deep patching entity %s for official card", state.entity_id)
                    
                    async def patched_release_notes(*args, **kwargs):
                        """Return translated text instead of the original."""
                        return translated_text
                    
                    # Apply the patch to the live object
                    entity.async_release_notes = patched_release_notes
        except Exception as deep_err:
            _LOGGER.debug("Could not deep patch entity %s: %s", state.entity_id, deep_err)

    async def _translate_text(self, text: str) -> str | None:
        """Call AI engine to translate text."""
        # Prioritize options over data to ensure user changes take effect
        ai_engine = self.entry.options.get(CONF_AI_ENGINE) or self.entry.data.get(CONF_AI_ENGINE)
        prompt_prefix = self.entry.options.get(CONF_PROMPT) or self.entry.data.get(CONF_PROMPT, DEFAULT_PROMPT)
        
        full_prompt = f"{prompt_prefix}\n\n内容如下：\n{text}"
        
        try:
            result = await conversation.async_converse(
                hass=self.hass,
                text=full_prompt,
                conversation_id=None,
                context=None,
                agent_id=ai_engine,
            )
            
            if result and result.response:
                speech = result.response.speech.get("plain", {})
                if isinstance(speech, dict):
                    translated_text = speech.get("speech")
                else:
                    translated_text = speech
                
                if translated_text:
                    return translated_text
                else:
                    _LOGGER.warning("AI agent returned empty speech for %s", ai_engine)
            else:
                _LOGGER.warning("AI agent failed to provide a valid response: %s", result)
        except Exception as err:
            _LOGGER.error("Error during AI translation with %s: %s", ai_engine, err)
        
        return None

    async def _fetch_release_notes_from_url(self, url: str) -> str | None:
        """Fetch release notes from a URL (GitHub releases supported)."""
        try:
            # Improved GitHub URL parsing
            github_match = re.match(r"https://github\.com/([^/]+)/([^/]+)/releases/(?:tag/)?([^/?# ]+)", url)
            if github_match:
                owner, repo, tag = github_match.groups()
                
                if tag == "latest":
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                else:
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
                
                session = aiohttp_client.async_get_clientsession(self.hass)
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        body = data.get("body", "")
                        if body:
                            _LOGGER.debug("Fetched release notes from GitHub API: %s chars", len(body))
                            return body
                    else:
                        _LOGGER.warning("Failed to fetch GitHub release: HTTP %s", response.status)
            else:
                _LOGGER.debug("release_url is not a GitHub release URL: %s", url)
        except Exception as err:
            _LOGGER.error("Error fetching release notes from %s: %s", url, err)
        
        return None

    async def _async_update_data(self) -> dict[str, str]:
        """Fetch data from API (not used as we use push model)."""
        return self.translations
