#include "ExplorerCommand.h"
#include "Guids.h"

#include <shlwapi.h>
#include <cwctype>
#include <fstream>
#include <sstream>

extern std::atomic<ULONG> g_refCount;

bool IsSupportedImageExtension(std::wstring_view path) {
    const size_t dotPos = path.find_last_of(L'.');
    if (dotPos == std::wstring_view::npos) {
        return false;
    }
    const std::wstring_view ext = path.substr(dotPos);

    auto iequals = [](std::wstring_view a, std::wstring_view b) {
        if (a.size() != b.size()) {
            return false;
        }
        for (size_t i = 0; i < a.size(); ++i) {
            if (towlower(a[i]) != towlower(b[i])) {
                return false;
            }
        }
        return true;
    };

    return iequals(ext, L".jpg") || iequals(ext, L".jpeg") || iequals(ext, L".png");
}

static void DummyAddressMarker() {}

static std::wstring GetDllDirectory() {
    HMODULE hModule = nullptr;
    GetModuleHandleExW(
        GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&DummyAddressMarker),
        &hModule
    );
    wchar_t path[MAX_PATH] = {0};
    if (hModule) {
        GetModuleFileNameW(hModule, path, MAX_PATH);
        PathRemoveFileSpecW(path);
    }
    return std::wstring(path);
}

