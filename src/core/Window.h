#pragma once
#include "utils/stdafx.h"
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

// Window Management Class
// Create, process messages, manage window events
class Window {
   public:
    Window();
    ~Window();

    // Initialize Window Function
    // title: Window Title
    // width, height: Window Size
    bool Initialize(const wchar_t *title, int width, int height);

    // Return Window Handle
    HWND GetHandle() const {
        return hwnd;
    }

    // Process Window Messages Function
    // Returns false to terminate program
    bool ProcessMessages();

   private:
    HWND hwnd; // Window Handle

    // Window Procedure: Process Window Messages Function
    static LRESULT CALLBACK WindowProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam);
};