cmake_minimum_required(VERSION 3.20)
project(EvydenciaShellExtension LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
    add_compile_options(/W4 /permissive- /EHsc /utf-8)
endif()

# Shell extension COM in-process DLL
add_library(EvydenciaShellExtension SHARED
    src/ExplorerCommand.h
    src/ExplorerCommand.cpp
    src/Guids.h
    src/DllMain.cpp
    src/EvydenciaShellExtension.def
)

target_link_libraries(EvydenciaShellExtension PRIVATE
    shlwapi
    ole32
    shell32
    user32
    advapi32
)

set_target_properties(EvydenciaShellExtension PROPERTIES
    OUTPUT_NAME "EvydenciaShellExtension"
    PREFIX ""
)

# Contract test executable
add_executable(test_shell_extension
    tests/contract/test_shell_extension.cpp
    src/ExplorerCommand.cpp
    src/DllMain.cpp
)

target_link_libraries(test_shell_extension PRIVATE
    shlwapi
    ole32
    shell32
    user32
    advapi32
)

enable_testing()
add_test(NAME ShellContractTest COMMAND test_shell_extension)
