THEMES = {
    "nuntius": {
        "name": "Nuntius Default",
        "primary": "#eebd35",
        "secondary": "#00bcd4",
        "accent": "#ff6b6b",
        "background": "#1a1b26",
        "surface": "#24283b",
        "chat_user_bg": "#2d3b5e",
        "chat_assistant_bg": "#1e2a3a",
        "chat_tool_bg": "#2a2a2a",
        "chat_system_bg": "#1a1a2e",
        "text_primary": "#c0caf5",
        "text_secondary": "#a9b1d6",
        "text_dim": "#565f89",
        "border": "#3b4261",
        "success": "#9ece6a",
        "error": "#f7768e",
        "warning": "#e0af68",
    },
    "dracula": {
        "name": "Dracula",
        "primary": "#ff79c6",
        "secondary": "#8be9fd",
        "accent": "#50fa7b",
        "background": "#282a36",
        "surface": "#44475a",
        "chat_user_bg": "#3a3c4e",
        "chat_assistant_bg": "#2c2e3e",
        "chat_tool_bg": "#333544",
        "chat_system_bg": "#222430",
        "text_primary": "#f8f8f2",
        "text_secondary": "#e0e0d0",
        "text_dim": "#6272a4",
        "border": "#6272a4",
        "success": "#50fa7b",
        "error": "#ff5555",
        "warning": "#f1fa8c",
    },
    "monokai": {
        "name": "Monokai",
        "primary": "#f92672",
        "secondary": "#66d9ef",
        "accent": "#a6e22e",
        "background": "#272822",
        "surface": "#383830",
        "chat_user_bg": "#3e3d32",
        "chat_assistant_bg": "#2e2e27",
        "chat_tool_bg": "#33332c",
        "chat_system_bg": "#22221c",
        "text_primary": "#f8f8f2",
        "text_secondary": "#cfcfc2",
        "text_dim": "#75715e",
        "border": "#75715e",
        "success": "#a6e22e",
        "error": "#f92672",
        "warning": "#fd971f",
    },
    "nord": {
        "name": "Nord",
        "primary": "#88c0d0",
        "secondary": "#81a1c1",
        "accent": "#bf616a",
        "background": "#2e3440",
        "surface": "#3b4252",
        "chat_user_bg": "#434c5e",
        "chat_assistant_bg": "#3b4252",
        "chat_tool_bg": "#353b48",
        "chat_system_bg": "#2a303c",
        "text_primary": "#eceff4",
        "text_secondary": "#d8dee9",
        "text_dim": "#616e88",
        "border": "#4c566a",
        "success": "#a3be8c",
        "error": "#bf616a",
        "warning": "#ebcb8b",
    },
    "light": {
        "name": "Light",
        "primary": "#eebd35",
        "secondary": "#00897b",
        "accent": "#e53935",
        "background": "#fafafa",
        "surface": "#ffffff",
        "chat_user_bg": "#e3f2fd",
        "chat_assistant_bg": "#f5f5f5",
        "chat_tool_bg": "#eeeeee",
        "chat_system_bg": "#fce4ec",
        "text_primary": "#212121",
        "text_secondary": "#424242",
        "text_dim": "#9e9e9e",
        "border": "#bdbdbd",
        "success": "#43a047",
        "error": "#e53935",
        "warning": "#fb8c00",
    },
    "gruvbox": {
        "name": "Gruvbox Dark",
        "primary": "#fabd2f",
        "secondary": "#83a598",
        "accent": "#fb4934",
        "background": "#282828",
        "surface": "#3c3836",
        "chat_user_bg": "#4a453e",
        "chat_assistant_bg": "#3c3836",
        "chat_tool_bg": "#34302c",
        "chat_system_bg": "#2a2825",
        "text_primary": "#ebdbb2",
        "text_secondary": "#d5c4a1",
        "text_dim": "#928374",
        "border": "#665c54",
        "success": "#b8bb26",
        "error": "#fb4934",
        "warning": "#fe8019",
    },
}


def get_theme(name: str = "nuntius") -> dict:
    return THEMES.get(name, THEMES["nuntius"])


def list_themes() -> list[str]:
    return list(THEMES.keys())


def get_theme_css(t: dict) -> str:
    return f"""
$primary: {t["primary"]};
$secondary: {t["secondary"]};
$accent: {t["accent"]};
$background: {t["background"]};
$surface: {t["surface"]};
$chat-user-bg: {t["chat_user_bg"]};
$chat-assistant-bg: {t["chat_assistant_bg"]};
$chat-tool-bg: {t["chat_tool_bg"]};
$chat-system-bg: {t["chat_system_bg"]};
$text-primary: {t["text_primary"]};
$text-secondary: {t["text_secondary"]};
$text-dim: {t["text_dim"]};
$border: {t["border"]};
$success: {t["success"]};
$error: {t["error"]};
$warning: {t["warning"]};
"""
