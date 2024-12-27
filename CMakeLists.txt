cmake_minimum_required(VERSION 3.20)
project(DX11Test)

# Use C++17 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add source files
set(SOURCES
    src/main.cpp
)

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES})

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