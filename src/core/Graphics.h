#pragma once
#include "utils/stdafx.h"

// DirectX Graphics Management Class
// Initializes and manages the rendering pipeline and graphics resources
class Graphics {
   public:
    Graphics();
    ~Graphics();

    // DirectX Initialize Function
    // hwnd: Window Handle to Render
    // width, height: Size of the rendering area
    bool Initialize(HWND hwnd, int width, int height);

    // Frame Rendering Function
    void Render();

    // Graphics Resource Cleanup Function
    void Cleanup();

   private:
    ID3D11Device *device;                     // Graphics Device: Create and manage resources
    ID3D11DeviceContext *deviceContext;       // Device Context: Execute rendering commands
    IDXGISwapChain *swapChain;                // Swap Chain: Manage double buffering
    ID3D11RenderTargetView *renderTargetView; // Render Target View: Rendering output destination

    // Shader Related Member Variables
    ID3D11VertexShader *vertexShader;
    ID3D11PixelShader *pixelShader;
    ID3D11InputLayout *inputLayout;

    bool LoadShaders(); // Load Shaders Function
};