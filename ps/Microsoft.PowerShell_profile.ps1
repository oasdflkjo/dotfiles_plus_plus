# INFO
# C:\Users\<username>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
#
# winget install fzf
# winget install Neovim.Neovim
#
#  symlink to make this work with git
# New-Item -ItemType SymbolicLink -Path "C:\Users\petri\Documents\PowerShell\Microsoft.PowerShell_profile.ps1" -Target "C:\Users\petri\.config\ps\Microsoft.PowerShell_profile.ps1"

# "aliases"
function b { Set-Location .. }
function c { clear }
function exp { explorer . }
function flstudio { Start-Process -FilePath "C:\Program Files\Image-Line\FL Studio 2024\FL64.exe" }
function htop { btm }
function steam { Start-Process -FilePath "C:\Program Files (x86)\Steam\steam.exe" }

#########################################################
# cd history browser ph
#########################################################
function Set-Location {
    param([string]$Path)

    # Run the real Set-Location
    Microsoft.PowerShell.Management\Set-Location $Path

    # Save to history
    $logfile = "$env:USERPROFILE\.path_history.log"
    "$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) $PWD" | Add-Content $logfile
}

function cd {
    param([string]$Path)
    Set-Location $Path
}

function ph {
    $paths = Get-Content "$env:USERPROFILE\.path_history.log" |
        ForEach-Object { $_.Substring(20) } |
        Sort-Object -Unique |
        fzf --height=40% --reverse --border --prompt "cd> "

    if ($paths) {
        Set-Location $paths
    }
}
$env:FZF_DEFAULT_OPTS = @"
--color=fg:#c0caf5,bg:#1a1b26,hl:#414868
--color=fg+:#c0caf5,bg+:#414868,hl+:#c0caf5
--color=info:#565f89,prompt:#7aa2f7,pointer:#7aa2f7
--color=marker:#73daca,spinner:#e0af68,header:#565f89
"@ -replace "`r`n", " "

#########################################################

Import-Module posh-git

