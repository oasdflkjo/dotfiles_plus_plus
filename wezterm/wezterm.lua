local wezterm = require 'wezterm'
local config = {}

-- visuals
config.font = wezterm.font_with_fallback {
  'JetBrainsMono Nerd Font',
  'Cascadia Code PL',
}
config.font_size = 16.0
config.color_scheme = 'tokyonight'

config.colors = {
  ansi = {
    "#414868", -- black
    "#f7768e", -- red
    "#73daca", -- green
    "#bb9af7", -- blue
    "#414868", -- yellow (powershell folder color)
    "#bb9af7", -- magenta
    "#7dcfff", -- cyan
    "#c0caf5", -- white
  },
  brights = {
    "#414868", -- bright black
    "#f7768e", -- bright red
    "#73daca", -- bright green
    "#c0caf5", -- bright blue (search text) 
    "#e0af68", -- bright yellow
    "#bb9af7", -- bright magenta
    "#7dcfff", -- bright cyan
    "#c0caf5", -- bright white
  },
}

config.enable_tab_bar = true
config.hide_tab_bar_if_only_one_tab = true
config.window_decorations = "RESIZE" -- enable drag
config.window_padding = {
  left = 5, right = 0, top = 8, bottom = 0,
}
config.enable_scroll_bar = false
config.use_fancy_tab_bar = true
config.window_background_opacity = 0.95
config.adjust_window_size_when_changing_font_size = false

-- terminal
config.default_prog = { "pwsh.exe", "-NoLogo" }

return config

