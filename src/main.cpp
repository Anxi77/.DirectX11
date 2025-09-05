#include "core/Graphics.h"
#include "core/Window.h"

int main() {
    std::cout << "Application starting...\n";

    Window window;
    if (!window.Initialize(L"Graphics", 800, 600)) {
        std::cout << "ERROR: Window initialization failed\n";
        std::cout << "Press Enter to exit...\n";
        std::cin.get();
        return -1;
    }
    std::cout << "SUCCESS: Window created!\n";

    Graphics graphics;
    if (!graphics.Initialize(window.GetHandle(), 800, 600)) {
        std::cout << "ERROR: Graphics initialization failed\n";
        std::cout << "Press Enter to exit...\n";
        std::cin.get();
        return -1;
    }
    std::cout << "SUCCESS: Graphics initialized!\n";

    std::cout << "Starting render loop...\n";
    while (window.ProcessMessages()) {
        graphics.Render();
    }

    std::cout << "Application ending normally.\n";
    return 0;
}