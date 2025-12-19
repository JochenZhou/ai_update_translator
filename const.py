"""Constants for the AI Update Translator integration."""
from typing import Final

DOMAIN: Final = "ai_update_translator"

CONF_AI_ENGINE: Final = "ai_engine"
CONF_PROMPT: Final = "prompt"

DEFAULT_PROMPT: Final = (
    "你是一位专业的软件更新日志翻译专家。请将以下软件更新摘要翻译为简洁、地道的中文。"
    "保留版本号和关键专有名词（如集成名称、组件名称）。"
    "输出结果仅包含翻译后的文本，不要有任何开场白或解释。"
)

# Platforms
PLATFORMS: Final = []

# Attributes
ATTR_ORIGINAL_TEXT: Final = "original_text"
ATTR_TRANSLATED_TEXT: Final = "translated_text"
ATTR_UPDATE_ENTITY: Final = "update_entity"
