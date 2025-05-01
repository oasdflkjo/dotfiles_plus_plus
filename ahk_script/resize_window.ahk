; === Default target size ===
targetWidth := 1866
targetHeight := 1400

; === Window-specific padding adjustments ===
; Format: [WindowIdentifier] := "leftPadding,topPadding,rightPadding,bottomPadding"
WindowAdjustments := {}
WindowAdjustments["Cursor"] := "8,0,8,8" 
WindowAdjustments["Discord"] := "8,0,8,8"

; === Win + C — Center current window with window-specific padding ===
#c::
{
    ; Get active window information
    WinGetClass, activeClass, A
    WinGet, activeProcName, ProcessName, A
    
    ; Default padding
    leftPad := 0
    topPad := 0
    rightPad := 0
    bottomPad := 0
    
    ; Check for window-specific adjustments
    For key, value in WindowAdjustments
    {
        If (InStr(activeClass, key) or InStr(activeProcName, key))
        {
            ; Parse padding values
            paddingArray := StrSplit(value, ",")
            leftPad := paddingArray[1]
            topPad := paddingArray[2]
            rightPad := paddingArray[3]
            bottomPad := paddingArray[4]
            break
        }
    }
    
    ; Calculate position and adjusted size
    adjustedWidth := targetWidth - (leftPad + rightPad)
    adjustedHeight := targetHeight - (topPad + bottomPad)
    x := (A_ScreenWidth - targetWidth) // 2 + leftPad
    y := ((A_ScreenHeight - targetHeight) // 2) + 5 + topPad
    
    WinMove, A,, x, y, adjustedWidth, adjustedHeight
}
return

; === Win + T — Open WezTerm or bring to foreground ===
#t::
{
    ; Check if WezTerm is already running
    If WinExist("ahk_exe wezterm-gui.exe") or WinExist("ahk_exe wezterm.exe")
    {
        ; Minimize all windows first (Win+D)
        Send, #d
        Sleep, 20
        
        ; Then activate WezTerm
        WinActivate
    }
    else
    {
        ; Launch WezTerm if not running
        Run, wezterm
    }
}
return

;; === Debug Hotkey — Ctrl+Alt+D to show window info ===
^!d::
{
    WinGetClass, class, A
    WinGet, process, ProcessName, A
    WinGetTitle, title, A
    MsgBox, Window Class: %class%`nProcess: %process%`nTitle: %title%
}
return
