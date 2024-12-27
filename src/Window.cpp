#include "Window.h"

Window::Window() : hwnd(nullptr)
{
}

Window::~Window()
{
    if (hwnd)
    {
        DestroyWindow(hwnd);
    }
}

LRESULT CALLBACK Window::WindowProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    switch (msg)
    {
    case WM_CLOSE:
        DestroyWindow(hwnd);
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

bool Window::Initialize(const wchar_t *title, int width, int height)
{
    WNDCLASSEXW wc = {};
    wc.cbSize = sizeof(WNDCLASSEXW);
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = GetModuleHandle(nullptr);
    wc.lpszClassName = L"DX11WindowClass";

    if (!RegisterClassExW(&wc))
    {
        return false;
    }

    hwnd = CreateWindowExW(
        0,
        L"DX11WindowClass",
        title,
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT,
        width, height,
        nullptr,
        nullptr,
        GetModuleHandle(nullptr),
        nullptr);

    if (!hwnd)
    {
        return false;
    }

    ShowWindow(hwnd, SW_SHOW);
    return true;
}

bool Window::ProcessMessages()
{
    MSG msg = {};
    while (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE))
    {
        if (msg.message == WM_QUIT)
        {
            return false;
        }
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return true;
}