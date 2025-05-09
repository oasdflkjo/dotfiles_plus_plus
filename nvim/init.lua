-- Lazy.nvim setup
local lazypath = vim.fn.stdpath("data") .. "/site/pack/lazy/start/lazy.nvim"
vim.opt.rtp:prepend(lazypath)

-- Neovide optimizations
if vim.g.neovide then 
    -- Optimize rendering
    vim.g.neovide_refresh_rate = 165
    vim.g.neovide_refresh_rate_idle = 5
     
    -- Enable hardware acceleration
    vim.g.neovide_hide_mouse_when_typing = true
    vim.g.neovide_remember_window_size = true
end

-- Disable Netrw
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

require("lazy").setup({
  -- LSP support
  { "neovim/nvim-lspconfig" },

  -- Autocompletion engine
  { "hrsh7th/nvim-cmp" },
  { "hrsh7th/cmp-nvim-lsp" },
  { "hrsh7th/cmp-buffer" },
  { "hrsh7th/cmp-path" },

  -- Theme
  { "folke/tokyonight.nvim", lazy = false, priority = 1000 },

  -- Treesitter
  { "nvim-treesitter/nvim-treesitter", build = ":TSUpdate" },

  -- Autopairs (VSCode-style brackets)
  { "windwp/nvim-autopairs", event = "InsertEnter", config = true },
  
  -- File Explorer (VSCode-style sidebar)
  {
    "nvim-tree/nvim-tree.lua",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
      require("nvim-tree").setup({
        sort_by = "case_sensitive",
        view = {
          width = 30,
        },
        renderer = {
          group_empty = true,
          icons = {
            show = {
              file = true,
              folder = true,
              folder_arrow = true,
              git = true,
            },
          },
          -- Format paths with forward slashes consistently
          root_folder_label = function(path)
            -- Convert backslashes to forward slashes
            path = path:gsub("\\", "/")
            -- Limit the path length
            local max_len = 40
            if #path > max_len then
              path = "..." .. string.sub(path, -max_len + 3)
            end
            return path
          end,
        },
        filters = {
          dotfiles = false,  -- Show dotfiles
          git_ignored = false,  -- Show git ignored files
          custom = { "^.git$" }  -- Hide .git folder
        },
        git = {
          ignore = false,  -- Show files even if they're in .gitignore
        },
        on_attach = function(bufnr)
          local api = require("nvim-tree.api")
          
          -- Override directory naming to ensure forward slash consistency
          api.events.subscribe(api.events.Event.NodeRenamed, function(data)
            data.fname = data.fname:gsub("\\", "/")
          end)

          -- Default keymaps
          local function opts(desc)
            return { desc = "nvim-tree: " .. desc, buffer = bufnr, noremap = true, silent = true, nowait = true }
          end
          
          -- Standard mappings
          vim.keymap.set('n', '<Space>', api.node.open.edit, opts('Open'))
          vim.keymap.set('n', '<CR>', api.node.open.edit, opts('Open'))
          vim.keymap.set('n', 'o', api.node.open.edit, opts('Open'))
          vim.keymap.set('n', '<C-v>', api.node.open.vertical, opts('Open: Vertical Split'))
          vim.keymap.set('n', '<C-x>', api.node.open.horizontal, opts('Open: Horizontal Split'))
          vim.keymap.set('n', 'a', api.fs.create, opts('Create'))
          vim.keymap.set('n', 'd', api.fs.remove, opts('Delete'))
          vim.keymap.set('n', 'r', api.fs.rename, opts('Rename'))
          vim.keymap.set('n', 'R', api.tree.reload, opts('Refresh'))
        end,
        -- Auto close when opening files
        actions = {
          open_file = {
            quit_on_open = true,
          },
        },
      })
    end,
  },
  
  -- Fuzzy finder (for Ctrl+p like VSCode)
  {
    "nvim-telescope/telescope.nvim",
    dependencies = { 
      "nvim-lua/plenary.nvim",
      "nvim-tree/nvim-web-devicons" 
    },
  },
  
  -- Status line
  {
    "nvim-lualine/lualine.nvim",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
      require("lualine").setup({
        options = {
          icons_enabled = true,
          theme = "tokyonight",
          component_separators = { left = "", right = "" },
          section_separators = { left = "", right = "" },
          disabled_filetypes = {
            statusline = { "terminal" },
            winbar = {},
          },
          ignore_focus = {},
          always_divide_middle = true,
          globalstatus = true,
          refresh = {
            statusline = 1,  -- Update every 1ms instead of 1000ms
            tabline = 1000,
            winbar = 1000,
          }
        },
        sections = {
          lualine_a = {"mode"},
          lualine_b = {"branch"},
          lualine_c = {"filename"},
          lualine_x = {},
          lualine_y = {},
          lualine_z = {}
        },
        inactive_sections = {
          lualine_a = {},
          lualine_b = {},
          lualine_c = {"filename"},
          lualine_x = {},
          lualine_y = {},
          lualine_z = {}
        }
      })
    end
  },
})

