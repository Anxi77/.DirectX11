#pragma once
#include "utils/stdafx.h"
#include <wrl/client.h>

using Microsoft::WRL::ComPtr;

// DirectX Graphics Management Class
// Initializes and manages the rendering pipeline and graphics resources
class Graphics {
  public:
    Graphics();
    ~Graphics();

    /*
    DirectX Initialize Function
    hwnd: Window Handle to Render
    width, height: Size of the rendering area
    */
    bool Initialize(HWND hwnd, int width, int height);

    // Frame Rendering Function
    void Render();

  private:
    // DirectX 11 core components
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> deviceContext;
    ComPtr<IDXGISwapChain> swapChain;
    ComPtr<ID3D11RenderTargetView> renderTargetView;

    // Shader related
    ComPtr<ID3D11VertexShader> vertexShader;
    ComPtr<ID3D11PixelShader> pixelShader;
    ComPtr<ID3D11InputLayout> inputLayout;

    bool LoadShaders(); // Load Shaders Function
};