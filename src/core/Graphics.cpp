#include "Graphics.h"

Graphics::Graphics() {
    // ComPtr automatically initializes to nullptr, but explicit initialization for clarity
    device           = nullptr;
    deviceContext    = nullptr;
    swapChain        = nullptr;
    renderTargetView = nullptr;
    vertexShader     = nullptr;
    pixelShader      = nullptr;
    inputLayout      = nullptr;
}

Graphics::~Graphics() {}

bool Graphics::Initialize(HWND hwnd, int width, int height) {
    std::cout << "Starting Graphics::Initialize..." << std::endl;
    // ========================================
    // 1. SWAP CHAIN CONFIGURATION
    // ========================================
    // Configure swap chain settings - this controls how frames are presented to screen
    DXGI_SWAP_CHAIN_DESC swapChainDesc = {};
    swapChainDesc.BufferCount          = 1;      // Single back buffer (double buffering)
    swapChainDesc.BufferDesc.Width     = width;  // Render target width
    swapChainDesc.BufferDesc.Height    = height; // Render target height
    swapChainDesc.BufferDesc.Format =
        DXGI_FORMAT_R8G8B8A8_UNORM; // 32-bit RGBA format (8 bits per channel)
    swapChainDesc.BufferUsage =
        DXGI_USAGE_RENDER_TARGET_OUTPUT;   // Buffer will be used as render target
    swapChainDesc.OutputWindow     = hwnd; // Target window handle
    swapChainDesc.SampleDesc.Count = 1;    // No multisampling (anti-aliasing)
    swapChainDesc.Windowed         = TRUE; // Windowed mode (not fullscreen)

    // ========================================
    // 2. CREATE DIRECTX DEVICE AND SWAP CHAIN
    // ========================================
    // This is the core DirectX initialization - creates the main rendering device and swap chain
    D3D_FEATURE_LEVEL featureLevel;
    HRESULT hr = D3D11CreateDeviceAndSwapChain(
        nullptr,                     // Default adapter (GPU)
        D3D_DRIVER_TYPE_HARDWARE,    // Hardware acceleration
        nullptr,                     // No software rasterizer
        0,                           // Flags (debug etc.)
        nullptr,                     // Feature level array
        0,                           // Array size
        D3D11_SDK_VERSION,           // SDK version
        &swapChainDesc,              // Swap chain settings
        swapChain.GetAddressOf(),    // [Output] Swap chain - ComPtr output
        device.GetAddressOf(),       // [Output] Device - ComPtr output
        &featureLevel,               // [Output] Feature level
        deviceContext.GetAddressOf() // [Output] Context - ComPtr output
    );

    // Check if DirectX initialization succeeded
    if (FAILED(hr)) {
        std::cout << "ERROR: D3D11CreateDeviceAndSwapChain failed! HRESULT: 0x" << std::hex << hr
                  << std::endl;
        MessageBox(hwnd, L"Failed to create Device/SwapChain", L"Error", MB_OK);
        return false;
    }
    std::cout << "SUCCESS: DirectX device and swap chain created!\n";

    // Debug: Check if device is really created properly
    std::cout << "Device pointer: " << device.Get() << std::endl;
    std::cout << "DeviceContext pointer: " << deviceContext.Get() << std::endl;
    std::cout << "SwapChain pointer: " << swapChain.Get() << std::endl;

    // ========================================
    // 3. CREATE RENDER TARGET VIEW
    // ========================================
    // Get the back buffer texture from swap chain and create a render target view
    // This is where all rendering operations will draw to
    ComPtr<ID3D11Texture2D> backBuffer;

    // GetBuffer() extracts the actual texture from swap chain for rendering
    // Parameters breakdown:
    // - 0: Buffer index (0 = primary back buffer, 1 = secondary for triple buffering)
    // - __uuidof(ID3D11Texture2D): COM interface UUID to specify return type
    //   This tells DirectX "I want this buffer as a 2D texture interface"
    // - backBuffer.GetAddressOf(): ComPtr output parameter
    //   ComPtr handles COM interface returns automatically
    swapChain->GetBuffer(0,
                         __uuidof(ID3D11Texture2D),
                         reinterpret_cast<void**>(backBuffer.GetAddressOf()));

    // Create a render target view from the back buffer texture
    // This "view" allows the graphics pipeline to render into the texture
    // nullptr = use default render target view description
    // backBuffer.Get() = get raw pointer for input parameter
    device->CreateRenderTargetView(backBuffer.Get(), nullptr, renderTargetView.GetAddressOf());

    // NOTE: No manual Release() needed - ComPtr automatically manages reference counting
    // backBuffer will be automatically released when it goes out of scope

    // ========================================
    // 4. BIND RENDER TARGET
    // ========================================
    // Tell DirectX to use our render target view for all drawing operations
    // OM = Output Merger stage (final stage of graphics pipeline)
    // renderTargetView.GetAddressOf() gets pointer to the ComPtr for array input
    deviceContext->OMSetRenderTargets(1, renderTargetView.GetAddressOf(), nullptr);
    std::cout << "SUCCESS: Render target bound!\n";

    // ========================================
    // 5. SETUP VIEWPORT
    // ========================================
    // Define the screen area where rendering will occur (coordinate transformation)
    D3D11_VIEWPORT viewport = {};
    viewport.Width          = (float)width;      // Viewport width in pixels
    viewport.Height         = (float)height;     // Viewport height in pixels
    viewport.MinDepth       = 0.0f;              // Minimum depth value (near plane)
    viewport.MaxDepth       = 1.0f;              // Maximum depth value (far plane)
    deviceContext->RSSetViewports(1, &viewport); // RS = Rasterizer Stage

    // ========================================
    // 6. LOAD AND COMPILE SHADERS
    // ========================================
    // Load vertex and pixel shaders from compiled .cso files
    std::cout << "Starting shader loading...\n";
    if (!LoadShaders()) {
        std::cout << "ERROR: Shader loading failed!\n";
        return false;
    }
    std::cout << "SUCCESS: Shaders loaded successfully!\n";

    return true;
}