-- Set leader key
vim.g.mapleader = " "

-- Theme
vim.cmd("colorscheme tokyonight-night")

-- Hide mode display in command line (lualine shows it instead)
vim.opt.showmode = false

-- Set global status line
vim.opt.laststatus = 3

-- Hide command line when not in use
vim.opt.cmdheight = 0

-- Show line numbers
vim.o.number = true

-- Enable mouse
vim.o.mouse = "a"

-- Use system clipboard
vim.o.clipboard = "unnamedplus"

-- Make search case-insensitive by default
vim.o.ignorecase = true

-- Center search matches and improve scrolling
vim.o.scrolloff = 15  -- Keep cursor centered with 15 lines above/below
vim.o.sidescrolloff = 8  -- Keep cursor centered horizontally too

-- Remap search from / to \
vim.keymap.set('n', '\\', '/', { desc = "Search forward (remapped from /)" })
vim.keymap.set('v', '\\', '/', { desc = "Search forward in visual mode" })

-- Auto-center search matches
vim.api.nvim_create_autocmd("CmdlineEnter", {
  pattern = "/",
  callback = function()
    vim.keymap.set("n", "n", "nzz", { buffer = true, desc = "Next match and center" })
    vim.keymap.set("n", "N", "Nzz", { buffer = true, desc = "Previous match and center" })
  end,
})

-- Enable syntax highlighting (this should be all you need)
vim.cmd("syntax enable")

-- Make sure filetype detection is on
vim.cmd("filetype plugin indent on")

-- Remember last opened file
vim.opt.shada = "!,'1000,<50,s10,h"


-- Indentation settings
vim.o.tabstop = 4
vim.o.shiftwidth = 4
vim.o.expandtab = true
vim.o.smartindent = true

-- Better colors (for Neovide)
vim.o.termguicolors = true

-- Custom commands for text cleanup
vim.api.nvim_create_user_command("ReplaceTabs", function(opts)
  -- Save cursor position
  local save_cursor = vim.fn.getpos(".")
  -- Replace tabs with spaces
  local count = tonumber(opts.args) or 4
  local spaces = string.rep(" ", count)
  vim.cmd("%s/\\t/" .. spaces .. "/ge")
  -- Restore cursor position
  vim.fn.setpos(".", save_cursor)
end, { nargs = "?" })

