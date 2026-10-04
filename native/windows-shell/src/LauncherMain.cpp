#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shlwapi.h>
#include <string>
#include <vector>

#pragma comment(lib, "shlwapi.lib")

static std::wstring GetExecutableDir() {
    wchar_t path[MAX_PATH] = {0};
    GetModuleFileNameW(nullptr, path, MAX_PATH);
    PathRemoveFileSpecW(path);
    return std::wstring(path);
}

static std::wstring FindPythonw() {
    std::wstring exeDir = GetExecutableDir();
    // 1. Search parent directories for .venv\Scripts\pythonw.exe
    std::wstring searchDir = exeDir;
    for (int i = 0; i < 6; ++i) {
        std::wstring venvPyw = searchDir + L"\\.venv\\Scripts\\pythonw.exe";
        if (PathFileExistsW(venvPyw.c_str())) {
            return venvPyw;
        }
        wchar_t parent[MAX_PATH] = {0};
        wcscpy_s(parent, searchDir.c_str());
        if (!PathRemoveFileSpecW(parent)) {
            break;
        }
        searchDir = parent;
    }

    // 2. Fallback to pythonw.exe in PATH
    return L"pythonw.exe";
}

int WINAPI wWinMain(HINSTANCE /*hInstance*/, HINSTANCE /*hPrevInstance*/, PWSTR pCmdLine, int /*nCmdShow*/) {
    std::wstring pythonw = FindPythonw();
    std::wstring cmd = L"\"" + pythonw + L"\" -m evydencia_print_generator";

    if (pCmdLine && wcslen(pCmdLine) > 0) {
        cmd += L" ";
        cmd += pCmdLine;
    } else {
        cmd += L" --gui";
    }

    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi = { 0 };

    std::vector<wchar_t> cmdBuffer(cmd.begin(), cmd.end());
    cmdBuffer.push_back(L'\0');

    BOOL success = CreateProcessW(
        nullptr,
        cmdBuffer.data(),
        nullptr,
        nullptr,
        FALSE,
        0,
        nullptr,
        nullptr,
        &si,
        &pi
    );

    if (success) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return 0;
    }

    return 1;
}