bool Graphics::LoadShaders() {
    // ========================================================================
    // DIRECTX 11 SHADER LOADING AND COMPILATION PIPELINE
    // ========================================================================
    // This function demonstrates the complete process of loading compiled shaders
    // and setting up the graphics pipeline for rendering operations.
    //
    // KEY CONCEPTS COVERED:
    // 1. Compiled Shader Objects (.cso files) - Pre-compiled HLSL bytecode
    // 2. Vertex Shaders - Transform vertices from model to screen space
    // 3. Pixel Shaders - Calculate final pixel colors for rendering
    // 4. Input Layouts - Define vertex data structure and attributes
    // 5. DirectX Resource Management - Creating and binding GPU resources
    // ========================================================================

    // ========================================
    // 1. SHADER FILE DISCOVERY AND VALIDATION
    // ========================================
    // Define the directory path where compiled shader files (.cso) are located
    // .cso = Compiled Shader Object - these are HLSL shaders pre-compiled to bytecode
    std::wstring shaderPath = L"shaders/";

    std::wcout << L"Looking for shaders in: " << shaderPath << std::endl;

    // Debug output: Show current working directory for troubleshooting
    // This helps verify we're looking in the right location for shader files
    wchar_t currentDir[MAX_PATH];
    GetCurrentDirectoryW(MAX_PATH, currentDir);
    std::wcout << L"Current directory: " << currentDir << std::endl;

    // File system enumeration: Search for all .cso files in the shader directory
    // This is primarily for debugging - helps verify shader files exist before loading
    WIN32_FIND_DATAW findData;
    HANDLE hFind = FindFirstFileW((shaderPath + L"*.cso").c_str(), &findData);
    if (hFind != INVALID_HANDLE_VALUE) {
        do {
            std::wcout << L"Found shader file: " << findData.cFileName << std::endl;
        } while (FindNextFileW(hFind, &findData));
        FindClose(hFind);
    } else {
        std::wcout << L"No shader files found in directory!" << std::endl;
    }

    // ========================================
    // 2. VERTEX SHADER LOADING AND CREATION
    // ========================================
    // Vertex shaders are the first programmable stage in the graphics pipeline
    // They transform vertex positions, apply transformations, and prepare data for rasterization

    // Binary file loading: Read the compiled vertex shader bytecode from disk
    // Use binary mode ("rb") because .cso files contain compiled bytecode, not text
    std::vector<char> vsData; // Vector to hold vertex shader bytecode
    FILE* vsFile = nullptr;
    _wfopen_s(&vsFile, (shaderPath + L"BasicVS.cso").c_str(), L"rb");

    if (vsFile) {
        std::cout << "Found vertex shader file\n";

        // File size calculation: Determine the size of the shader bytecode
        // This is necessary for memory allocation and DirectX buffer creation
        fseek(vsFile, 0, SEEK_END);   // Move to end of file
        vsData.resize(ftell(vsFile)); // Resize vector to file size
        fseek(vsFile, 0, SEEK_SET);   // Return to beginning of file

        // Binary data loading: Read the entire shader bytecode into memory
        // fread() loads the raw bytecode that DirectX will use to create the shader
        fread(vsData.data(), 1, vsData.size(), vsFile);
        fclose(vsFile);
    } else {
        std::cout << "Failed to load vertex shader!\n";
        return false; // Early return if vertex shader loading fails
    }

    // ========================================
    // 3. PIXEL SHADER LOADING AND CREATION
    // ========================================
    // Pixel shaders (also called fragment shaders) run for each pixel/fragment
    // They calculate the final color that appears on screen for each pixel
    // Binary file loading: Read the compiled pixel shader bytecode from disk
    // Similar process to vertex shader loading - binary mode for bytecode
    std::vector<char> psData; // Vector to hold pixel shader bytecode
    FILE* psFile = nullptr;
    _wfopen_s(&psFile, (shaderPath + L"BasicPS.cso").c_str(), L"rb");

    if (psFile) {
        // File size calculation and binary data loading (same pattern as vertex shader)
        fseek(psFile, 0, SEEK_END);
        psData.resize(ftell(psFile));
        fseek(psFile, 0, SEEK_SET);
        fread(psData.data(), 1, psData.size(), psFile);
        fclose(psFile);
    } else {
        std::cout << "Failed to load pixel shader!\n";
        return false; // Early return if pixel shader loading fails
    }

    // ========================================
    // 4. DIRECTX VERTEX SHADER OBJECT CREATION
    // ========================================
    // Convert the loaded bytecode into a DirectX vertex shader object
    // This creates a GPU resource that can be bound to the graphics pipeline

    // CreateVertexShader() parameters breakdown:
    // - vsData.data(): Pointer to the vertex shader bytecode
    // - vsData.size(): Size of the bytecode in bytes
    // - nullptr: No class linkage interface (advanced feature, not needed here)
    // - vertexShader.GetAddressOf(): Output parameter - receives the created shader
    HRESULT hr = device->CreateVertexShader(vsData.data(),
                                            vsData.size(),
                                            nullptr,
                                            vertexShader.GetAddressOf());

    // Error handling: Check if vertex shader creation succeeded
    // FAILED() macro checks if HRESULT indicates an error condition
    if (FAILED(hr)) {
        char errorMsg[256];
        sprintf_s(errorMsg, "Failed to create vertex shader! Error: 0x%08X\n", hr);
        std::cout << errorMsg;
        std::cout << "Shader size: " << vsData.size() << " bytes\n";
        return false;
    }

    // ========================================
    // 5. INPUT LAYOUT DEFINITION AND CREATION
    // ========================================
    // Input layouts define how vertex data is structured and interpreted by shaders
    // They create a contract between your vertex buffer format and shader expectations
    // This is critical for the Input Assembler stage of the graphics pipeline

    // Vertex attribute description: Define the structure of vertex data
    // Each D3D11_INPUT_ELEMENT_DESC describes one attribute (position, color, etc.)
    D3D11_INPUT_ELEMENT_DESC layout[] = {
        // POSITION attribute (first 3 floats of each vertex)
        // - "POSITION": Semantic name that matches the shader input
        // - 0: Semantic index (for multiple attributes of same type)
        // - DXGI_FORMAT_R32G32B32_FLOAT: 3 32-bit floats (x, y, z coordinates)
        // - 0: Input slot (which vertex buffer stream)
        // - 0: Byte offset from start of vertex (position comes first)
        // - D3D11_INPUT_PER_VERTEX_DATA: Data changes per vertex (not per instance)
        // - 0: Instance data step rate (not used for per-vertex data)
        {"POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D11_INPUT_PER_VERTEX_DATA, 0},

        // COLOR attribute (next 4 floats of each vertex)
        // - "COLOR": Semantic name that matches the shader input
        // - DXGI_FORMAT_R32G32B32A32_FLOAT: 4 32-bit floats (r, g, b, a values)
        // - 12: Byte offset (3 position floats × 4 bytes = 12 bytes offset)
        {"COLOR", 0, DXGI_FORMAT_R32G32B32A32_FLOAT, 0, 12, D3D11_INPUT_PER_VERTEX_DATA, 0}};

    // Create the input layout object using the vertex shader bytecode
    // The input layout must be created using the same shader bytecode that will use it
    // This ensures compatibility between vertex data format and shader expectations
    hr = device->CreateInputLayout(layout,        // Array of input element descriptions
                                   2,             // Number of elements in the array
                                   vsData.data(), // Vertex shader bytecode for validation
                                   vsData.size(), // Size of vertex shader bytecode
                                   inputLayout.GetAddressOf()); // Output parameter

    // Error handling: Verify input layout creation succeeded
    if (FAILED(hr)) {
        std::cout << "Failed to create input layout! Error: 0x" << std::hex << hr << std::endl;
        return false;
    }

    // ========================================
    // 6. DIRECTX PIXEL SHADER OBJECT CREATION
    // ========================================
    // Convert the loaded pixel shader bytecode into a DirectX pixel shader object
    // This creates the final GPU resource needed for pixel/fragment processing

    // CreatePixelShader() parameters (similar to vertex shader):
    // - psData.data(): Pointer to the pixel shader bytecode
    // - psData.size(): Size of the bytecode in bytes
    // - nullptr: No class linkage interface needed
    // - pixelShader.GetAddressOf(): Output parameter for the created shader
    hr = device->CreatePixelShader(psData.data(),
                                   psData.size(),
                                   nullptr,
                                   pixelShader.GetAddressOf());

    // Error handling: Check if pixel shader creation succeeded
    if (FAILED(hr)) {
        std::cout << "Failed to create pixel shader!\n";
        return false;
    }

    // ========================================
    // 7. SHADER LOADING SUCCESS
    // ========================================
    // If we reach this point, all shader resources have been successfully created:
    // - Vertex shader object (transforms vertex positions)
    // - Pixel shader object (calculates pixel colors)
    // - Input layout (defines vertex data structure)
    //
    // These resources are now ready to be bound to the graphics pipeline during rendering

    return true; // Success - all shaders and layouts created successfully
}

void Graphics::Render() {
    // ========================================================================
    // DIRECTX 11 RENDERING PIPELINE EXECUTION
    // ========================================================================
    // This function demonstrates the complete DirectX 11 rendering process from
    // frame initialization to final presentation. It covers all major stages
    // of the graphics pipeline in a real-world rendering scenario.
    //
    // KEY CONCEPTS COVERED:
    // 1. Render Target Management - Frame buffer clearing and preparation
    // 2. Vertex Buffer Creation - GPU memory management for geometry data
    // 3. Input Assembly Configuration - Setting up the vertex input stage
    // 4. Shader Pipeline Binding - Connecting programmable shader stages
    // 5. Draw Call Execution - Triggering GPU rendering commands
    // 6. Frame Presentation - Double buffering and screen update
    // 7. Resource Management - Proper cleanup and memory management
    // ========================================================================

    // ========================================
    // 1. DIRECTX RESOURCE VALIDATION
    // ========================================
    // Safety check: Verify that all essential DirectX objects are properly initialized
    // This prevents crashes and provides clear error messaging for debugging
    // These objects are created during Graphics::Initialize() and are required for rendering
    if (!device.Get() || !deviceContext.Get() || !swapChain.Get()) {
        std::cout << "ERROR: DirectX objects are NULL" << std::endl;
        return; // Early exit if core DirectX objects are not available
    }

    // ========================================
    // 2. FRAME BUFFER CLEARING (RENDER TARGET PREPARATION)
    // ========================================
    // Frame clearing is essential for proper rendering - without this, you get
    // accumulation of previous frames (ghosting effect). This prepares a clean
    // canvas for the current frame's rendering operations.

    // Clear color definition: RGBA values (Red, Green, Blue, Alpha)
    // Values range from 0.0f (minimum) to 1.0f (maximum intensity)
    // {0.0f, 0.0f, 0.0f, 1.0f} = solid black background with full opacity
    float clearColor[4] = {0.0f, 0.0f, 0.0f, 1.0f};

    // Clear the render target view (back buffer) with the specified color
    // This operation runs on the GPU and clears every pixel in the frame buffer
    // clearColor array provides the RGBA values for the background
    deviceContext->ClearRenderTargetView(renderTargetView.Get(), clearColor);

    // ========================================
    // 3. VERTEX DATA DEFINITION AND LAYOUT
    // ========================================
    // Define the geometry we want to render - in this case, a colored triangle
    // Each vertex contains both position (3D coordinates) and color (RGBA values)
    // The vertex winding order is CLOCKWISE - this affects face culling and normals

    // Vertex data structure: 7 floats per vertex (position: 3, color: 4)
    // Coordinate system: DirectX uses left-handed coordinates
    // X-axis: right (+) / left (-), Y-axis: up (+) / down (-), Z-axis: into screen (+) / out of
    // screen (-)
    float triangle[] = {
        // Top vertex - RED color
        // Position (x, y, z): Center-top of screen at (0, 0.8, 0)
        // Color (r, g, b, a): Full red with full opacity (1, 0, 0, 1)
        0.0f,
        0.8f,
        0.0f, // Position coordinates
        1.0f,
        0.0f,
        0.0f,
        1.0f, // Color values (red)

        // Bottom right vertex - GREEN color
        // Position: Bottom-right at (0.8, -0.8, 0)
        // Color: Full green with full opacity (0, 1, 0, 1)
        0.8f,
        -0.8f,
        0.0f,
        0.0f,
        1.0f,
        0.0f,
        1.0f, // Color values (green)

        // Bottom left vertex - BLUE color
        // Position: Bottom-left at (-0.8, -0.8, 0)
        // Color: Full blue with full opacity (0, 0, 1, 1)
        -0.8f,
        -0.8f,
        0.0f,
        0.0f,
        0.0f,
        1.0f,
        1.0f // Color values (blue)
    };

    // ========================================
    // 4. VERTEX BUFFER CREATION AND GPU UPLOAD
    // ========================================
    // Vertex buffers store geometry data in GPU memory for efficient rendering
    // Creating buffers every frame is inefficient - typically done during initialization
    // This example shows the process for educational purposes

    // Buffer description: Define properties of the vertex buffer
    D3D11_BUFFER_DESC bufferDesc = {};
    bufferDesc.Usage             = D3D11_USAGE_DEFAULT; // GPU read/write access (most common)
    bufferDesc.ByteWidth =
        sizeof(triangle); // Total size: 3 vertices × 7 floats × 4 bytes = 84 bytes
    bufferDesc.BindFlags = D3D11_BIND_VERTEX_BUFFER; // This buffer will be used as vertex data

    // Initialization data: Specify the initial content of the buffer
    D3D11_SUBRESOURCE_DATA initData = {};
    initData.pSysMem                = triangle; // Pointer to our vertex data array

    // Create the vertex buffer on the GPU using the device interface
    // This allocates GPU memory and uploads our vertex data to it
    ID3D11Buffer* vertexBuffer; // Raw pointer for the created buffer
    HRESULT hr = device->CreateBuffer(&bufferDesc, &initData, &vertexBuffer);

    // Error handling: Check if buffer creation succeeded
    if (FAILED(hr)) {
        std::cout << "Failed to create vertex buffer! HRESULT: 0x" << std::hex << hr << std::endl;
        return; // Exit if vertex buffer creation fails
    }

    // ========================================
    // 5. INPUT ASSEMBLER STAGE CONFIGURATION
    // ========================================
    // The Input Assembler (IA) is the first stage of the DirectX graphics pipeline
    // It reads vertex data from buffers and assembles it into geometric primitives
    // This stage prepares data for the vertex shader processing

    // Configure vertex buffer binding parameters
    UINT stride = sizeof(float) * 7; // Size of one vertex (7 floats: 3 position + 4 color)
    UINT offset = 0;                 // Start reading from the beginning of the buffer

    // Bind our vertex buffer to the Input Assembler stage
    // Parameters: slot index, buffer count, buffer pointer, stride, offset
    // Slot 0 is the primary vertex stream (can have multiple streams for complex geometry)
    deviceContext->IASetVertexBuffers(0, 1, &vertexBuffer, &stride, &offset);

    // Set primitive topology: Define how vertices form geometric primitives
    // D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST: Every 3 vertices form one triangle
    // Other options: TRIANGLESTRIP, LINELIST, POINTLIST, etc.
    deviceContext->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);

    // ========================================
    // 6. SHADER PIPELINE VALIDATION AND BINDING
    // ========================================
    // Verify that all required shader resources are loaded and ready
    // Without shaders, the graphics pipeline cannot process vertices or pixels

    // Safety check: Ensure all shader objects are properly created
    if (!vertexShader.Get() || !pixelShader.Get() || !inputLayout.Get()) {
        std::cout << "ERROR: Shaders are null!" << std::endl;

        // Debug output: Show the state of each shader component
        std::cout << "vertexShader: " << (vertexShader.Get() ? "OK" : "NULL") << std::endl;
        std::cout << "pixelShader: " << (pixelShader.Get() ? "OK" : "NULL") << std::endl;
        std::cout << "inputLayout: " << (inputLayout.Get() ? "OK" : "NULL") << std::endl;

        vertexBuffer->Release(); // Clean up vertex buffer before exiting
        return;                  // Cannot render without shaders
    }

    // Bind input layout to the Input Assembler stage
    // This MUST be set BEFORE binding shaders - defines how vertex data is interpreted
    // The input layout was created using the vertex shader bytecode for compatibility
    deviceContext->IASetInputLayout(inputLayout.Get());

    // Bind shaders to their respective pipeline stages
    // Vertex Shader: Transforms vertex positions and attributes
    // Parameters: shader object, class instances (advanced), instance count
    deviceContext->VSSetShader(vertexShader.Get(), nullptr, 0);

    // Pixel Shader: Calculates final pixel colors for rasterized fragments
    // Parameters: shader object, class instances (advanced), instance count
    deviceContext->PSSetShader(pixelShader.Get(), nullptr, 0);

    // ========================================
    // 7. OUTPUT MERGER STAGE CONFIGURATION
    // ========================================
    // The Output Merger (OM) stage handles the final pixel output operations
    // Including depth testing, stencil testing, and blending

    // Disable depth testing by setting depth stencil state to nullptr
    // We don't have a depth buffer in this simple example, so depth testing is not needed
    // In 3D applications, depth testing prevents far objects from drawing over near objects
    deviceContext->OMSetDepthStencilState(nullptr, 0);

    // ========================================
    // 8. DRAW CALL EXECUTION (GPU COMMAND SUBMISSION)
    // ========================================
    // The Draw call is where actual rendering happens - this sends a command to the GPU
    // to process our vertices through the entire graphics pipeline

    // Draw() parameters breakdown:
    // - 3: Number of vertices to draw (our triangle has 3 vertices)
    // - 0: Starting vertex index (begin from the first vertex in the buffer)
    // This triggers the complete pipeline: Input Assembly → Vertex Shader →
    // Rasterization → Pixel Shader → Output Merger
    deviceContext->Draw(3, 0);

    // ========================================
    // 9. FRAME PRESENTATION (DOUBLE BUFFERING)
    // ========================================
    // Present the completed frame to the screen using the swap chain
    // This implements double buffering - rendering to back buffer, then swapping to front

    // Present() parameters:
    // - 1: Sync interval (1 = wait for vertical sync, 0 = present immediately)
    // - 0: Presentation flags (none in this case)
    // VSync synchronization prevents screen tearing but limits frame rate to monitor refresh
    swapChain->Present(0, 0);

    // ========================================
    // 10. RESOURCE CLEANUP AND MEMORY MANAGEMENT
    // ========================================
    // Proper resource management is crucial in DirectX applications
    // Every Created buffer must be Released to prevent memory leaks

    // Release the vertex buffer - decrements reference count
    // When reference count reaches 0, DirectX automatically frees the GPU memory
    // In production code, consider using ComPtr for automatic resource management
    vertexBuffer->Release();

    // NOTE: Other resources (shaders, input layout) are managed by ComPtr in class members
    // and will be automatically released when the Graphics object is destroyed
}
