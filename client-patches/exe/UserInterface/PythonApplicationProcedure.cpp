#include "StdAfx.h"
#include "PythonApplication.h"
#include "../eterlib/Camera.h"
#include "../CWebBrowser/CWebBrowser.h"

#include <winuser.h>

static int gs_nMouseCaptureRef = 0;

void CPythonApplication::SafeSetCapture()
{
	SetCapture(m_hWnd);
	gs_nMouseCaptureRef++;
}

void CPythonApplication::SafeReleaseCapture()
{
	gs_nMouseCaptureRef--;
	if (gs_nMouseCaptureRef==0)
		ReleaseCapture();
}

#ifdef ENABLE_MT2009_BORDERLESS_FULLSCREEN
// MT2009_PLUS_BORDERLESS_FULLSCREEN_V1: "Pelny ekran" as a borderless window (device Windowed=TRUE, see Locale_inc.h).
// The window stays on the monitor it was created on (the primary one); its device name is kept, so the display mode
// is changed and restored on that monitor only, and the window is put back over that monitor's rect after a change.
namespace
{
	char s_szFullScreenDevice[CCHDEVICENAME] = {};	// "\\.\DISPLAYn" of the game's monitor, "" - not known yet
	bool s_isFullScreenModeChanged = false;			// our CDS_FULLSCREEN mode is on (restore on deactivate / exit)

	struct SFullScreenMonitorFind
	{
		const char* c_szDevice;
		RECT rcMonitor;
		bool isFound;
	};

	BOOL CALLBACK FullScreenMonitorEnumProc(HMONITOR hMonitor, HDC, LPRECT, LPARAM lParam)
	{
		SFullScreenMonitorFind* pFind = (SFullScreenMonitorFind*) lParam;
		MONITORINFOEXA kInfo;
		kInfo.cbSize = sizeof(kInfo);
		if (GetMonitorInfoA(hMonitor, &kInfo) && 0 == _stricmp(kInfo.szDevice, pFind->c_szDevice))
		{
			pFind->rcMonitor = kInfo.rcMonitor;
			pFind->isFound = true;
			return FALSE;
		}
		return TRUE;
	}

	void FullScreenRememberMonitor(HWND hWnd)
	{
		if (s_szFullScreenDevice[0])
			return;

		MONITORINFOEXA kInfo;
		kInfo.cbSize = sizeof(kInfo);
		HMONITOR hMonitor = MonitorFromWindow(hWnd, MONITOR_DEFAULTTOPRIMARY);
		if (hMonitor && GetMonitorInfoA(hMonitor, &kInfo))
		{
			strncpy(s_szFullScreenDevice, kInfo.szDevice, sizeof(s_szFullScreenDevice) - 1);
			s_szFullScreenDevice[sizeof(s_szFullScreenDevice) - 1] = '\0';
		}
	}

	const char* FullScreenDeviceName()
	{
		return s_szFullScreenDevice[0] ? s_szFullScreenDevice : NULL; // NULL = the primary display
	}

	// The monitor rect in virtual-screen coordinates (a secondary monitor may start at negative x/y).
	void FullScreenGetMonitorRect(HWND hWnd, RECT* prc)
	{
		if (s_szFullScreenDevice[0])
		{
			SFullScreenMonitorFind kFind;
			kFind.c_szDevice = s_szFullScreenDevice;
			SetRectEmpty(&kFind.rcMonitor);
			kFind.isFound = false;
			EnumDisplayMonitors(NULL, NULL, FullScreenMonitorEnumProc, (LPARAM) &kFind);
			if (kFind.isFound)
			{
				*prc = kFind.rcMonitor;
				return;
			}
		}

		MONITORINFO kInfo;
		kInfo.cbSize = sizeof(kInfo);
		HMONITOR hMonitor = MonitorFromWindow(hWnd, MONITOR_DEFAULTTONEAREST);
		if (hMonitor && GetMonitorInfo(hMonitor, &kInfo))
		{
			*prc = kInfo.rcMonitor;
			return;
		}

		SetRect(prc, 0, 0, GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN));
	}
}

