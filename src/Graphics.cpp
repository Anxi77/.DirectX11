#include "Graphics.h"

Graphics::Graphics() : device(nullptr),
                       deviceContext(nullptr),
                       swapChain(nullptr),
                       renderTargetView(nullptr)
{
}

Graphics::~Graphics()
{
    Cleanup();
}

bool Graphics::Initialize(HWND hwnd, int width, int height)
{
    DXGI_SWAP_CHAIN_DESC swapChainDesc = {};
    swapChainDesc.BufferCount = 1;
    swapChainDesc.BufferDesc.Width = width;
    swapChainDesc.BufferDesc.Height = height;
    swapChainDesc.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    swapChainDesc.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    swapChainDesc.OutputWindow = hwnd;
    swapChainDesc.SampleDesc.Count = 1;
    swapChainDesc.Windowed = TRUE;

    D3D_FEATURE_LEVEL featureLevel;
    HRESULT hr = D3D11CreateDeviceAndSwapChain(
        nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, 0,
        nullptr, 0, D3D11_SDK_VERSION,
        &swapChainDesc, &swapChain, &device,
        &featureLevel, &deviceContext);

    if (FAILED(hr))
    {
        return false;
    }

    ID3D11Texture2D *backBuffer;
    swapChain->GetBuffer(0, __uuidof(ID3D11Texture2D), (void **)&backBuffer);
    device->CreateRenderTargetView(backBuffer, nullptr, &renderTargetView);
    backBuffer->Release();

    deviceContext->OMSetRenderTargets(1, &renderTargetView, nullptr);

    D3D11_VIEWPORT viewport = {};
    viewport.Width = (float)width;
    viewport.Height = (float)height;
    viewport.MinDepth = 0.0f;
    viewport.MaxDepth = 1.0f;
    deviceContext->RSSetViewports(1, &viewport);

    return true;
}

void Graphics::Render()
{
    float clearColor[4] = {0.0f, 0.0f, 0.0f, 1.0f};
    deviceContext->ClearRenderTargetView(renderTargetView, clearColor);

    // 여기에 점과 선을 그리는 코드가 들어갈 예정

    swapChain->Present(1, 0);
}

void Graphics::Cleanup()
{
    if (renderTargetView)
        renderTargetView->Release();
    if (swapChain)
        swapChain->Release();
    if (deviceContext)
        deviceContext->Release();
    if (device)
        device->Release();

    renderTargetView = nullptr;
    swapChain = nullptr;
    deviceContext = nullptr;
    device = nullptr;
}