#pragma once

#define WIN32_LEAN_AND_MEAN

#include <windows.h>

extern "C" {
int		WebBrowser_Startup(HINSTANCE hInstance);
void	WebBrowser_Cleanup();
void	WebBrowser_Destroy();
int		WebBrowser_Show(HWND parent, const char* addr, const RECT* rcWebBrowser);
void	WebBrowser_Hide();
void	WebBrowser_Move(const RECT* rcWebBrowser);

int WebBrowser_IsVisible();
const RECT& WebBrowser_GetRect();
// MT2009_PLUS_ITEMSHOP_V3_V3: a WM_MOUSEWHEEL of the game window over the shop -> the page (CWebBrowser.c)
int		WebBrowser_ForwardMouseWheel(WPARAM wParam, LPARAM lParam);
}
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f

// Files shared by GameCore.top