static bool __IsFullScreenModeOn(DWORD dwWidth, DWORD dwHeight)
{
	DEVMODEA kCurrent;
	ZeroMemory(&kCurrent, sizeof(kCurrent));
	kCurrent.dmSize = sizeof(kCurrent);
	return EnumDisplaySettingsA(FullScreenDeviceName(), ENUM_CURRENT_SETTINGS, &kCurrent)
		&& kCurrent.dmPelsWidth == dwWidth && kCurrent.dmPelsHeight == dwHeight;
}

void CPythonApplication::__RestoreFullScreenDisplayMode()
{
	if (!s_isFullScreenModeChanged)
		return;

	ChangeDisplaySettingsExA(FullScreenDeviceName(), NULL, NULL, 0, NULL); // back to the registry (desktop) mode
	s_isFullScreenModeChanged = false;
}

void CPythonApplication::__PlaceFullScreenWindow(HWND hWnd, DWORD dwWidth, DWORD dwHeight, bool bShow)
{
	RECT rcMonitor;
	FullScreenGetMonitorRect(hWnd, &rcMonitor);

	const int iMonitorWidth = rcMonitor.right - rcMonitor.left;
	const int iMonitorHeight = rcMonitor.bottom - rcMonitor.top;

	// The window is always the size of the back buffer, so a mouse position is a back buffer pixel. Normally the
	// monitor now has exactly that resolution and the window covers it; if the mode change failed, the image is
	// centred on the bigger monitor (or starts at its corner on a smaller one).
	int x = rcMonitor.left;
	int y = rcMonitor.top;
	if (iMonitorWidth > (int) dwWidth)
		x += (iMonitorWidth - (int) dwWidth) / 2;
	if (iMonitorHeight > (int) dwHeight)
		y += (iMonitorHeight - (int) dwHeight) / 2;

	SetWindowPos(hWnd, HWND_TOPMOST, x, y, dwWidth, dwHeight, bShow ? SWP_SHOWWINDOW : SWP_NOACTIVATE);
}
#endif