vim.api.nvim_create_user_command("RemoveTrailingWhite", function()
  -- Save cursor position
  local save_cursor = vim.fn.getpos(".")
  -- Remove trailing whitespace
  vim.cmd([[%s/\s\+$//e]])
  -- Restore cursor position
  vim.fn.setpos(".", save_cursor)
end, {})

-- Add LLVM to PATH for clangd
local function add_to_path(path)
    local current_path = vim.fn.getenv("PATH")
    if not string.find(current_path, path, 1, true) then
        vim.fn.setenv("PATH", current_path .. ";" .. path)
    end
end

add_to_path([[C:\Program Files\LLVM\bin]])

-- LSP setup
local lspconfig = require("lspconfig")

lspconfig.clangd.setup({
    cmd = { "clangd" },
    filetypes = { "c", "cpp", "objc", "objcpp", "cuda" },
    root_dir = function(fname)
        return lspconfig.util.root_pattern(
            'compile_commands.json',
            'compile_flags.txt',
            '.git'
        )(fname) or vim.fn.getcwd()
    end,
    on_attach = function(_, bufnr)
        -- Enable completion triggered by <c-x><c-o>
        vim.api.nvim_buf_set_option(bufnr, 'omnifunc', 'v:lua.vim.lsp.omnifunc')
    end,
})

-- Setup cmp
local cmp = require("cmp")

cmp.setup({
  mapping = cmp.mapping.preset.insert({
    ["<Tab>"] = cmp.mapping.select_next_item(),
    ["<S-Tab>"] = cmp.mapping.select_prev_item(),
    ["<CR>"] = cmp.mapping.confirm({ select = true }),
  }),
  sources = cmp.config.sources({
    { name = "nvim_lsp" },
    { name = "buffer" },
    { name = "path" },
  }),
})

-- Treesitter config - simplified
require("nvim-treesitter.configs").setup({
  ensure_installed = { "c", "cpp", "lua", "vim", "python" },
  sync_install = false,
  auto_install = true,
  highlight = {
    enable = true,  -- This is the key setting for syntax highlighting
  },
})

-- Configure Telescope for Ctrl+p file searching
local telescope = require("telescope")
telescope.setup({
  defaults = {
    file_ignore_patterns = { "^.git/" },
    path_display = { "smart" },
    sorting_strategy = "ascending",
    layout_config = {
      prompt_position = "top",
    },
  },
})

-- VSCode-like keybindings

-- File management
-- Ctrl+p to fuzzy find files (like VSCode)
vim.keymap.set('n', '<C-p>', function()
  require('telescope.builtin').find_files({
    hidden = false,
  })
end, { desc = "Find files (VSCode Ctrl+p)" })

-- Space+f to toggle file explorer
vim.keymap.set('n', '<leader>f', ':NvimTreeToggle<CR>', { desc = "Toggle file explorer", silent = true })

-- Editing
-- Ctrl+Backspace to delete word in insert mode
vim.keymap.set('i', '<C-BS>', '<C-w>', { desc = "Delete word before cursor (VSCode style)" })
vim.keymap.set('i', '<C-H>', '<C-w>', { desc = "Delete word before cursor (terminal compatibility)" })
-- Add explicit terminal key code mapping for Ctrl+Backspace
vim.api.nvim_exec([[
  map! <C-BS> <C-w>
  map! <C-h> <C-w>
]], false)

-- Navigation
-- Alt+Left/Right to navigate through the jump list (VSCode Go Back/Forward)
vim.keymap.set('n', '<A-Left>', '<C-o>', { desc = "Go back to previous cursor position (VSCode Alt+Left)" })
vim.keymap.set('n', '<A-Right>', '<C-i>', { desc = "Go forward to next cursor position (VSCode Alt+Right)" })

-- Also add the same for insert mode
vim.keymap.set('i', '<A-Left>', '<Esc><C-o>a', { desc = "Go back to previous cursor position in insert mode" })
vim.keymap.set('i', '<A-Right>', '<Esc><C-i>a', { desc = "Go forward to next cursor position in insert mode" })

-- Alt+o to switch between header and source files (like VSCode)
vim.keymap.set('n', '<A-o>', function()
  local current_file = vim.fn.expand('%:p')
  local extension = vim.fn.expand('%:e')
  local basename = vim.fn.expand('%:r')
  local filename = vim.fn.expand('%:t:r')
  
  -- Define file extension pairs
  local paired_extensions = {
    c = 'h',
    cpp = 'hpp',
    h = 'c',
    hpp = 'cpp'
  }
  
  -- Get the paired extension
  local target_ext = paired_extensions[extension]
  if not target_ext then
    return  -- Silently do nothing for unsupported file types
  end
  
  -- Build possible file paths to try
  local possible_files = {
    basename .. '.' .. target_ext,
    vim.fn.expand('%:p:h') .. '/' .. filename .. '.' .. target_ext,
  }
  
  -- Try to find and open the corresponding file
  local found_file = false
  for _, file_path in ipairs(possible_files) do
    if vim.fn.filereadable(file_path) == 1 then
      vim.cmd('edit ' .. vim.fn.fnameescape(file_path))
      found_file = true
      break
    end
  end
  
  -- If no file found, do nothing silently
end, { desc = "Switch between header/source files (like VSCode Alt+o)" })

-- Terminal megablock ```````````````````````````````````````````````````````````````````

-- Use PowerShell Core (pwsh) as the default shell
vim.opt.shell = "pwsh"
vim.opt.shellcmdflag = "-NoLogo -NoProfile -ExecutionPolicy RemoteSigned -Command"
vim.opt.shellquote = ""
vim.opt.shellxquote = ""

-- Store original UI state to restore when leaving terminal
local terminal_ui_state = {
  number = true,
  relativenumber = false,
  signcolumn = "auto",
  laststatus = 2,
  showmode = true,
  ruler = true,
  cmdheight = 1
}

-- Smart terminal toggle with <leader>t
local terminal_bufnr = nil

vim.keymap.set("n", "<leader>t", function()
  -- Search for existing terminal buffer by name
  for _, bufnr in ipairs(vim.api.nvim_list_bufs()) do
    if vim.api.nvim_buf_get_option(bufnr, "buftype") == "terminal" then
      terminal_bufnr = bufnr
      break
    end
  end

  if terminal_bufnr then
    local wins = vim.fn.win_findbuf(terminal_bufnr)
    if #wins > 0 then
      -- If terminal is visible, close the window
      vim.api.nvim_win_close(wins[1], true)
      
      -- Restore UI elements when closing terminal
      vim.opt.laststatus = terminal_ui_state.laststatus
      vim.opt.showmode = terminal_ui_state.showmode
      vim.opt.ruler = terminal_ui_state.ruler
      vim.opt.cmdheight = terminal_ui_state.cmdheight
    else
      -- Terminal buffer exists but hidden → show it again
      
      -- Save current UI state before opening terminal
      terminal_ui_state.laststatus = vim.opt.laststatus:get()
      terminal_ui_state.showmode = vim.opt.showmode:get()
      terminal_ui_state.ruler = vim.opt.ruler:get()
      terminal_ui_state.cmdheight = vim.opt.cmdheight:get()
      
      -- Hide global UI elements when opening terminal
      vim.opt.laststatus = 0
      vim.opt.showmode = false
      vim.opt.ruler = false
      vim.opt.cmdheight = 0
      
      vim.cmd("botright 20split")
      vim.api.nvim_win_set_buf(0, terminal_bufnr)
      vim.cmd("startinsert")
    end
  else
    -- No terminal exists yet → create one
    
    -- Save current UI state before opening terminal
    terminal_ui_state.laststatus = vim.opt.laststatus:get()
    terminal_ui_state.showmode = vim.opt.showmode:get()
    terminal_ui_state.ruler = vim.opt.ruler:get()
    terminal_ui_state.cmdheight = vim.opt.cmdheight:get()
    
    -- Hide global UI elements when opening terminal
    vim.opt.laststatus = 0
    vim.opt.showmode = false
    vim.opt.ruler = false
    vim.opt.cmdheight = 0
    
    vim.cmd("botright 20split | terminal")
    vim.cmd("startinsert")
    terminal_bufnr = vim.api.nvim_get_current_buf()
  end
end, { desc = "Toggle terminal" })

-- Improved ESC behavior in terminal
-- First ESC exits terminal mode, second ESC hides the terminal
vim.keymap.set("t", "<Esc>", [[<C-\><C-n>]], { desc = "ESC exits terminal mode" })

-- Map Ctrl+Backspace in terminal mode to send the correct escape sequence
-- This sends the right escape sequence for Ctrl+Backspace in PowerShell
vim.keymap.set("t", "<C-BS>", [[<C-w>]], { desc = "Ctrl+Backspace in terminal mode" })
vim.keymap.set("t", "<C-H>", [[<C-w>]], { desc = "Ctrl+Backspace in terminal mode (compatibility)" })

vim.keymap.set("n", "<Esc>", function()
  local bufnr = vim.api.nvim_get_current_buf()
  if vim.api.nvim_buf_get_option(bufnr, "buftype") == "terminal" then
    -- If we're in normal mode in a terminal buffer, hide it
    local win = vim.api.nvim_get_current_win()
    vim.api.nvim_win_close(win, true)
    
    -- Restore UI elements when closing terminal
    vim.opt.laststatus = terminal_ui_state.laststatus
    vim.opt.showmode = terminal_ui_state.showmode
    vim.opt.ruler = terminal_ui_state.ruler
    vim.opt.cmdheight = terminal_ui_state.cmdheight
  else
    -- Regular ESC behavior in other contexts
    vim.cmd("echo ''") -- Clear any messages
  end
end, { desc = "ESC in terminal normal mode hides terminal" })

vim.api.nvim_create_autocmd("TermOpen", {
  pattern = "*",
  callback = function()
    -- These settings are only for the terminal buffer/window
    vim.opt_local.number = false
    vim.opt_local.relativenumber = false
    vim.opt_local.signcolumn = "no"
  end,
})

-- Font size persistence
local function get_font_size_file()
  return vim.fn.stdpath("data") .. "/font_size.txt"
end

local function save_font_size(size)
  local file = io.open(get_font_size_file(), "w")
  if file then
    file:write(tostring(size))
    file:close()
  end
end

local function load_font_size()
  local file = io.open(get_font_size_file(), "r")
  if file then
    local size = tonumber(file:read("*a"))
    file:close()
    return size
  end
  return 12  -- Default size if no saved size exists
end

-- Font size control
local function change_font_size(delta)
  local guifont = vim.o.guifont
  local size = tonumber(string.match(guifont, ":h(%d+)"))
  if size then
    size = size + delta
    if size < 1 then size = 1 end
    if size > 100 then size = 100 end
    vim.o.guifont = string.gsub(guifont, ":h%d+", ":h" .. size)
    save_font_size(size)
  end
end

-- Initialize font size from saved value
local saved_size = load_font_size()
vim.o.guifont = "Consolas:h" .. saved_size

-- Increase font size with Ctrl+=
vim.keymap.set('n', '<C-=>', function() change_font_size(1) end, { desc = "Increase font size" })
vim.keymap.set('i', '<C-=>', function() change_font_size(1) end, { desc = "Increase font size" })

-- Decrease font size with Ctrl+-
vim.keymap.set('n', '<C-->', function() change_font_size(-1) end, { desc = "Decrease font size" })
vim.keymap.set('i', '<C-->', function() change_font_size(-1) end, { desc = "Decrease font size" })

-- Ensure lua directory is in runtime path
vim.opt.runtimepath:append(vim.fn.stdpath("config") .. "/lua")

-- Global word wrap settings
vim.opt.wrap = true  -- Enable line wrap
vim.opt.linebreak = true  -- Don't break words
vim.opt.breakindent = true  -- Preserve indentation in wrapped text
vim.opt.breakat = " "  -- Only break at spaces
vim.opt.showbreak = "  "  -- Indent wrapped lines slightly
vim.opt.formatoptions:remove("t")  -- Don't auto-wrap text
vim.opt.formatoptions:append("l")  -- Don't wrap if line is already long

-- Make j/k move by visual lines
vim.keymap.set('n', 'j', "v:count == 0 ? 'gj' : 'j'", { expr = true })
vim.keymap.set('n', 'k', "v:count == 0 ? 'gk' : 'k'", { expr = true })
vim.keymap.set('v', 'j', "v:count == 0 ? 'gj' : 'j'", { expr = true })
vim.keymap.set('v', 'k', "v:count == 0 ? 'gk' : 'k'", { expr = true })

-- Custom movement functions
local function find_next_char_in_column()
    local current_col = vim.fn.col('.')
    local current_line = vim.fn.line('.')
    local last_line = vim.fn.line('$')
    
    -- Search downward
    for line = current_line + 1, last_line do
        -- Get content of the line
        local line_text = vim.fn.getline(line)
        -- Convert tabs to spaces using the current tab settings
        line_text = vim.fn.substitute(line_text, '\t', string.rep(' ', vim.bo.tabstop), 'g')
        
        -- Check if the line has a non-space character at our column
        if #line_text >= current_col and line_text:sub(current_col, current_col):match('%S') then
            return line
        end
    end
    return current_line
end

local function find_prev_char_in_column()
    local current_col = vim.fn.col('.')
    local current_line = vim.fn.line('.')
    
    -- Search upward
    for line = current_line - 1, 1, -1 do
        -- Get content of the line
        local line_text = vim.fn.getline(line)
        -- Convert tabs to spaces using the current tab settings
        line_text = vim.fn.substitute(line_text, '\t', string.rep(' ', vim.bo.tabstop), 'g')
        
        -- Check if the line has a non-space character at our column
        if #line_text >= current_col and line_text:sub(current_col, current_col):match('%S') then
            return line
        end
    end
    return current_line
end

-- Custom vertical movement mappings
vim.keymap.set('n', '<C-Up>', function()
    local target_line = find_prev_char_in_column()
    if target_line ~= vim.fn.line('.') then
        vim.cmd('normal! ' .. target_line .. 'G')
    end
end, { desc = "Jump to previous line with character in current column" })

vim.keymap.set('n', '<C-Down>', function()
    local target_line = find_next_char_in_column()
    if target_line ~= vim.fn.line('.') then
        vim.cmd('normal! ' .. target_line .. 'G')
    end
end, { desc = "Jump to next line with character in current column" })

-- Horizontal movement (simple word navigation)
vim.keymap.set('n', '<C-Right>', 'w', { desc = "Move to next word" })
vim.keymap.set('n', '<C-Left>', 'b', { desc = "Move to previous word" })

-- Simplified format on save using clang-format
vim.api.nvim_create_autocmd("BufWritePre", {
    pattern = "*.c,*.cpp,*.h,*.hpp",
    callback = function()
        vim.fn.jobstart({ 'clang-format', '-i', vim.fn.expand('%:p') }, {
            on_exit = function()
                vim.cmd('checktime')  -- Check if the file has changed
            end,
        })
    end,
})

-- Simple utility function to force syntax highlighting
vim.api.nvim_create_user_command("FixSyntax", function()
  -- Reset and enable syntax highlighting
  vim.cmd("syntax off")
  vim.cmd("syntax on")
  
  -- Force filetype detection
  vim.cmd("filetype detect")
  
  -- If Treesitter is available, try to enable it
  pcall(function() vim.cmd("TSEnable highlight") end)
  
  print("Syntax highlighting has been reset and enabled")
end, {})

-- Set Python path (update this to your Python installation path if needed)
vim.g.python3_host_prog = vim.fn.exepath('python')
