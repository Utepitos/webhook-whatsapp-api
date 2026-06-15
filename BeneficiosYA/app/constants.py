"""Constantes globales de la aplicación. Sin lógica, solo valores con nombre."""

# --- Claude API ---
CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_TOKENS_CHAT = 1200
MAX_TOKENS_VISION = 800

# --- Gestión de conversación ---
MAX_HISTORY_MESSAGES = 12
MIN_PROFILE_FIELDS_FOR_SISBEN = 3

# --- RAG ---
RAG_TOP_K = 4
RAG_MIN_SCORE = 0.1

# --- SISBEN IV: umbrales de grupos (aproximación, no oficial) ---
SISBEN_INITIAL_SCORE = 50.0
SISBEN_SCORE_FLOOR = 0.0
SISBEN_SCORE_CEILING = 80.0
SISBEN_GROUP_A_MAX = 11.68
SISBEN_GROUP_B_MAX = 22.89
SISBEN_GROUP_C_MAX = 47.99

# --- WhatsApp Cloud API ---
WHATSAPP_API_URL = "https://graph.facebook.com/v19.0"
WHATSAPP_REQUEST_TIMEOUT = 10.0
WHATSAPP_IMAGE_DOWNLOAD_TIMEOUT = 20.0
