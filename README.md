<div align="center">

![header](https://capsule-render.vercel.app/api?type=transparent&color=39FF14&height=150&section=header&text=DirectX%2011%20Engine&fontSize=70&animation=fadeIn&fontColor=39FF14&desc=Complete%20Learning%20Journey%20from%20Fundamentals%20to%20Ray%20Tracing&descSize=20&descAlignY=75)

# DirectX 11 Graphics Engine Learning Project

A comprehensive graphics engine project for learning DirectX 11, 3D mathematics, and advanced rendering techniques.

## 🎯 Current Status & Progress

<p align="center">
  <img src="https://img.shields.io/badge/Phase_1-Fundamentals-39FF14?style=for-the-badge&logo=directx&logoColor=white"/>
  <img src="https://img.shields.io/badge/Point_Rendering-✅_Complete-00AA00?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Next_Goal-Triangle_Rendering-FF8C00?style=for-the-badge"/>
</p>

### ✅ Completed

#### DirectX 11 pipeline setup and initialization
#### Window management system with Win32 integration
#### HLSL shader loading and compilation system
#### Basic point rendering implementation
#### CMake build system with automated shader compilation

### 🎯 Currently Working On

#### Triangle rendering with vertex buffers
#### Color system integration (vertex colors)
#### Multiple primitive rendering

### 🚀 Quick Start

```bash
# Build and run
cmake -B build -G Ninja
cmake --build build
./bin/DirectX11_Render.exe
```

</div>

---

## 📚 Complete Learning Journey

This project follows a structured 6-phase learning path designed to take you from DirectX basics to advanced ray tracing techniques.

```
[Phase 1: Fundamentals] → [Phase 2: 3D Math] → [Phase 3: Lighting] → [Phase 4: Texturing] → [Phase 5: Advanced] → [Phase 6: Ray Tracing]
```

<details>
<summary><strong>📖 Phase 1: Building Fundamentals</strong> <em>(Current Phase - 70% Complete)</em></summary>
<div align="left">

### Learning Goals

- Master vertex buffers and input layouts
- Understand primitive types (POINTLIST, TRIANGLELIST, TRIANGLESTRIP)
- Implement basic shader pipeline

### Current Progress

- [x] Point rendering implementation ✅
- [x] Basic pipeline setup ✅
- [x] Shader loading system ✅
- [x] Triangle rendering ✅
- [x] Vertex color system ✅
- [ ] Multiple object rendering with index buffers

### Key Implementation

```cpp
// Next: Triangle vertices with colors
struct Vertex {
    DirectX::XMFLOAT3 position;
    DirectX::XMFLOAT4 color;
};

float triangle[] = {
    -0.5f, -0.5f, 0.0f,  // Bottom left
     0.5f, -0.5f, 0.0f,  // Bottom right
     0.0f,  0.5f, 0.0f   // Top
};
```

</div>
</details>

<details>
<summary><strong>🎲 Phase 2: 3D Transformations and Camera</strong> <em>(Upcoming)</em></summary>
<div align="left">

### Core Concepts

- **World Matrix**: Object position, rotation, scale transformations
- **View Matrix**: Camera position and direction handling
- **Projection Matrix**: 3D to 2D projection mathematics

### Implementation Goals

- [ ] Constant buffer system for matrix data
- [ ] Camera class with view matrix generation
- [ ] 3D cube rendering with depth buffer
- [ ] Transformation animations (rotating objects, camera movement)

### Required Components

```cpp
struct MatrixBuffer {
    DirectX::XMMATRIX world;
    DirectX::XMMATRIX view;
    DirectX::XMMATRIX projection;
};

class Camera {
    DirectX::XMFLOAT3 position;
    DirectX::XMFLOAT3 target;
    DirectX::XMFLOAT3 up;
    DirectX::XMMATRIX GetViewMatrix();
};
```

</div>
</details>

<details>
<summary><strong>💡 Phase 3: Lighting and Materials</strong> <em>(Planned)</em></summary>
<div align="left">

### Phong Lighting Model Implementation

- **Ambient Light**: Base illumination level
- **Diffuse Light**: Surface angle-dependent lighting
- **Specular Light**: Reflection-based highlights

### Advanced Features

- Multiple light source types (Directional, Point, Spot)
- Material system with ambient/diffuse/specular properties
- Normal mapping with tangent space calculations

### HLSL Implementation Preview

```hlsl
// Pixel Shader lighting calculation
float3 lightDir = normalize(lightPos - worldPos);
float diffuse = max(dot(normal, lightDir), 0.0);
float3 finalColor = baseColor * (ambient + diffuse);
```

</div>
</details>

<details>
<summary><strong>🎨 Phase 4: Texturing</strong> <em>(Future)</em></summary>
<div align="left">

### Texture Pipeline

- WIC texture loading system
- Sampler state configuration
- UV mapping and coordinate systems
- Multi-texturing (Diffuse, Normal, Specular maps)

### Advanced Techniques

- Cube mapping for environment reflections
- Mipmap generation and usage
- Texture atlasing and optimization

</div>
</details>

<details>
<summary><strong>⚡ Phase 5: Advanced Rendering</strong> <em>(Advanced)</em></summary>
<div align="left">

### Major Features

- **Shadow Mapping**: Real-time shadow generation with PCF
- **Post Processing**: Bloom, tone mapping, FXAA anti-aliasing
- **Deferred Rendering**: G-buffer implementation for complex scenes
- **SSAO**: Screen space ambient occlusion for realistic depth

</div>
</details>

<details>
<summary><strong>🌟 Phase 6: Ray Tracing</strong> <em>(Expert Level)</em></summary>
<div align="left">

### Ray Tracing Fundamentals

- Ray-triangle intersection algorithms
- Recursive ray tracing for reflections/refractions
- Compute shader implementation

### Advanced Ray Tracing

- BVH acceleration structures
- Path tracing with Monte Carlo methods
- Real-time optimization and denoising

```hlsl
[numthreads(8, 8, 1)]
void RaytraceCS(uint3 id : SV_DispatchThreadID) {
    Ray ray = GenerateRay(id.xy);
    float3 color = Trace(ray);
    output[id.xy] = float4(color, 1.0);
}
```

</div>
</details>

---

## 📖 Documentation Library

<p align="center">
  <img src="https://img.shields.io/badge/Documentation-Complete_Guides-4A90E2?style=for-the-badge&logo=gitbook&logoColor=white"/>
  <img src="https://img.shields.io/badge/Analysis-Code_Deep_Dive-E85D75?style=for-the-badge&logo=microscope&logoColor=white"/>
  <img src="https://img.shields.io/badge/Reference-C++_DirectX-9B59B6?style=for-the-badge&logo=cplusplus&logoColor=white"/>
</p>

### 📋 Complete Learning Documents

- **[DirectX 11 Fundamentals](./Docs/DirectX/01_DirectX11_Fundamentals.md)** - Core concepts, graphics pipeline, DirectX vs OpenGL comparison
- **[Graphics Class Analysis](./Docs/DirectX/02_Graphics_Class_Analysis.md)** - Line-by-line code analysis of rendering pipeline
- **[Tirangle Rendering Implementation](./Docs/DirectX/03_Triangle_Rendering.md)**

### 💡 C++ & Programming Tips

- **[Arrow Operator](./Docs/Tips/Arrow_Operator.md)** - Pointer concepts and COM object usage
- **[DirectX Objects](./Docs/Tips/Com_Objects.md)** - DirectX object management and memory handling

---

## 🛠️ Development Environment

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows_10/11-0078D4?style=for-the-badge&logo=windows&logoColor=white"/>
  <img src="https://img.shields.io/badge/Language-C++17-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white"/>
  <img src="https://img.shields.io/badge/Build-CMake_Ninja-064F8C?style=for-the-badge&logo=cmake&logoColor=white"/>
  <img src="https://img.shields.io/badge/Graphics-DirectX_11-107C10?style=for-the-badge&logo=xbox&logoColor=white"/>
</p>

### Core Technologies

- **Graphics API**: DirectX 11 with HLSL shaders
- **Build System**: CMake with Ninja generator
- **Compiler**: MSVC with Unicode support (/utf-8, /DUNICODE)
- **IDE Setup**: VS Code with clangd language server
- **Code Style**: clang-format (Google style base, 4-space indent, 100 char limit)

### Essential Commands

```bash
# Project setup
cmake -B build -G Ninja

# Build with shader compilation
cmake --build build

# Code formatting
clang-format -i src/**/*.cpp src/**/*.h

# Clean build
cmake --build build --target clean
```

### Project Structure

```
src/core/          # Engine core (Window, Graphics classes)
shaders/           # HLSL shader sources (.hlsl → .cso)
tools/             # DirectX compiler tools (dxc.exe)
bin/               # Executable and compiled shaders
Docs/              # Complete learning documentation
```

---

## 🎮 Learning Projects by Phase

### 🟢 Beginner Projects (Phase 1-2)

1. **Rotating Cube Viewer** - Basic 3D transformations
2. **Simple Solar System** - Multiple object rendering
3. **Wireframe Renderer** - Different primitive types

### 🟡 Intermediate Projects (Phase 3-4)

1. **OBJ File Viewer** - Model loading and texturing
2. **Simple Scene Editor** - Interactive 3D manipulation
3. **Material Editor** - Real-time shader parameter tuning

### 🔴 Advanced Projects (Phase 5-6)

1. **Mini Game Engine** - Complete rendering pipeline
2. **PBR Renderer** - Physically-based shading
3. **Real-time Ray Tracing Demo** - Cutting-edge techniques

---

## 📚 Learning Resources & References

### 🌐 Online Resources

<p align="center">
  <a href="https://docs.microsoft.com/en-us/windows/win32/direct3d11/"><img src="https://img.shields.io/badge/Microsoft_DirectX_11_Docs-0078D4?style=flat-square&logo=microsoft&logoColor=white"/></a>
  <a href="https://learnopengl.com/"><img src="https://img.shields.io/badge/LearnOpenGL-Similar_Concepts-E97627?style=flat-square&logo=opengl&logoColor=white"/></a>
  <a href="https://www.scratchapixel.com/"><img src="https://img.shields.io/badge/Scratchapixel-Graphics_Theory-4A90E2?style=flat-square&logo=scratchapixel&logoColor=white"/></a>
  <a href="https://developer.nvidia.com/gpugems"><img src="https://img.shields.io/badge/GPU_Gems-Advanced_Techniques-76B900?style=flat-square&logo=nvidia&logoColor=white"/></a>
</p>

### 🔧 Development Tools

- **RenderDoc** - GPU frame debugging and analysis
- **PIX** - DirectX-specific performance profiler
- **Visual Studio Graphics Debugger** - DirectX debugging integration

---

## 🚀 Success Strategy

### 📈 Learning Approach

1. **Small Incremental Goals** - Complete one concept per week
2. **Visual Feedback Focus** - Always see your progress on screen
3. **Code Quality Emphasis** - Refactor and improve as you learn
4. **Documentation Habit** - Record what you learn for reference
5. **Community Engagement** - Ask questions, share progress

### 🎯 Phase Completion Criteria

- **Visual Results**: Each phase produces something you can see
- **Code Understanding**: Can explain every line of implementation
- **Problem Solving**: Can debug and fix issues independently
- **Extension Ready**: Prepared to build upon the foundation

---

<div align="center">

**Current Focus**: Phase 1 Triangle Rendering → [Graphics Class Analysis](./Docs/DirectX/02_Graphics_Class_Analysis.md)

**Next Steps**: Complete triangle rendering, add vertex colors, prepare for 3D transformations

---

</div>
