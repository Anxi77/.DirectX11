#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d11.h>
#include <iostream>

// Window Procedure
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam)
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

int main()
{
    // Register window class
    WNDCLASSEXW wc = {};
    wc.cbSize = sizeof(WNDCLASSEXW);
    wc.lpfnWndProc = WndProc;
    wc.hInstance = GetModuleHandle(nullptr);
    wc.lpszClassName = L"DX11WindowClass";

    if (!RegisterClassExW(&wc))
    {
        std::cout << "Window registration failed\n";
        return -1;
    }

    // Create window
    HWND hwnd = CreateWindowExW(
        0,                            // Optional window styles
        L"DX11WindowClass",           // Window class
        L"DirectX11 Window",          // Window text
        WS_OVERLAPPEDWINDOW,          // Window style
        CW_USEDEFAULT, CW_USEDEFAULT, // Position
        800, 600,                     // Size
        nullptr,                      // Parent window
        nullptr,                      // Menu
        GetModuleHandle(nullptr),     // Instance handle
        nullptr                       // Additional data
    );

    if (!hwnd)
    {
        std::cout << "Window creation failed\n";
        return -1;
    }

    // Show window
    ShowWindow(hwnd, SW_SHOW);

    // Message loop
    MSG msg = {};
    while (GetMessage(&msg, nullptr, 0, 0))
    {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return 0;
}