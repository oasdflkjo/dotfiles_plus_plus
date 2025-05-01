# INFO
# C:\Users\<username>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
#
# winget install fzf
# winget install Neovim.Neovim
#
#  symlink to make this work with git
# New-Item -ItemType SymbolicLink -Path "C:\Users\petri\Documents\PowerShell\Microsoft.PowerShell_profile.ps1" -Target "C:\Users\petri\.config\ps\Microsoft.PowerShell_profile.ps1"
# 
#
#
# Paths
$WEZTERM_LUA_PATH = "C:\Users\petri\.config\wezterm\"
$NVIM_LUA_PATH    = "C:\Users\petri\AppData\Local\nvim\"
$PROJECTS_PATH    = "C:\projects"

# "aliases"
function edit { nvim $PROFILE }
function edit_vim { nvim $NVIM_LUA_PATH }
function edit_wez { nvim $WEZTERM_LUA_PATH }
function b { Set-Location .. }
function c { clear }
function exp { explorer . }
function flstudio { Start-Process -FilePath "C:\Program Files\Image-Line\FL Studio 2024\FL64.exe" }
function htop { btm }
function steam { Start-Process -FilePath "C:\Program Files (x86)\Steam\steam.exe" }

function toggle-taskbar {
    # Direct registry approach for taskbar auto-hide setting
    $path = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    $property = "TaskbarAutoHide"
    
    # Get current value (0 = show always, 1 = auto-hide)
    $currentValue = (Get-ItemProperty -Path $path -Name $property -ErrorAction SilentlyContinue).$property
    
    # If property doesn't exist, create it
    if ($null -eq $currentValue) {
        $currentValue = 0
        New-ItemProperty -Path $path -Name $property -Value $currentValue -PropertyType DWord -Force | Out-Null
    }
    
    # Toggle between 0 and 1
    $newValue = if ($currentValue -eq 0) { 1 } else { 0 }
    
    # Set new value
    Set-ItemProperty -Path $path -Name $property -Value $newValue -Type DWord
    
    # Broadcast setting change to windows
    $code = @'
    [DllImport("user32.dll", SetLastError=true, CharSet=CharSet.Auto)]
    public static extern IntPtr SendMessageTimeoutW(
        IntPtr hWnd, 
        uint Msg, 
        UIntPtr wParam, 
        IntPtr lParam, 
        uint fuFlags, 
        uint uTimeout, 
        out UIntPtr lpdwResult);
'@
    
    $type = Add-Type -MemberDefinition $code -Name WinUser -Namespace Win32Functions -PassThru
    
    [UIntPtr]$result = [UIntPtr]::Zero
    
    # Notify all windows of settings change
    $HWND_BROADCAST = [IntPtr]0xffff
    $WM_SETTINGCHANGE = 0x001A
    
    $type::SendMessageTimeoutW(
        $HWND_BROADCAST,
        $WM_SETTINGCHANGE,
        [UIntPtr]::Zero,
        [IntPtr]::Zero,
        2,
        1000,
        [ref]$result
    ) | Out-Null
}

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

