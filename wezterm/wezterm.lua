local wezterm = require 'wezterm'
local config = {}

-- visuals
config.font = wezterm.font_with_fallback {
  'JetBrainsMono Nerd Font',
  'Cascadia Code PL',
}
config.font_size = 16.0
config.color_scheme = 'tokyonight'

local palette = {
  bg_dark     = "#1a1b26", -- background behind tabs, terminal bg
  bg_dim      = "#2a2b3c", -- hover/low emphasis backgrounds
  bg          = "#1e1e2e", -- normal background
  bg_lighter  = "#414868", -- tab active, muted blocks
  fg          = "#c0caf5", -- normal foreground
  fg_muted    = "#737aa2", -- inactive tab text, low-emphasis
  fg_bright   = "#ffffff", -- strong foreground

  accent_red    = "#f7768e",
  accent_green  = "#73daca",
  accent_blue   = "#7dcfff",
  accent_purple = "#bb9af7",
  accent_yellow = "#e0af68",
}

config.colors = {
  ansi = {
    "#414868", -- ansi black
    "#f7768e", -- ansi red
    "#73daca", -- ansi green
    "#bb9af7", -- ansi blue
    "#414868", -- ansi yellow (powershell folder color)
    "#bb9af7", -- ansi magenta
    "#7dcfff", -- ansi cyan
    "#c0caf5", -- ansi white
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

config.window_decorations = "RESIZE" -- enable drag
config.window_padding = {
  left = 5, right = 0, top = 8, bottom = 0,
}
config.enable_scroll_bar = false
config.window_background_opacity = 0.95
config.adjust_window_size_when_changing_font_size = false

-- tabs

config.show_tab_index_in_tab_bar = false
config.hide_tab_bar_if_only_one_tab = true
config.enable_tab_bar = true
config.use_fancy_tab_bar = false
config.colors.tab_bar = {
  background = palette.bg_dark, -- background behind the tabs

  active_tab = {
    bg_color = "#414868",
    fg_color = "#c0caf5",
    intensity = "Normal",
    underline = "None",
    italic = false,
    strikethrough = false,
  },

  inactive_tab = {
    bg_color = "#1a1b26",
    fg_color = "#737aa2",
  },

  inactive_tab_hover = {
    bg_color = "#2a2b3c",
    fg_color = "#c0caf5",
    italic = false,
  },

  new_tab = {
    bg_color = "#1a1b26",
    fg_color = "#737aa2",
  },

  new_tab_hover = {
    bg_color = "#2a2b3c",
    fg_color = "#c0caf5",
  },
}

-- terminal
config.default_prog = { "pwsh.exe", "-NoLogo" }

return config

