cmake_minimum_required(VERSION 3.20)

project(DirectX11_Render)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(MSVC)
    add_compile_options(
        /utf-8
        /EHsc
        /MP
        $<$<CONFIG:DEBUG>:/Od>
        $<$<CONFIG:RELEASE>:/O2>
    )
endif()

# Use C++17 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Shader Compile Settings
set(SHADER_SOURCE_DIR "${CMAKE_SOURCE_DIR}/shaders")
set(SHADER_OUTPUT_DIR "${CMAKE_SOURCE_DIR}/bin/shaders")

# Shader Compile Function
function(compile_shader SHADER_FILE SHADER_TYPE)
    # Check if DXC compiler exists
    set(DXC_PATH "${CMAKE_SOURCE_DIR}/tools/dxc.exe")
    message(STATUS "Looking for DXC at: ${DXC_PATH}")
    
    if(NOT EXISTS "${CMAKE_SOURCE_DIR}/tools/dxc.exe")
        message(WARNING "DXC compiler not found at ${CMAKE_SOURCE_DIR}/tools/dxc.exe")
        message(STATUS "Current source dir: ${CMAKE_SOURCE_DIR}")
        message(STATUS "Current binary dir: ${CMAKE_BINARY_DIR}")
        return()
    endif()
    
    message(STATUS "DXC compiler found!")

    get_filename_component(SHADER_NAME ${SHADER_FILE} NAME_WE)
    set(SHADER_INPUT "${SHADER_SOURCE_DIR}/${SHADER_FILE}")
    set(SHADER_OUTPUT "${SHADER_OUTPUT_DIR}/${SHADER_NAME}.cso")
    set(SHADER_PDB "${SHADER_OUTPUT_DIR}/${SHADER_NAME}.pdb")
    set(SHADER_ASM "${SHADER_OUTPUT_DIR}/${SHADER_NAME}.asm")

    # Make Shader Output Directory
    file(MAKE_DIRECTORY ${SHADER_OUTPUT_DIR})

    # Print Debug Message
    message(STATUS "Compiling shader: ${SHADER_INPUT}")
    message(STATUS "Output to: ${SHADER_OUTPUT}")

    # Add Shader Compile Command
    add_custom_command(
        OUTPUT ${SHADER_OUTPUT}
        COMMAND fxc.exe /T ${SHADER_TYPE}_5_0 /E main 
                /Zi /Od /WX
                ${SHADER_INPUT} /Fo ${SHADER_OUTPUT}
        DEPENDS ${SHADER_INPUT}
        COMMENT "Compiling ${SHADER_TYPE} shader: ${SHADER_FILE}"
    )

    # Add Shader Output to Global Property
    set_property(GLOBAL APPEND PROPERTY SHADER_OUTPUTS ${SHADER_OUTPUT})
endfunction()

# Shader File List - Recursively find all shader files
file(GLOB_RECURSE SHADER_FILES 
    "${CMAKE_SOURCE_DIR}/shaders/*.hlsl"
)

# Compile Shaders
foreach(SHADER ${SHADER_FILES})
    get_filename_component(SHADER_NAME ${SHADER} NAME)
    if(${SHADER_NAME} MATCHES "VS.hlsl$")
        compile_shader(${SHADER_NAME} "vs")
    elseif(${SHADER_NAME} MATCHES "PS.hlsl$")
        compile_shader(${SHADER_NAME} "ps")
    endif()
endforeach()

# Add Compiled Shader Files to Custom Target
get_property(SHADER_OUTPUTS GLOBAL PROPERTY SHADER_OUTPUTS)
add_custom_target(Shaders ALL DEPENDS ${SHADER_OUTPUTS})

# Source Files - Recursively find all source/header files
file(GLOB_RECURSE SOURCES
    "${CMAKE_SOURCE_DIR}/src/*.cpp"
)

file(GLOB_RECURSE HEADERS
    "${CMAKE_SOURCE_DIR}/src/*.h"
    "${CMAKE_SOURCE_DIR}/src/*.hpp"
)

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS})
add_dependencies(${PROJECT_NAME} Shaders)

# Windows SDK Settings
if(MSVC)
    # Remove default UNICODE definitions from MSVC flags
    foreach(flag_var
        CMAKE_CXX_FLAGS CMAKE_CXX_FLAGS_DEBUG CMAKE_CXX_FLAGS_RELEASE
        CMAKE_CXX_FLAGS_MINSIZEREL CMAKE_CXX_FLAGS_RELWITHDEBINFO)
        if(${flag_var} MATCHES "/D_UNICODE")
            string(REGEX REPLACE "/D_UNICODE" "" ${flag_var} "${${flag_var}}")
        endif()
        if(${flag_var} MATCHES "/DUNICODE")
            string(REGEX REPLACE "/DUNICODE" "" ${flag_var} "${${flag_var}}")
        endif()
    endforeach(flag_var)
    
    # Add our own Unicode and UTF-8 support
    target_compile_options(${PROJECT_NAME} PRIVATE 
        /utf-8
        /DUNICODE
        /D_UNICODE
    )

    target_include_directories(${PROJECT_NAME} PRIVATE
        ${CMAKE_SOURCE_DIR}/src
        "C:/Program Files (x86)/Windows Kits/10/Include/10.0.22621.0/um"
        "C:/Program Files (x86)/Windows Kits/10/Include/10.0.22621.0/shared"
        "C:/Program Files (x86)/Windows Kits/10/Include/10.0.22621.0/ucrt"
        "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.38.33130/include"
    )
    
    target_link_libraries(${PROJECT_NAME} PRIVATE
        d3d11
        dxgi
        ole32
        user32
    )

    # 컴파일러 옵션 설정
    string(REPLACE "/W3" "/W4" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
    add_compile_options(
        /utf-8
        /EHsc
        /MP
        $<$<CONFIG:DEBUG>:/Od>
        $<$<CONFIG:RELEASE>:/O2>
    )
endif() 

# Set output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_SOURCE_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_SOURCE_DIR}/bin) 