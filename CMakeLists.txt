cmake_minimum_required(VERSION 3.20)
project(DX11Test)

# Force UTF-8 for all files
if(MSVC)
    add_compile_options(/utf-8 /validate-charset)
endif()

# Use C++17 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 셰이더 컴파일 설정
set(SHADER_SOURCE_DIR "${CMAKE_SOURCE_DIR}/shaders")
set(SHADER_OUTPUT_DIR "${CMAKE_SOURCE_DIR}/bin/shaders")

# 셰이더 컴파일 함수
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

    # 셰이더 출력 디렉토리 생성
    file(MAKE_DIRECTORY ${SHADER_OUTPUT_DIR})

    # 디버그 메시지 출력
    message(STATUS "Compiling shader: ${SHADER_INPUT}")
    message(STATUS "Output to: ${SHADER_OUTPUT}")

    # 셰이더 컴파일 명령 추가
    add_custom_command(
        OUTPUT ${SHADER_OUTPUT}
        COMMAND fxc.exe /T ${SHADER_TYPE}_5_0 /E main 
                /Zi /Od /WX
                ${SHADER_INPUT} /Fo ${SHADER_OUTPUT}
        DEPENDS ${SHADER_INPUT}
        COMMENT "Compiling ${SHADER_TYPE} shader: ${SHADER_FILE}"
    )

    # 전역 속성에 출력 파일 추가
    set_property(GLOBAL APPEND PROPERTY SHADER_OUTPUTS ${SHADER_OUTPUT})
endfunction()

# 셰이더 파일 목록
set(SHADER_FILES
    BasicVS.hlsl
    BasicPS.hlsl
)

# 셰이더 컴파일
foreach(SHADER ${SHADER_FILES})
    if(${SHADER} MATCHES "VS.hlsl$")
        compile_shader(${SHADER} "vs")
    elseif(${SHADER} MATCHES "PS.hlsl$")
        compile_shader(${SHADER} "ps")
    endif()
endforeach()

# 컴파일된 셰이더 파일들을 커스텀 타겟으로 추가
get_property(SHADER_OUTPUTS GLOBAL PROPERTY SHADER_OUTPUTS)
add_custom_target(Shaders ALL DEPENDS ${SHADER_OUTPUTS})

# Add source files
set(SOURCES
    src/main.cpp
    src/Window.cpp
    src/Graphics.cpp
)

# Add header files
set(HEADERS
    src/Window.h
    src/Graphics.h
)

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS})
add_dependencies(${PROJECT_NAME} Shaders)

# Windows SDK settings
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
    
    target_link_libraries(${PROJECT_NAME} PRIVATE
        d3d11
        dxgi
        ole32
        user32
    )
endif() 

# Set output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_SOURCE_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_SOURCE_DIR}/bin) 