void CPythonApplication::__SetFullScreenWindow(HWND hWnd, DWORD dwWidth, DWORD dwHeight, DWORD dwBPP)
{
#ifdef ENABLE_MT2009_BORDERLESS_FULLSCREEN
	// MT2009_PLUS_BORDERLESS_FULLSCREEN_V1: the display mode is changed only when the chosen resolution is not the
	// desktop one (no blink on start and on Alt+Tab for most players); the frequency from metin2.cfg goes with it
	// (exclusive mode used it the same way), dropped if the monitor refuses it.
	FullScreenRememberMonitor(hWnd);

	DEVMODEA kDesktopMode;
	ZeroMemory(&kDesktopMode, sizeof(kDesktopMode));
	kDesktopMode.dmSize = sizeof(kDesktopMode);
	const bool isDesktopKnown = FALSE != EnumDisplaySettingsA(FullScreenDeviceName(), ENUM_REGISTRY_SETTINGS, &kDesktopMode);

	if (isDesktopKnown && kDesktopMode.dmPelsWidth == dwWidth && kDesktopMode.dmPelsHeight == dwHeight)
	{
		__RestoreFullScreenDisplayMode();	// only if a mode of ours is still on
	}
	else if (s_isFullScreenModeChanged && __IsFullScreenModeOn(dwWidth, dwHeight))
	{
		// our mode is still on (the first activation right after Create) - no second change, no device loss
	}
	else
	{
		DEVMODEA kMode;
		ZeroMemory(&kMode, sizeof(kMode));
		kMode.dmSize = sizeof(kMode);
		kMode.dmBitsPerPel = dwBPP;
		kMode.dmPelsWidth = dwWidth;
		kMode.dmPelsHeight = dwHeight;
		kMode.dmFields = DM_BITSPERPEL | DM_PELSWIDTH | DM_PELSHEIGHT;

		const DWORD dwFrequency = m_pySystem.GetFrequency();
		if (dwFrequency > 0)
		{
			kMode.dmDisplayFrequency = dwFrequency;
			kMode.dmFields |= DM_DISPLAYFREQUENCY;
		}

		LONG lError = ChangeDisplaySettingsExA(FullScreenDeviceName(), &kMode, NULL, CDS_FULLSCREEN, NULL);
		if (DISP_CHANGE_SUCCESSFUL != lError && (kMode.dmFields & DM_DISPLAYFREQUENCY))
		{
			kMode.dmFields &= ~DM_DISPLAYFREQUENCY;
			lError = ChangeDisplaySettingsExA(FullScreenDeviceName(), &kMode, NULL, CDS_FULLSCREEN, NULL);
		}

		if (DISP_CHANGE_SUCCESSFUL == lError)
		{
			s_isFullScreenModeChanged = true;
		}
		else
		{
			TraceError("FullScreen: ChangeDisplaySettingsEx %ux%u %ubpp failed (%d) - the desktop mode stays", dwWidth, dwHeight, dwBPP, lError);
			s_isFullScreenModeChanged = true;	// make sure the registry mode is put back (as the old DISP_CHANGE_RESTART case)
			__RestoreFullScreenDisplayMode();
		}
	}

	// Before the device exists (CPythonApplication::Create) the window is only placed; it is shown after CreateDevice.
	__PlaceFullScreenWindow(hWnd, dwWidth, dwHeight, IsWindowVisible(hWnd) ? true : false);
	return;
#endif

	DEVMODE DevMode;
	DevMode.dmSize = sizeof(DevMode);
	DevMode.dmBitsPerPel = dwBPP;
	DevMode.dmPelsWidth = dwWidth;
	DevMode.dmPelsHeight = dwHeight;
	DevMode.dmFields = DM_BITSPERPEL | DM_PELSWIDTH | DM_PELSHEIGHT;

	LONG Error = ChangeDisplaySettings(&DevMode, CDS_FULLSCREEN);
	if(Error == DISP_CHANGE_RESTART)
	{
		ChangeDisplaySettings(0,0);
	}
}

