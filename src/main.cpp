#include "Window.h"
#include "Graphics.h"

int main()
{
    Window window;
    if (!window.Initialize(L"DirectX11 Window", 800, 600))
    {
        std::cout << "Window initialization failed\n";
        return -1;
    }

    Graphics graphics;
    if (!graphics.Initialize(window.GetHandle(), 800, 600))
    {
        std::cout << "Graphics initialization failed\n";
        return -1;
    }

    while (window.ProcessMessages())
    {
        graphics.Render();
    }

    return 0;
}