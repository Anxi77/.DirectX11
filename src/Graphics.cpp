#include "Graphics.h"

Graphics::Graphics() : device(nullptr),
                       deviceContext(nullptr),
                       swapChain(nullptr),
                       renderTargetView(nullptr),
                       vertexShader(nullptr),
                       pixelShader(nullptr)
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

    if (!LoadShaders())
    {
        std::cout << "Shader loading failed!\n";
        return false;
    }
    std::cout << "Shaders loaded successfully!\n";

    return true;
}

bool Graphics::LoadShaders()
{
    std::wstring shaderPath = L"shaders/";
    std::wcout << L"Looking for shaders in: " << shaderPath << std::endl;

    wchar_t currentDir[MAX_PATH];
    GetCurrentDirectoryW(MAX_PATH, currentDir);
    std::wcout << L"Current directory: " << currentDir << std::endl;

    // 디버깅을 위한 파일 존재 여부 확인
    WIN32_FIND_DATAW findData;
    HANDLE hFind = FindFirstFileW((shaderPath + L"*.cso").c_str(), &findData);
    if (hFind != INVALID_HANDLE_VALUE)
    {
        do
        {
            std::wcout << L"Found shader file: " << findData.cFileName << std::endl;
        } while (FindNextFileW(hFind, &findData));
        FindClose(hFind);
    }
    else
    {
        std::wcout << L"No shader files found in directory!" << std::endl;
    }

    std::vector<char> vsData;
    FILE *vsFile = nullptr;
    _wfopen_s(&vsFile, (shaderPath + L"BasicVS.cso").c_str(), L"rb");
    if (vsFile)
    {
        std::cout << "Found vertex shader file\n";
        fseek(vsFile, 0, SEEK_END);
        vsData.resize(ftell(vsFile));
        fseek(vsFile, 0, SEEK_SET);
        fread(vsData.data(), 1, vsData.size(), vsFile);
        fclose(vsFile);
    }
    else
    {
        std::cout << "Failed to load vertex shader!\n";
        return false;
    }

    std::vector<char> psData;
    FILE *psFile = nullptr;
    _wfopen_s(&psFile, (shaderPath + L"BasicPS.cso").c_str(), L"rb");
    if (psFile)
    {
        fseek(psFile, 0, SEEK_END);
        psData.resize(ftell(psFile));
        fseek(psFile, 0, SEEK_SET);
        fread(psData.data(), 1, psData.size(), psFile);
        fclose(psFile);
    }
    else
    {
        std::cout << "Failed to load pixel shader!\n";
        return false;
    }

    HRESULT hr = device->CreateVertexShader(
        vsData.data(), vsData.size(), nullptr, &vertexShader);
    if (FAILED(hr))
    {
        char errorMsg[256];
        sprintf_s(errorMsg, "Failed to create vertex shader! Error: 0x%08X\n", hr);
        std::cout << errorMsg;
        std::cout << "Shader size: " << vsData.size() << " bytes\n";
        
        // 입력 레이아웃 정의
        D3D11_INPUT_ELEMENT_DESC layout[] = {
            { "POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 },
            { "COLOR", 0, DXGI_FORMAT_R32G32B32A32_FLOAT, 0, 12, D3D11_INPUT_PER_VERTEX_DATA, 0 }
        };

        // 입력 레이아웃 생성 시도
        hr = device->CreateInputLayout(
            layout,
            2,
            vsData.data(),
            vsData.size(),
            &inputLayout
        );

        if (FAILED(hr))
        {
            std::cout << "Failed to create input layout! Error: 0x%08X\n" << hr << std::endl;
        }
        return false;
    }

    // 입력 레이아웃 정의 및 생성을 셰이더 생성 성공 후로 이동
    D3D11_INPUT_ELEMENT_DESC layout[] = {
        { "POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 },
        { "COLOR", 0, DXGI_FORMAT_R32G32B32A32_FLOAT, 0, 12, D3D11_INPUT_PER_VERTEX_DATA, 0 }
    };

    hr = device->CreateInputLayout(
        layout,
        2,
        vsData.data(),
        vsData.size(),
        &inputLayout
    );

    if (FAILED(hr))
    {
        std::cout << "Failed to create input layout! Error: 0x%08X\n" << hr << std::endl;
        return false;
    }

    // 입력 레이아웃 설정
    deviceContext->IASetInputLayout(inputLayout);

    hr = device->CreatePixelShader(
        psData.data(), psData.size(), nullptr, &pixelShader);
    if (FAILED(hr))
    {
        std::cout << "Failed to create pixel shader!\n";
        return false;
    }

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
    if (vertexShader)
        vertexShader->Release();
    if (pixelShader)
        pixelShader->Release();
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
    vertexShader = nullptr;
    pixelShader = nullptr;
}