void CPythonApplication::__MinimizeFullScreenWindow(HWND hWnd, DWORD dwWidth, DWORD dwHeight)
{
#ifdef ENABLE_MT2009_BORDERLESS_FULLSCREEN
	// MT2009_PLUS_BORDERLESS_FULLSCREEN_V1: as before the game goes to the taskbar on Alt+Tab (a topmost window would
	// cover the other program), with the desktop resolution back if we changed it. The windowed device is lost by the
	// mode change and reset by CheckDeviceState (DEVICESTATE_NEEDS_RESET) like the exclusive one was.
	__RestoreFullScreenDisplayMode();
	SetWindowPos(hWnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
	ShowWindow(hWnd, SW_MINIMIZE);
	return;
#endif

	ChangeDisplaySettings(0, 0);
	SetWindowPos(hWnd, 0, 0, 0,
				 dwWidth,
				 dwHeight,
				 SWP_SHOWWINDOW);
	ShowWindow(hWnd, SW_MINIMIZE);
}

LRESULT CPythonApplication::WindowProcedure(HWND hWnd, UINT uiMsg, WPARAM wParam, LPARAM lParam)
{
	const int c_DoubleClickTime = 300;
	const int c_DoubleClickBox = 5;
	static int s_xDownPosition = 0;
	static int s_yDownPosition = 0;

	switch (uiMsg)
	{
		case WM_SYSCOMMAND:
			if (wParam == SC_KEYMENU) // @fixme032
				return 0;
			break;

		case WM_ACTIVATEAPP:
			{
				m_isActivateWnd = (wParam == WA_ACTIVE) || (wParam == WA_CLICKACTIVE);

				if (m_isActivateWnd)
				{
					m_SoundManager.RestoreVolume();

					//////////////////

					if (m_isWindowFullScreenEnable)
					{
#ifdef ENABLE_MT2009_BORDERLESS_FULLSCREEN
						// MT2009_PLUS_BORDERLESS_FULLSCREEN_V1: out of the taskbar first, then the mode and the topmost
						// window over the monitor (a minimised window would only get its icon moved).
						if (IsIconic(hWnd))
							ShowWindow(hWnd, SW_RESTORE);
#endif
						__SetFullScreenWindow(hWnd, m_dwWidth, m_dwHeight, m_pySystem.GetBPP());
					}
				}
				else
				{
					m_SoundManager.SaveVolume();

					//////////////////

					if (m_isWindowFullScreenEnable)
					{
						__MinimizeFullScreenWindow(hWnd, m_dwWidth, m_dwHeight);
					}
				}
			}
			break;

		case WM_INPUTLANGCHANGE:
			return CPythonIME::Instance().WMInputLanguage(hWnd, uiMsg, wParam, lParam);
			break;

		case WM_IME_STARTCOMPOSITION:
			return CPythonIME::Instance().WMStartComposition(hWnd, uiMsg, wParam, lParam);
			break;

		case WM_IME_COMPOSITION:
			return CPythonIME::Instance().WMComposition(hWnd, uiMsg, wParam, lParam);
			break;

		case WM_IME_ENDCOMPOSITION:
			return CPythonIME::Instance().WMEndComposition(hWnd, uiMsg, wParam, lParam);
			break;

		case WM_IME_NOTIFY:
			return CPythonIME::Instance().WMNotify(hWnd, uiMsg, wParam, lParam);
			break;

		case WM_IME_SETCONTEXT:
			lParam &= ~(ISC_SHOWUICOMPOSITIONWINDOW | ISC_SHOWUIALLCANDIDATEWINDOW);
			break;

		case WM_CHAR:
			return CPythonIME::Instance().WMChar(hWnd, uiMsg, wParam, lParam);
			break;

		case WM_KEYDOWN:
			OnIMEKeyDown(LOWORD(wParam));
			break;

		case WM_LBUTTONDOWN:
			SafeSetCapture();

			if (ELTimer_GetMSec() - m_dwLButtonDownTime < c_DoubleClickTime &&
				abs(LOWORD(lParam) - s_xDownPosition) < c_DoubleClickBox &&
				abs(HIWORD(lParam) - s_yDownPosition) < c_DoubleClickBox)
			{
				m_dwLButtonDownTime = 0;

				OnMouseLeftButtonDoubleClick(short(LOWORD(lParam)), short(HIWORD(lParam)));
			}
			else
			{
				m_dwLButtonDownTime = ELTimer_GetMSec();

				OnMouseLeftButtonDown(short(LOWORD(lParam)), short(HIWORD(lParam)));
			}

			s_xDownPosition = LOWORD(lParam);
			s_yDownPosition = HIWORD(lParam);
			return 0;

		case WM_LBUTTONUP:
			m_dwLButtonUpTime = ELTimer_GetMSec();

			if (hWnd == GetCapture())
			{
				SafeReleaseCapture();
				OnMouseLeftButtonUp(short(LOWORD(lParam)), short(HIWORD(lParam)));
			}
			return 0;

		case WM_MBUTTONDOWN:
			SafeSetCapture();

			UI::CWindowManager::Instance().RunMouseMiddleButtonDown(short(LOWORD(lParam)), short(HIWORD(lParam)));
//			OnMouseMiddleButtonDown(short(LOWORD(lParam)), short(HIWORD(lParam)));
			break;

		case WM_MBUTTONUP:
			if (GetCapture() == hWnd)
			{
				SafeReleaseCapture();

				UI::CWindowManager::Instance().RunMouseMiddleButtonUp(short(LOWORD(lParam)), short(HIWORD(lParam)));
//				OnMouseMiddleButtonUp(short(LOWORD(lParam)), short(HIWORD(lParam)));
			}
			break;

		case WM_RBUTTONDOWN:
			SafeSetCapture();
			OnMouseRightButtonDown(short(LOWORD(lParam)), short(HIWORD(lParam)));
			return 0;

		case WM_RBUTTONUP:
			if (hWnd == GetCapture())
			{
				SafeReleaseCapture();

				OnMouseRightButtonUp(short(LOWORD(lParam)), short(HIWORD(lParam)));
			}
			return 0;

		case WM_MOUSEWHEEL:
			if (WebBrowser_IsVisible())
			{
#ifdef ENABLE_MT2009_INGAME_BROWSER
				// MT2009_PLUS_ITEMSHOP_V3_V3: the turn over the shop scrolls the page (the focus is on the browser's host
				// window, which passes the wheel up to here); anywhere else it stays unused while a page is shown, as before.
				WebBrowser_ForwardMouseWheel(wParam, lParam);
#endif
			}
			else
			{
#ifdef ENABLE_MOUSEWHEEL_EVENT
				if (OnMouseWheelEvent(GET_WHEEL_DELTA_WPARAM(wParam)))
					break;
#endif

				OnMouseWheel(short(HIWORD(wParam)));
			}
			break;

		case WM_SIZE:
			switch (wParam)
			{
				case SIZE_RESTORED:
				case SIZE_MAXIMIZED:
#ifdef ENABLE_MT2009_BORDERLESS_FULLSCREEN
					// MT2009_PLUS_BORDERLESS_FULLSCREEN_V1: the full-screen back buffer keeps the chosen resolution (the
					// window has that size; a Reset here would also run with the D3DPOOL_DEFAULT resources alive).
					if (m_isWindowFullScreenEnable)
						break;
#endif
					{
						RECT rcWnd;
						GetClientRect(&rcWnd);

						UINT uWidth=rcWnd.right-rcWnd.left;
						UINT uHeight=rcWnd.bottom-rcWnd.left;
						m_grpDevice.ResizeBackBuffer(uWidth, uHeight);
					}
					break;
			}

			if (wParam==SIZE_MINIMIZED)
				m_isMinimizedWnd=true;
			else
				m_isMinimizedWnd=false;

			OnSizeChange(short(LOWORD(lParam)), short(HIWORD(lParam)));

			break;

		case WM_EXITSIZEMOVE:
#ifdef ENABLE_MT2009_BORDERLESS_FULLSCREEN
			if (m_isWindowFullScreenEnable)
				break; // MT2009_PLUS_BORDERLESS_FULLSCREEN_V1: see WM_SIZE
#endif
			{
				RECT rcWnd;
				GetClientRect(&rcWnd);

				UINT uWidth=rcWnd.right-rcWnd.left;
				UINT uHeight=rcWnd.bottom-rcWnd.left;
				m_grpDevice.ResizeBackBuffer(uWidth, uHeight);
				OnSizeChange(short(LOWORD(lParam)), short(HIWORD(lParam)));
			}
			break;

		case WM_SYSKEYDOWN:
			switch (LOWORD(wParam))
			{
				case VK_F10:
					break;
			}
			break;

		case WM_SYSKEYUP:
			switch(LOWORD(wParam))
			{
				case 18:
					return FALSE;
					break;
				case VK_F10:
					break;
			}
			break;

		case WM_SETCURSOR:
			if (IsActive())
			{
				if (m_bCursorVisible && CURSOR_MODE_HARDWARE == m_iCursorMode)
				{
					SetCursor((HCURSOR) m_hCurrentCursor);
					return 0;
				}
				else
				{
					SetCursor(NULL);
					return 0;
				}
			}
			break;

		case WM_CLOSE:
#ifdef _DEBUG
			PostQuitMessage(0);
#else
			RunPressExitKey();
#endif
			return 0;

		case WM_DESTROY:
			return 0;
		default:
			//Tracenf("%x msg %x", timeGetTime(), uiMsg);
			break;
	}

	return CMSApplication::WindowProcedure(hWnd, uiMsg, wParam, lParam);
}
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f

// Files shared by GameCore.top
