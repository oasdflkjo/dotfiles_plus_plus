; === Default target size ===
targetWidth := 1866
targetHeight := 1400

; === Window-specific padding adjustments ===
; Format: [WindowIdentifier] := "leftPadding,topPadding,rightPadding,bottomPadding"
WindowAdjustments := {}
WindowAdjustments["Cursor"] := "7,0,7,7"    ; Cursor needs padding on left, right and bottom

; === Ctrl + Alt + C — Center current window with window-specific padding ===
^!c::
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

; === Debug Hotkey — Ctrl+Alt+D to show window info ===
^!d::
{
    WinGetClass, class, A
    WinGet, process, ProcessName, A
    WinGetTitle, title, A
    MsgBox, Window Class: %class%`nProcess: %process%`nTitle: %title%
}
return