static std::wstring FindAppExecutable() {
    // 1. Environment variable override
    wchar_t envPath[MAX_PATH] = {0};
    if (GetEnvironmentVariableW(L"EVYDENCIA_APP_PATH", envPath, MAX_PATH) > 0) {
        if (PathFileExistsW(envPath)) {
            return envPath;
        }
    }

    // 2. Registry HKCU\Software\EvydenciaPrintGenerator\AppPath
    HKEY hKey = nullptr;
    if (RegOpenKeyExW(HKEY_CURRENT_USER, L"Software\\EvydenciaPrintGenerator", 0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        wchar_t regPath[MAX_PATH] = {0};
        DWORD dataSize = sizeof(regPath);
        DWORD type = REG_SZ;
        if (RegQueryValueExW(hKey, L"AppPath", nullptr, &type, reinterpret_cast<LPBYTE>(regPath), &dataSize) == ERROR_SUCCESS) {
            RegCloseKey(hKey);
            if (PathFileExistsW(regPath)) {
                return regPath;
            }
        } else {
            RegCloseKey(hKey);
        }
    }

    // 3. Local adjacent EvydenciaPrintGenerator.exe
    std::wstring dllDir = GetDllDirectory();
    std::wstring adjExe = dllDir + L"\\EvydenciaPrintGenerator.exe";
    if (PathFileExistsW(adjExe.c_str())) {
        return adjExe;
    }

    // 4. Per-user installed app (%LOCALAPPDATA%\EVYDENCIA\PrintGenerator\EvydenciaPrintGenerator.exe)
    wchar_t localAppData[MAX_PATH] = {0};
    if (GetEnvironmentVariableW(L"LOCALAPPDATA", localAppData, MAX_PATH) > 0) {
        std::wstring installedExe = std::wstring(localAppData) + L"\\EVYDENCIA\\PrintGenerator\\EvydenciaPrintGenerator.exe";
        if (PathFileExistsW(installedExe.c_str())) {
            return installedExe;
        }
    }

    // 5. Repo developer environment: traverse parents looking for .venv\Scripts\python.exe
    std::wstring searchDir = dllDir;
    for (int i = 0; i < 5; ++i) {
        std::wstring venvPyw = searchDir + L"\\.venv\\Scripts\\pythonw.exe";
        if (PathFileExistsW(venvPyw.c_str())) {
            return venvPyw;
        }
        std::wstring venvPy = searchDir + L"\\.venv\\Scripts\\python.exe";
        if (PathFileExistsW(venvPy.c_str())) {
            return venvPy;
        }
        wchar_t parent[MAX_PATH] = {0};
        wcscpy_s(parent, searchDir.c_str());
        if (!PathRemoveFileSpecW(parent)) {
            break;
        }
        searchDir = parent;
    }

    // 6. Global pythonw.exe or python.exe
    return L"python.exe";
}

ExplorerCommand::ExplorerCommand() {
    ++g_refCount;
}

ExplorerCommand::~ExplorerCommand() {
    if (m_site) {
        m_site->Release();
        m_site = nullptr;
    }
    --g_refCount;
}

IFACEMETHODIMP ExplorerCommand::QueryInterface(REFIID riid, void** ppvObject) {
    if (!ppvObject) {
        return E_POINTER;
    }
    *ppvObject = nullptr;

    if (riid == IID_IUnknown || riid == IID_IExplorerCommand) {
        *ppvObject = static_cast<IExplorerCommand*>(this);
    } else if (riid == IID_IObjectWithSite) {
        *ppvObject = static_cast<IObjectWithSite*>(this);
    } else {
        return E_NOINTERFACE;
    }

    AddRef();
    return S_OK;
}

IFACEMETHODIMP_(ULONG) ExplorerCommand::AddRef() {
    return ++m_refCount;
}

IFACEMETHODIMP_(ULONG) ExplorerCommand::Release() {
    ULONG count = --m_refCount;
    if (count == 0) {
        delete this;
    }
    return count;
}

IFACEMETHODIMP ExplorerCommand::GetTitle(IShellItemArray* /*psiItemArray*/, LPWSTR* ppszName) {
    if (!ppszName) {
        return E_POINTER;
    }
    const wchar_t szTitle[] = L"Gerar com EVYD\u00CANCIA";
    const size_t cch = wcslen(szTitle) + 1;
    *ppszName = static_cast<LPWSTR>(CoTaskMemAlloc(cch * sizeof(wchar_t)));
    if (!*ppszName) {
        return E_OUTOFMEMORY;
    }
    wcscpy_s(*ppszName, cch, szTitle);
    return S_OK;
}

IFACEMETHODIMP ExplorerCommand::GetIcon(IShellItemArray* /*psiItemArray*/, LPWSTR* ppszIcon) {
    if (!ppszIcon) {
        return E_POINTER;
    }
    *ppszIcon = nullptr;
    return E_NOTIMPL;
}

IFACEMETHODIMP ExplorerCommand::GetToolTip(IShellItemArray* /*psiItemArray*/, LPWSTR* ppszInfo) {
    if (!ppszInfo) {
        return E_POINTER;
    }
    const wchar_t szToolTip[] = L"Abrir no EVYD\u00CANCIA Print Generator";
    const size_t cch = wcslen(szToolTip) + 1;
    *ppszInfo = static_cast<LPWSTR>(CoTaskMemAlloc(cch * sizeof(wchar_t)));
    if (!*ppszInfo) {
        return E_OUTOFMEMORY;
    }
    wcscpy_s(*ppszInfo, cch, szToolTip);
    return S_OK;
}

IFACEMETHODIMP ExplorerCommand::GetCanonicalName(GUID* pguidCommandName) {
    if (!pguidCommandName) {
        return E_POINTER;
    }
    *pguidCommandName = CLSID_EvydenciaShellCommand;
    return S_OK;
}

IFACEMETHODIMP ExplorerCommand::GetState(IShellItemArray* psiItemArray, BOOL /*fOkToBeSlow*/, EXPCMDSTATE* pCmdState) {
    if (!pCmdState) {
        return E_POINTER;
    }
    *pCmdState = ECS_HIDDEN;

    if (!psiItemArray) {
        return S_OK;
    }

    DWORD count = 0;
    if (FAILED(psiItemArray->GetCount(&count)) || count == 0) {
        return S_OK;
    }

    // Bounded check: verify all items have supported image extensions (.jpg, .jpeg, .png)
    for (DWORD i = 0; i < count; ++i) {
        IShellItem* item = nullptr;
        if (SUCCEEDED(psiItemArray->GetItemAt(i, &item)) && item) {
            LPWSTR pszPath = nullptr;
            if (SUCCEEDED(item->GetDisplayName(SIGDN_FILESYSPATH, &pszPath)) && pszPath) {
                const bool supported = IsSupportedImageExtension(pszPath);
                CoTaskMemFree(pszPath);
                item->Release();
                if (!supported) {
                    *pCmdState = ECS_HIDDEN;
                    return S_OK;
                }
            } else {
                item->Release();
                *pCmdState = ECS_HIDDEN;
                return S_OK;
            }
        }
    }

    *pCmdState = ECS_ENABLED;
    return S_OK;
}

IFACEMETHODIMP ExplorerCommand::Invoke(IShellItemArray* psiItemArray, IBindCtx* /*pbc*/) {
    if (!psiItemArray) {
        return S_OK;
    }

    DWORD count = 0;
    if (FAILED(psiItemArray->GetCount(&count)) || count == 0) {
        return S_OK;
    }

    std::vector<std::wstring> files;
    files.reserve(count);

    for (DWORD i = 0; i < count; ++i) {
        IShellItem* item = nullptr;
        if (SUCCEEDED(psiItemArray->GetItemAt(i, &item)) && item) {
            LPWSTR pszPath = nullptr;
            if (SUCCEEDED(item->GetDisplayName(SIGDN_FILESYSPATH, &pszPath)) && pszPath) {
                if (IsSupportedImageExtension(pszPath)) {
                    files.emplace_back(pszPath);
                }
                CoTaskMemFree(pszPath);
            }
            item->Release();
        }
    }

    if (!files.empty()) {
        LaunchApplication(files);
    }

    return S_OK;
}

IFACEMETHODIMP ExplorerCommand::GetFlags(EXPCMDFLAGS* pFlags) {
    if (!pFlags) {
        return E_POINTER;
    }
    *pFlags = ECF_DEFAULT;
    return S_OK;
}

IFACEMETHODIMP ExplorerCommand::EnumSubCommands(IEnumExplorerCommand** ppEnum) {
    if (!ppEnum) {
        return E_POINTER;
    }
    *ppEnum = nullptr;
    return E_NOTIMPL;
}

IFACEMETHODIMP ExplorerCommand::SetSite(IUnknown* pUnkSite) {
    if (m_site) {
        m_site->Release();
        m_site = nullptr;
    }
    m_site = pUnkSite;
    if (m_site) {
        m_site->AddRef();
    }
    return S_OK;
}

IFACEMETHODIMP ExplorerCommand::GetSite(REFIID riid, void** ppvSite) {
    if (!ppvSite) {
        return E_POINTER;
    }
    *ppvSite = nullptr;
    if (!m_site) {
        return E_FAIL;
    }
    return m_site->QueryInterface(riid, ppvSite);
}

bool ExplorerCommand::LaunchApplication(const std::vector<std::wstring>& files) {
    if (files.empty()) {
        return false;
    }

    const std::wstring exePath = FindAppExecutable();
    const bool isPython = (exePath.find(L"python") != std::wstring::npos);

    std::wstring baseCmd;
    if (isPython) {
        baseCmd = L"\"" + exePath + L"\" -m evydencia_print_generator --gui";
    } else {
        baseCmd = L"\"" + exePath + L"\" --gui";
    }

    // Estimate command line size
    size_t estimatedLength = baseCmd.length();
    for (const auto& file : files) {
        estimatedLength += file.length() + 3;
    }

    std::wstring finalCmd;

    // Protocol threshold: use manifest if more than 10 files or length > 2048
    if (files.size() > 10 || estimatedLength > 2048) {
        wchar_t tempPath[MAX_PATH] = {0};
        GetTempPathW(MAX_PATH, tempPath);
        std::wstring manifestPath = std::wstring(tempPath) + L"evydencia_shell_" +
            std::to_wstring(GetTickCount64()) + L"_" + std::to_wstring(GetCurrentProcessId()) + L".txt";

        HANDLE hFile = CreateFileW(
            manifestPath.c_str(),
            GENERIC_WRITE,
            0,
            nullptr,
            CREATE_ALWAYS,
            FILE_ATTRIBUTE_TEMPORARY,
            nullptr
        );

        if (hFile != INVALID_HANDLE_VALUE) {
            for (const auto& file : files) {
                int utf8Bytes = WideCharToMultiByte(CP_UTF8, 0, file.c_str(), -1, nullptr, 0, nullptr, nullptr);
                if (utf8Bytes > 1) {
                    std::string utf8Str(utf8Bytes - 1, '\0');
                    WideCharToMultiByte(CP_UTF8, 0, file.c_str(), -1, &utf8Str[0], utf8Bytes - 1, nullptr, nullptr);
                    utf8Str += "\n";
                    DWORD bytesWritten = 0;
                    WriteFile(hFile, utf8Str.data(), static_cast<DWORD>(utf8Str.size()), &bytesWritten, nullptr);
                }
            }
            CloseHandle(hFile);
            finalCmd = baseCmd + L" --shell-request \"" + manifestPath + L"\"";
        } else {
            // Fallback to inline command line
            finalCmd = baseCmd;
            for (const auto& file : files) {
                finalCmd += L" \"" + file + L"\"";
            }
        }
    } else {
        finalCmd = baseCmd;
        for (const auto& file : files) {
            finalCmd += L" \"" + file + L"\"";
        }
    }

    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi = { 0 };

    std::vector<wchar_t> cmdBuffer(finalCmd.begin(), finalCmd.end());
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
        return true;
    }

    return false;
}
