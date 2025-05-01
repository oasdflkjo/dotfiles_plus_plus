#include <windows.h>

// Global variables
bool taskbarHidden = false;
HWND taskbarWindow = NULL;

// Function to toggle taskbar visibility
void ToggleTaskbar() {
    if (!taskbarWindow) {
        taskbarWindow = FindWindowW(L"Shell_TrayWnd", NULL);
        if (!taskbarWindow) return;
    }
    
    if (taskbarHidden) {
        ShowWindow(taskbarWindow, SW_SHOW);
        taskbarHidden = false;
    } else {
        ShowWindow(taskbarWindow, SW_HIDE);
        taskbarHidden = true;
    }
}

// Hide taskbar on startup
void HideTaskbarOnStartup() {
    taskbarWindow = FindWindowW(L"Shell_TrayWnd", NULL);
    if (taskbarWindow) {
        ShowWindow(taskbarWindow, SW_HIDE);
        taskbarHidden = true;
    }
}

// Win+F12 hotkey callback
LRESULT CALLBACK KeyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode >= 0) {
        KBDLLHOOKSTRUCT* kbStruct = (KBDLLHOOKSTRUCT*)lParam;
        
        // Check for Win+F12
        if (wParam == WM_KEYDOWN && kbStruct->vkCode == VK_F12 && 
            (GetAsyncKeyState(VK_LWIN) & 0x8000 || GetAsyncKeyState(VK_RWIN) & 0x8000)) {
            ToggleTaskbar();
        }
    }
    
    return CallNextHookEx(NULL, nCode, wParam, lParam);
}

int main() {
    // Hide taskbar on startup
    HideTaskbarOnStartup();
    
    // Set up keyboard hook for Win+F12
    HHOOK keyboardHook = SetWindowsHookEx(
        WH_KEYBOARD_LL, KeyboardProc, GetModuleHandle(NULL), 0);
        
    if (!keyboardHook) {
        MessageBoxW(NULL, L"Failed to set keyboard hook", L"Error", MB_OK | MB_ICONERROR);
        return 1;
    }
    
    // Message loop
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    
    UnhookWindowsHookEx(keyboardHook);
    return 0;
}
