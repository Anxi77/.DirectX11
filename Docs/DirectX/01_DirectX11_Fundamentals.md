# DirectX 11 Fundamentals

## Table of Contents

1. [Core Components](#core-components)
2. [Graphics Pipeline](#graphics-pipeline)
3. [DirectX 11 vs DirectX 12](#directx-11-vs-directx-12)

---

## Core Components

### 1. Device (ID3D11Device)

```cpp
ID3D11Device* device;  // GPU resource manager
```

- **Role**: Create and manage GPU resources (buffers, textures, shaders)
- **Analogy**: "Production line manager" in a factory
- **Main methods**:
  - `CreateBuffer()`: Create buffer
  - `CreateVertexShader()`: Create vertex shader
  - `CreateRenderTargetView()`: Create render target view

### 2. Device Context (ID3D11DeviceContext)

```cpp
ID3D11DeviceContext* deviceContext;  // Rendering command executor
```

- **Role**: Execute actual rendering commands
- **Analogy**: "Conductor" of an orchestra
- **Main methods**:
  - `Draw()`: Drawing commands
  - `ClearRenderTargetView()`: Clear screen
  - `IASetVertexBuffers()`: Set vertex buffer

### 3. Swap Chain (IDXGISwapChain)

```cpp
IDXGISwapChain* swapChain;  // Double buffering management
```

- **Role**: Smooth rendering without screen flickering
- **Structure**:
  - Front Buffer: Currently displayed on screen
  - Back Buffer: Drawing next frame
- **Present()**: Swap buffers (screen update)

### 4. Render Target View (ID3D11RenderTargetView)

```cpp
ID3D11RenderTargetView* renderTargetView;  // Rendering destination
```

- **Role**: Destination where GPU draws pixels
- **Analogy**: "Canvas" for drawing

---

## Graphics Pipeline

```
[3D Model Data]
     ↓
[1. Input Assembler (IA)]
  - Read vertex data
  - Assemble primitives
     ↓
[2. Vertex Shader (VS)]
  - 3D → 2D conversion
  - Space transformations (World, View, Projection)
     ↓
[3. Rasterization]
  - 3D triangles → 2D pixels
  - Interpolation
     ↓
[4. Pixel Shader (PS)]
  - Calculate each pixel color
  - Texture sampling, lighting
     ↓
[5. Output Merger (OM)]
  - Output final pixels to render target
  - Blending, depth testing
     ↓
[Screen Output]
```

### Shaders

Small programs that run on the GPU, optimized for parallel processing.

#### Vertex Shader

- **Input**: 3D vertex coordinates
- **Output**: 2D screen coordinates
- **Example**: Transformation based on camera position

#### Pixel Shader

- **Input**: Rasterized pixel information
- **Output**: Final pixel color
- **Example**: Lighting calculations, texture application

---

## Next Steps

- [Graphics Class Detailed Analysis](./02_Graphics_Class_Analysis.md)
- [Learning Roadmap](./03_Learning_Roadmap.md)
- [C++ Pointers Guide](./04_Cpp_Pointers_Guide.md)
