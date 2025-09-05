#pragma once

/*
WIN32_LEAN_AND_MEAN: Excludes rarely-used Windows APIs (GDI, Shell, COM, Networking, Multimedia)
This significantly reduces compilation time and memory usage for DirectX projects
DirectX provides its own graphics/audio APIs, so we don't need legacy Windows multimedia functions
*/

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

// DirectX Headers
#include <d3d11.h>
#include <directxmath.h>
#include <dxgi.h>

// Standard Library Headers
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
