# COM Objects

## Table of Contents

- [What is COM?](#what-is-com)
- [COM in DirectX Context](#com-in-directx-context)
- [Memory Management](#memory-management)
- [Interface Querying](#interface-querying)
- [Common DirectX COM Objects](#common-directx-com-objects)
- [Best Practices](#best-practices)
- [Debugging COM Issues](#debugging-com-issues)
- [Advanced Topics](#advanced-topics)

---

## What is COM?

**Component Object Model (COM)** is Microsoft's binary-interface standard that enables inter-process communication and dynamic object creation. DirectX heavily relies on COM for managing graphics resources.

### Core COM Principles

```cpp
// Every COM object implements IUnknown
interface IUnknown {
    HRESULT QueryInterface(REFIID riid, void** ppvObject);
    ULONG AddRef();
    ULONG Release();
};
```

### Key Characteristics

- **Reference Counted**: Objects manage their own lifetime
- **Interface-Based**: Access through well-defined interfaces
- **Binary Standard**: Language-independent communication
- **Thread-Safe**: When properly implemented

---

## COM in DirectX Context

DirectX uses COM for all major graphics objects: devices, buffers, shaders, textures, etc.

### Typical DirectX COM Object Lifecycle

```cpp
// 1. Creation - Usually through factory methods
ID3D11Device* device = nullptr;
ID3D11DeviceContext* context = nullptr;
HRESULT hr = D3D11CreateDevice(
    nullptr,                    // Adapter
    D3D_DRIVER_TYPE_HARDWARE,  // Driver type
    nullptr,                   // Software rasterizer
    0,                        // Flags
    nullptr,                  // Feature levels
    0,                       // Feature levels count
    D3D11_SDK_VERSION,      // SDK version
    &device,               // Output device
    nullptr,              // Output feature level
    &context             // Output context
);

// 2. Usage - Call methods through interface
device->CreateBuffer(&bufferDesc, &initData, &vertexBuffer);

// 3. Cleanup - Release when done
if (context) context->Release();
if (device) device->Release();
```

---

## Memory Management

### Reference Counting System

Each COM object maintains an internal reference counter:

```cpp
// When you receive a COM pointer:
ID3D11Buffer* buffer = nullptr;
device->CreateBuffer(&desc, nullptr, &buffer); // RefCount = 1

// AddRef() increases reference count
buffer->AddRef(); // RefCount = 2

// Release() decreases reference count
buffer->Release(); // RefCount = 1
buffer->Release(); // RefCount = 0 → Object destroyed
buffer = nullptr;  // Always null after final Release()
```

### Smart Pointers for Automatic Management

```cpp
#include <wrl/client.h>
using Microsoft::WRL::ComPtr;

class Graphics {
private:
    ComPtr<ID3D11Device> m_device;
    ComPtr<ID3D11DeviceContext> m_context;
    ComPtr<ID3D11Buffer> m_vertexBuffer;

public:
    bool Initialize() {
        HRESULT hr = D3D11CreateDevice(
            nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, 0,
            nullptr, 0, D3D11_SDK_VERSION,
            &m_device,    // ComPtr automatically manages AddRef/Release
            nullptr,
            &m_context
        );

        return SUCCEEDED(hr);
    }

    // Destructor automatically calls Release() on all ComPtr objects
    ~Graphics() = default;
};
```

### Memory Management Rules

1. **Always Release**: Every COM pointer must be released
2. **One-to-One**: Each successful creation needs one Release()
3. **Null Check**: Always check for nullptr before Release()
4. **Set to Null**: Set pointers to nullptr after Release()

```cpp
// Correct pattern
if (m_vertexBuffer) {
    m_vertexBuffer->Release();
    m_vertexBuffer = nullptr;
}

// Even better with helper function
template<typename T>
void SafeRelease(T*& ptr) {
    if (ptr) {
        ptr->Release();
        ptr = nullptr;
    }
}

// Usage
SafeRelease(m_vertexBuffer);
SafeRelease(m_indexBuffer);
SafeRelease(m_shader);
```

---

## Interface Querying

### QueryInterface Mechanism

COM objects can implement multiple interfaces. Use `QueryInterface` to access different interfaces:

```cpp
// Get different interface from same object
ID3D11Resource* resource = nullptr;
HRESULT hr = vertexBuffer->QueryInterface(
    __uuidof(ID3D11Resource),
    (void**)&resource
);

if (SUCCEEDED(hr)) {
    // Now can use resource-specific methods
    D3D11_RESOURCE_DIMENSION dimension;
    resource->GetType(&dimension);

    resource->Release(); // Don't forget to release!
}
```

### Interface Hierarchy Example

```cpp
// DirectX interface inheritance
ID3D11DeviceChild
├── ID3D11Resource
│   ├── ID3D11Buffer
│   ├── ID3D11Texture1D
│   ├── ID3D11Texture2D
│   └── ID3D11Texture3D
├── ID3D11View
│   ├── ID3D11RenderTargetView
│   ├── ID3D11DepthStencilView
│   └── ID3D11ShaderResourceView
└── ID3D11InputLayout
```

---

## Common DirectX COM Objects

### Device Objects

```cpp
// Primary rendering device
ID3D11Device* device;
- CreateBuffer()
- CreateTexture2D()
- CreateVertexShader()
- CreatePixelShader()
- CreateInputLayout()

// Immediate rendering context
ID3D11DeviceContext* context;
- Draw()
- DrawIndexed()
- VSSetShader()
- PSSetShader()
- IASetVertexBuffers()
```

### Resource Objects

```cpp
// Vertex/Index/Constant buffers
ID3D11Buffer* buffer;
- Map() / Unmap()  // For dynamic access
- GetDesc()        // Get buffer description

// 2D Textures and render targets
ID3D11Texture2D* texture;
- GetDesc()
- Map() / Unmap()

// Shader resource views
ID3D11ShaderResourceView* srv;
- GetResource()
- GetDesc()
```

### Shader Objects

```cpp
// Compiled shaders
ID3D11VertexShader* vertexShader;
ID3D11PixelShader* pixelShader;
ID3D11ComputeShader* computeShader;

// Input layout for vertex data
ID3D11InputLayout* inputLayout;
```

---

## Best Practices

### 1. RAII Pattern Implementation

```cpp
class DirectXBuffer {
private:
    ID3D11Buffer* m_buffer;
    ID3D11Device* m_device;

public:
    DirectXBuffer(ID3D11Device* device) : m_device(device), m_buffer(nullptr) {
        if (m_device) m_device->AddRef();
    }

    ~DirectXBuffer() {
        SafeRelease(m_buffer);
        SafeRelease(m_device);
    }

    // No copy constructor/assignment (or implement properly)
    DirectXBuffer(const DirectXBuffer&) = delete;
    DirectXBuffer& operator=(const DirectXBuffer&) = delete;

    bool Create(const D3D11_BUFFER_DESC& desc) {
        HRESULT hr = m_device->CreateBuffer(&desc, nullptr, &m_buffer);
        return SUCCEEDED(hr);
    }

    ID3D11Buffer* Get() const { return m_buffer; }
};
```

### 2. Error Handling Patterns

```cpp
#define CHECK_HR(hr, msg) \
    if (FAILED(hr)) { \
        OutputDebugStringA("FAILED: " msg "\n"); \
        return false; \
    }

bool CreateResources() {
    HRESULT hr;

    // Create vertex buffer
    hr = m_device->CreateBuffer(&bufferDesc, &initData, &m_vertexBuffer);
    CHECK_HR(hr, "Failed to create vertex buffer");

    // Create input layout
    hr = m_device->CreateInputLayout(layout, numElements,
                                   vsBlob->GetBufferPointer(),
                                   vsBlob->GetBufferSize(),
                                   &m_inputLayout);
    CHECK_HR(hr, "Failed to create input layout");

    return true;
}
```

### 3. Resource Management Class

```cpp
class GraphicsResourceManager {
private:
    std::vector<IUnknown*> m_resources;

public:
    template<typename T>
    void Track(T* resource) {
        if (resource) {
            resource->AddRef();
            m_resources.push_back(resource);
        }
    }

    ~GraphicsResourceManager() {
        for (auto* resource : m_resources) {
            if (resource) {
                resource->Release();
            }
        }
        m_resources.clear();
    }
};
```

---

## Debugging COM Issues

### 1. Debug Layer

Enable D3D11 debug layer for detailed error information:

```cpp
UINT createDeviceFlags = 0;
#ifdef _DEBUG
    createDeviceFlags |= D3D11_CREATE_DEVICE_DEBUG;
#endif

HRESULT hr = D3D11CreateDevice(
    nullptr,
    D3D_DRIVER_TYPE_HARDWARE,
    nullptr,
    createDeviceFlags,  // Enable debug layer
    nullptr, 0,
    D3D11_SDK_VERSION,
    &device, nullptr, &context
);
```

### 2. Reference Counting Debugging

```cpp
#ifdef _DEBUG
class ComPtrDebug {
public:
    template<typename T>
    static void CheckRefCount(T* ptr, const char* name) {
        if (ptr) {
            ptr->AddRef();
            ULONG refCount = ptr->Release();
            char buffer[256];
            sprintf_s(buffer, "%s RefCount: %lu\n", name, refCount);
            OutputDebugStringA(buffer);
        }
    }
};

// Usage
ComPtrDebug::CheckRefCount(m_device, "Device");
ComPtrDebug::CheckRefCount(m_vertexBuffer, "VertexBuffer");
#endif
```

### 3. Memory Leak Detection

```cpp
#ifdef _DEBUG
#include <d3d11sdklayers.h>

void CheckD3D11Leaks() {
    ID3D11Debug* debugDevice = nullptr;
    HRESULT hr = m_device->QueryInterface(__uuidof(ID3D11Debug),
                                        (void**)&debugDevice);
    if (SUCCEEDED(hr)) {
        hr = debugDevice->ReportLiveDeviceObjects(D3D11_RLDO_DETAIL);
        debugDevice->Release();
    }
}
#endif
```

---

## Advanced Topics

### 1. Thread Safety Considerations

```cpp
// DirectX 11 contexts are NOT thread-safe
// Use separate deferred contexts for multi-threading
ID3D11DeviceContext* deferredContext = nullptr;
hr = device->CreateDeferredContext(0, &deferredContext);

// Record commands on worker thread
deferredContext->VSSetShader(shader, nullptr, 0);
deferredContext->Draw(vertexCount, 0);

// Finish command list
ID3D11CommandList* commandList = nullptr;
hr = deferredContext->FinishCommandList(FALSE, &commandList);

// Execute on main thread's immediate context
immediateContext->ExecuteCommandList(commandList, FALSE);
```

### 2. Custom COM Object Creation

```cpp
class CustomVertexBuffer : public ID3D11Buffer {
private:
    ULONG m_refCount;
    ID3D11Buffer* m_actualBuffer;

public:
    CustomVertexBuffer(ID3D11Buffer* buffer)
        : m_refCount(1), m_actualBuffer(buffer) {
        if (m_actualBuffer) m_actualBuffer->AddRef();
    }

    // IUnknown implementation
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID riid, void** ppvObject) override {
        if (riid == __uuidof(ID3D11Buffer) || riid == __uuidof(IUnknown)) {
            *ppvObject = this;
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }

    ULONG STDMETHODCALLTYPE AddRef() override {
        return InterlockedIncrement(&m_refCount);
    }

    ULONG STDMETHODCALLTYPE Release() override {
        ULONG count = InterlockedDecrement(&m_refCount);
        if (count == 0) {
            delete this;
        }
        return count;
    }

    // ID3D11Buffer implementation - delegate to actual buffer
    void STDMETHODCALLTYPE GetDesc(D3D11_BUFFER_DESC* pDesc) override {
        m_actualBuffer->GetDesc(pDesc);
    }

    // ... other ID3D11Buffer methods
};
```

### 3. COM Interface Factories

```cpp
template<typename T>
class ComFactory {
public:
    static HRESULT CreateInstance(IUnknown* pUnkOuter, REFIID riid, void** ppvObject) {
        if (pUnkOuter != nullptr) {
            return CLASS_E_NOAGGREGATION;
        }

        T* pObject = new(std::nothrow) T();
        if (pObject == nullptr) {
            return E_OUTOFMEMORY;
        }

        HRESULT hr = pObject->QueryInterface(riid, ppvObject);
        pObject->Release();
        return hr;
    }
};
```

---

## Common Pitfalls and Solutions

### 1. Memory Leaks

```cpp
// ❌ Wrong - Missing Release()
ID3D11Buffer* CreateBuffer() {
    ID3D11Buffer* buffer;
    device->CreateBuffer(&desc, nullptr, &buffer);
    return buffer; // Caller must remember to Release()
}

// ✅ Correct - Use ComPtr
ComPtr<ID3D11Buffer> CreateBuffer() {
    ComPtr<ID3D11Buffer> buffer;
    device->CreateBuffer(&desc, nullptr, &buffer);
    return buffer; // Automatic reference management
}
```

### 2. Double Release

```cpp
// ❌ Wrong
buffer->Release();
buffer->Release(); // Crash! Object already destroyed

// ✅ Correct
SafeRelease(buffer); // Sets to nullptr after release
SafeRelease(buffer); // Safe to call again
```

### 3. Using Released Objects

```cpp
// ❌ Wrong
buffer->Release();
buffer->GetDesc(&desc); // Undefined behavior

// ✅ Correct
buffer->GetDesc(&desc);
SafeRelease(buffer);
```

---

## Conclusion

COM objects in DirectX require careful attention to:

- **Lifetime Management**: Always balance creation with release
- **Reference Counting**: Understand when AddRef/Release are called
- **Interface Querying**: Use QueryInterface for different object aspects
- **Error Handling**: Check HRESULT values and use debug layer
- **Thread Safety**: Understand DirectX threading limitations

Mastering COM object management is crucial for robust DirectX applications. Use smart pointers (ComPtr) whenever possible, implement proper RAII patterns, and leverage the debug layer during development.

---

## Quick Reference

```cpp
// Essential COM patterns for DirectX
ComPtr<ID3D11Device> device;
ComPtr<ID3D11DeviceContext> context;

// Creation
HRESULT hr = D3D11CreateDevice(..., &device, ..., &context);

// Usage
device->CreateBuffer(&desc, nullptr, &buffer);
context->Draw(vertexCount, 0);

// Automatic cleanup when ComPtr goes out of scope
```

Remember: **Every successful COM object creation must be balanced with exactly one Release() call** - ComPtr handles this automatically!
