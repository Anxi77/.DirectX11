# Graphics Class Analysis

## Table of Contents

1. [Class Structure](#class-structure)
2. [Initialize Function Detailed Analysis](#initialize-function-detailed-analysis)
3. [LoadShaders Function Analysis](#loadshaders-function-analysis)
4. [Render Function Analysis](#render-function-analysis)
5. [Cleanup Function](#cleanup-function)

---

## Class Structure

```cpp
class Graphics {
public:
    Graphics();
    ~Graphics();
    bool Initialize(HWND hwnd, int width, int height);
    void Render();
    void Cleanup();

private:
    // DirectX 11 core components
    ID3D11Device* device;
    ID3D11DeviceContext* deviceContext;
    IDXGISwapChain* swapChain;
    ID3D11RenderTargetView* renderTargetView;

    // Shader related
    ID3D11VertexShader* vertexShader;
    ID3D11PixelShader* pixelShader;
    ID3D11InputLayout* inputLayout;

    bool LoadShaders();
};
```

---

## Initialize Function Detailed Analysis

### 1. Swap Chain Setup Structure

```cpp
DXGI_SWAP_CHAIN_DESC swapChainDesc = {};
swapChainDesc.BufferCount = 1;                        // 1 back buffer
swapChainDesc.BufferDesc.Width = width;               // Buffer width
swapChainDesc.BufferDesc.Height = height;             // Buffer height
swapChainDesc.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM; // 32-bit color
swapChainDesc.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;  // For render target
swapChainDesc.OutputWindow = hwnd;                    // Output window
swapChainDesc.SampleDesc.Count = 1;                   // No MSAA
swapChainDesc.Windowed = TRUE;                        // Windowed mode
```

#### Pixel Format Details

- **R8G8B8A8**: 8 bits each channel (0-255)
- **UNORM**: Unsigned Normalized (0-255 → 0.0-1.0)
- **Total 32 bits**: 1 pixel = 4 bytes

### 2. Device and SwapChain Creation

```cpp
D3D11CreateDeviceAndSwapChain(
    nullptr,                    // Default adapter (GPU)
    D3D_DRIVER_TYPE_HARDWARE,   // Hardware acceleration
    nullptr,                    // No software rasterizer
    0,                          // Flags (debug etc.)
    nullptr,                    // Feature level array
    0,                          // Array size
    D3D11_SDK_VERSION,          // SDK version
    &swapChainDesc,             // Swap chain settings
    &swapChain,                 // [Output] Swap chain
    &device,                    // [Output] Device
    &featureLevel,              // [Output] Feature level
    &deviceContext              // [Output] Context
);
```

#### Parameter Meanings

| Parameter     | Purpose                     | Description                     |
| ------------- | --------------------------- | ------------------------------- |
| device        | GPU resource creation       | CreateBuffer, CreateShader etc. |
| deviceContext | Rendering command execution | Draw, Clear etc.                |
| swapChain     | Screen display              | Present to swap buffers         |

### 3. Render Target Setup

```cpp
// Get back buffer
ID3D11Texture2D* backBuffer;
swapChain->GetBuffer(0, __uuidof(ID3D11Texture2D), (void**)&backBuffer);

// Create render target view
device->CreateRenderTargetView(backBuffer, nullptr, &renderTargetView);

// Release back buffer (renderTargetView now references it)
backBuffer->Release();

// Set render target
deviceContext->OMSetRenderTargets(1, &renderTargetView, nullptr);
```

#### GetBuffer() Function Deep Dive

**Function Signature:**
```cpp
HRESULT GetBuffer(
    UINT Buffer,        // Buffer index
    REFIID riid,        // Interface ID
    void **ppSurface    // Output pointer
);
```

**Parameter Analysis:**

| Parameter | Value | Purpose | Details |
|-----------|--------|---------|---------|
| `0` | Buffer Index | First back buffer | 0=primary, 1=secondary (triple buffering) |
| `__uuidof(ID3D11Texture2D)` | COM Interface UUID | Return type specification | Tells DirectX which interface to return |
| `(void**)&backBuffer` | Double pointer | Output parameter | COM standard for interface returns |

**Why Double Pointer (void**)?**

```cpp
// COM Interface Return Pattern
ID3D11Texture2D* backBuffer = nullptr;  // 1. Declare pointer variable

// 2. Function needs to modify the pointer itself
//    &backBuffer = address of pointer variable  
//    (void**) = cast to COM standard type
swapChain->GetBuffer(0, __uuidof(ID3D11Texture2D), (void**)&backBuffer);

// 3. Now backBuffer points to actual texture object
```

**UUID Mechanism:**
```cpp
// COM objects can implement multiple interfaces
// UUID specifies exactly which interface you want

__uuidof(ID3D11Texture2D)     // 2D Texture interface
__uuidof(ID3D11Resource)      // Generic resource interface  
__uuidof(IUnknown)            // Base COM interface

// Each UUID is a unique 128-bit identifier like:
// {6f15aaf2-d208-4e89-9ab4-489535d34f9c}
```

**Swap Chain Buffer Structure:**
```cpp
// Double Buffering (BufferCount = 1)
Front Buffer (Display) ←→ Back Buffer (Render Target)
         ↑                      ↑
    Present()              GetBuffer(0)

// Triple Buffering (BufferCount = 2)  
Front → Back Buffer 0 → Back Buffer 1
              ↑              ↑
        GetBuffer(0)   GetBuffer(1)
```

**Memory Management Chain:**
```cpp
// Reference counting in action
swapChain->GetBuffer(...)                    // RefCount = 1 (we hold reference)
device->CreateRenderTargetView(backBuffer, ...) // RefCount = 2 (RTV also references)
backBuffer->Release()                        // RefCount = 1 (we release our reference)

// When RTV is destroyed later, RefCount = 0, actual memory freed
```

**Common Errors and Solutions:**
```cpp
// ❌ Wrong - Missing cast
swapChain->GetBuffer(0, __uuidof(ID3D11Texture2D), &backBuffer);

// ❌ Wrong - Wrong interface type
swapChain->GetBuffer(0, __uuidof(ID3D11Buffer), (void**)&backBuffer);

// ❌ Wrong - Forgetting to Release
backBuffer->Release(); // THIS IS CRITICAL - prevents memory leaks

// ✅ Correct - Full pattern
ID3D11Texture2D* backBuffer;
swapChain->GetBuffer(0, __uuidof(ID3D11Texture2D), (void**)&backBuffer);
device->CreateRenderTargetView(backBuffer, nullptr, &renderTargetView);
backBuffer->Release(); // Always release temporary references
```

### 4. Viewport Setup

```cpp
D3D11_VIEWPORT viewport = {};
viewport.Width = (float)width;    // Rendering area width
viewport.Height = (float)height;   // Rendering area height
viewport.MinDepth = 0.0f;         // Minimum depth (closest)
viewport.MaxDepth = 1.0f;         // Maximum depth (farthest)

deviceContext->RSSetViewports(1, &viewport);
```

---

## LoadShaders Function Analysis

### 1. Shader File Search

```cpp
std::wstring shaderPath = L"shaders/";
WIN32_FIND_DATAW findData;
HANDLE hFind = FindFirstFileW((shaderPath + L"*.cso").c_str(), &findData);
```

### 2. Compiled Shader Loading

```cpp
// Load Vertex Shader
std::vector<char> vsData;
//Vertex Shader File
FILE* vsFile = nullptr;
_wfopen_s(&vsFile, (shaderPath + L"BasicVS.cso").c_str(), L"rb");

if (vsFile) {
    fseek(vsFile, 0, SEEK_END);      // Go to end of file
    vsData.resize(ftell(vsFile));     // Set vector size to file size
    fseek(vsFile, 0, SEEK_SET);       // Go to beginning of file
    fread(vsData.data(), 1, vsData.size(), vsFile);  // Read data
    fclose(vsFile);
}
```

### 3. Shader Creation

```cpp
// Create Vertex Shader
device->CreateVertexShader(
    vsData.data(),    // Shader bytecode
    vsData.size(),    // Bytecode size
    nullptr,          // Class linkage
    &vertexShader     // [Output] Shader object
);
```

### 4. Input Layout Creation

```cpp
D3D11_INPUT_ELEMENT_DESC layout[] = {
    {"POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D11_INPUT_PER_VERTEX_DATA, 0},
    {"COLOR", 0, DXGI_FORMAT_R32G32B32A32_FLOAT, 0, 12, D3D11_INPUT_PER_VERTEX_DATA, 0}
};

device->CreateInputLayout(
    layout,           // Layout array
    2,                // Element count
    vsData.data(),    // Shader bytecode
    vsData.size(),    // Bytecode size
    &inputLayout      // [Output] Layout object
);
```

#### Input Layout Structure Description

| Field   | POSITION          | COLOR             |
| ------- | ----------------- | ----------------- |
| Format  | float3 (12 bytes) | float4 (16 bytes) |
| Offset  | 0                 | 12                |
| Purpose | 3D coordinates    | RGBA color        |

---

## Render Function Analysis

### 1. Clear Screen

```cpp
float clearColor[4] = {0.0f, 0.0f, 0.0f, 1.0f};  // Black color
deviceContext->ClearRenderTargetView(renderTargetView, clearColor);
```

### 2. Vertex Data Preparation

```cpp
float point[] = {0.0f, 0.0f, 0.0f};  // Screen center point

D3D11_BUFFER_DESC bufferDesc = {};
bufferDesc.Usage = D3D11_USAGE_DEFAULT;
bufferDesc.ByteWidth = sizeof(point);
bufferDesc.BindFlags = D3D11_BIND_VERTEX_BUFFER;

D3D11_SUBRESOURCE_DATA initData = {};
initData.pSysMem = point;

ID3D11Buffer* vertexBuffer;
device->CreateBuffer(&bufferDesc, &initData, &vertexBuffer);
```

### 3. Pipeline Setup

```cpp
// Set vertex buffer
UINT stride = sizeof(float) * 3;
UINT offset = 0;
deviceContext->IASetVertexBuffers(0, 1, &vertexBuffer, &stride, &offset);

// Set primitive type
deviceContext->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_POINTLIST);

// Set shaders
deviceContext->VSSetShader(vertexShader, nullptr, 0);
deviceContext->PSSetShader(pixelShader, nullptr, 0);
```

### 4. Draw and Present

```cpp
// Draw 1 vertex
deviceContext->Draw(1, 0);

// Release buffer
vertexBuffer->Release();

// Present to screen (VSync enabled)
swapChain->Present(1, 0);
```

---

## Cleanup Function

### COM Object Release Rules

```cpp
void Graphics::Cleanup() {
    // Release shaders
    if (vertexShader) vertexShader->Release();
    if (pixelShader) pixelShader->Release();

    // Release render target
    if (renderTargetView) renderTargetView->Release();

    // Release swap chain
    if (swapChain) swapChain->Release();

    // Release context and device
    if (deviceContext) deviceContext->Release();
    if (device) device->Release();

    // Initialize pointers
    device = nullptr;
    deviceContext = nullptr;
    // ...
}
```

### Release Order Importance

1. Release objects that use resources first
2. Release device that created resources last
3. Initialize to nullptr to prevent dangling pointers

---

## Next Steps

- [Learning Roadmap](./03_Learning_Roadmap.md)
- [C++ Pointers Guide](./04_Cpp_Pointers_Guide.md)
- [Project Extension Guide](./05_Project_Extension.md)
