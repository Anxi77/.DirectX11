#include "Window.h"

Window::Window() : hwnd(nullptr) {}

Window::~Window() {
    if (hwnd) {
        DestroyWindow(hwnd);
    }
}

// Window Procedure: Process Window Messages Function
// hwnd: Window Handle that received the message
// msg: Message type (WM_CREATE, WM_DESTROY, etc.)
// wParam, lParam: Additional data passed with the message
LRESULT CALLBACK Window::WindowProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_CLOSE: // When the close button is clicked
            DestroyWindow(hwnd);
            return 0;
        case WM_DESTROY:        // When the window is destroyed
            PostQuitMessage(0); // Post a WM_QUIT message to terminate the message loop
            return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam); // Default message processing
}

bool Window::Initialize(const wchar_t *title, int width, int height) {
    // 1. Define the window class
    WNDCLASSEXW wc   = {};                       // Initialize the window class structure
    wc.cbSize        = sizeof(WNDCLASSEXW);      // Structure size
    wc.lpfnWndProc   = WindowProc;               // Specify the window procedure function
    wc.hInstance     = GetModuleHandle(nullptr); // Handle to the current program instance
    wc.lpszClassName = L"DX11WindowClass";       // Window class name

    // 2. Register the window class
    // Register the window class defined here with Windows
    if (!RegisterClassExW(&wc)) {
        return false; // Registration failed
    }

    // 3. Create the window
    hwnd =
        CreateWindowExW(0,                   // Extended window style
                        L"DX11WindowClass",  // Registered class name
                        title,               // Window title
                        WS_OVERLAPPEDWINDOW, // Default window style (Minimize/Maximize/Resizeable)
                        CW_USEDEFAULT,       // X position (Default)
                        CW_USEDEFAULT,       // Y position (Default)
                        width,               // Window width
                        height,              // Window height
                        nullptr,             // No parent window
                        nullptr,             // No menu
                        GetModuleHandle(nullptr), // Handle to the current program instance
                        nullptr);                 // No additional data

    // Check if window creation failed
    if (!hwnd) {
        return false;
    }

    // 4. Display the window on the screen
    ShowWindow(hwnd, SW_SHOW);
    return true;
}

// Process Window Messages Function
bool Window::ProcessMessages() {
    MSG msg = {};
    // PeekMessage: Check messages in the message queue
    // PM_REMOVE: Remove messages from the queue
    while (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE)) {
        if (msg.message == WM_QUIT) // When the exit message is received
        {
            return false; // Return false to terminate the program
        }
        TranslateMessage(&msg); // Convert keyboard input messages
        DispatchMessage(&msg);  // Send messages to the window procedure
    }
    return true; // Continue execution
}