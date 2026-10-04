#include <windows.h>
#include <shobjidl_core.h>
#include <shlwapi.h>
#include <iostream>
#include <cassert>
#include <vector>
#include <string>
#include <atomic>

#include "../../src/Guids.h"
#include "../../src/ExplorerCommand.h"

// Forward declaration of DllGetClassObject from DllMain
STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, LPVOID* ppv);

// --- Mock Classes for Shell Testing ---

class MockShellItem final : public IShellItem {
public:
    explicit MockShellItem(std::wstring path, bool failDisplayName = false)
        : m_path(std::move(path)), m_failDisplayName(failDisplayName) {}

    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) override {
        if (riid == IID_IUnknown || riid == IID_IShellItem) {
            *ppv = static_cast<IShellItem*>(this);
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }
    IFACEMETHODIMP_(ULONG) AddRef() override { return ++m_ref; }
    IFACEMETHODIMP_(ULONG) Release() override {
        ULONG r = --m_ref;
        if (r == 0) delete this;
        return r;
    }

    IFACEMETHODIMP BindToHandler(IBindCtx*, REFGUID, REFIID, void**) override { return E_NOTIMPL; }
    IFACEMETHODIMP GetParent(IShellItem**) override { return E_NOTIMPL; }
    IFACEMETHODIMP GetDisplayName(SIGDN sigdnName, LPWSTR* ppszName) override {
        if (m_failDisplayName || !ppszName) return E_FAIL;
        if (sigdnName != SIGDN_FILESYSPATH) return E_FAIL;
        return SHStrDupW(m_path.c_str(), ppszName);
    }
    IFACEMETHODIMP GetAttributes(SFGAOF, SFGAOF*) override { return E_NOTIMPL; }
    IFACEMETHODIMP Compare(IShellItem*, SICHINTF, int*) override { return E_NOTIMPL; }

private:
    std::atomic<ULONG> m_ref{1};
    std::wstring m_path;
    bool m_failDisplayName{false};
};

class MockShellItemArray final : public IShellItemArray {
public:
    explicit MockShellItemArray(std::vector<IShellItem*> items, bool failGetItem = false)
        : m_items(std::move(items)), m_failGetItem(failGetItem) {}

    ~MockShellItemArray() {
        for (auto* item : m_items) {
            if (item) item->Release();
        }
    }

    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) override {
        if (riid == IID_IUnknown || riid == IID_IShellItemArray) {
            *ppv = static_cast<IShellItemArray*>(this);
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }
    IFACEMETHODIMP_(ULONG) AddRef() override { return ++m_ref; }
    IFACEMETHODIMP_(ULONG) Release() override {
        ULONG r = --m_ref;
        if (r == 0) delete this;
        return r;
    }

    IFACEMETHODIMP BindToHandler(IBindCtx*, REFGUID, REFIID, void**) override { return E_NOTIMPL; }
    IFACEMETHODIMP GetPropertyStore(GETPROPERTYSTOREFLAGS, REFIID, void**) override { return E_NOTIMPL; }
    IFACEMETHODIMP GetPropertyDescriptionList(REFPROPERTYKEY, REFIID, void**) override { return E_NOTIMPL; }
    IFACEMETHODIMP GetAttributes(SIATTRIBFLAGS, SFGAOF, SFGAOF*) override { return E_NOTIMPL; }
    IFACEMETHODIMP GetCount(DWORD* pdwNumItems) override {
        if (!pdwNumItems) return E_POINTER;
        *pdwNumItems = static_cast<DWORD>(m_items.size());
        return S_OK;
    }
    IFACEMETHODIMP GetItemAt(DWORD dwIndex, IShellItem** ppsi) override {
        if (!ppsi) return E_POINTER;
        if (m_failGetItem || dwIndex >= m_items.size()) return E_FAIL;
        *ppsi = m_items[dwIndex];
        (*ppsi)->AddRef();
        return S_OK;
    }
    IFACEMETHODIMP EnumItems(IEnumShellItems**) override { return E_NOTIMPL; }

private:
    std::atomic<ULONG> m_ref{1};
    std::vector<IShellItem*> m_items;
    bool m_failGetItem{false};
};

int main() {
    std::cout << "[TEST] Starting Windows Shell Extension Contract Tests (C++20 x64)..." << std::endl;

    // 0. Architecture check: assert x64 pointer size
    assert(sizeof(void*) == 8);
    std::cout << "[PASS] Architecture check: pure x64 binary (pointer size == 8)" << std::endl;

    // Initialize COM
    HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    assert(SUCCEEDED(hr));

    // 1. Test DllGetClassObject
    IClassFactory* pFactory = nullptr;
    hr = DllGetClassObject(CLSID_EvydenciaShellCommand, IID_IClassFactory, reinterpret_cast<void**>(&pFactory));
    if (FAILED(hr) || !pFactory) {
        std::cerr << "[FAIL] DllGetClassObject failed with hr=0x" << std::hex << hr << std::endl;
        return 1;
    }
    std::cout << "[PASS] DllGetClassObject instantiated IClassFactory" << std::endl;

    // 2. Test CreateInstance
    IExplorerCommand* pCmd = nullptr;
    hr = pFactory->CreateInstance(nullptr, IID_IExplorerCommand, reinterpret_cast<void**>(&pCmd));
    pFactory->Release();
    if (FAILED(hr) || !pCmd) {
        std::cerr << "[FAIL] CreateInstance failed with hr=0x" << std::hex << hr << std::endl;
        return 1;
    }
    std::cout << "[PASS] Factory created IExplorerCommand instance" << std::endl;

    // 3. Test GetTitle
    LPWSTR pszTitle = nullptr;
    hr = pCmd->GetTitle(nullptr, &pszTitle);
    if (FAILED(hr) || !pszTitle) {
        std::cerr << "[FAIL] GetTitle failed" << std::endl;
        pCmd->Release();
        return 1;
    }
    std::wcout << L"[PASS] GetTitle returned: " << pszTitle << std::endl;
    assert(wcsstr(pszTitle, L"EVYD") != nullptr);
    CoTaskMemFree(pszTitle);

    // 4. Test GetIcon (SHStrDup format dllPath + ",-101")
    LPWSTR pszIcon = nullptr;
    hr = pCmd->GetIcon(nullptr, &pszIcon);
    if (FAILED(hr) || !pszIcon) {
        std::cerr << "[FAIL] GetIcon failed" << std::endl;
        pCmd->Release();
        return 1;
    }
    std::wcout << L"[PASS] GetIcon returned: " << pszIcon << std::endl;
    assert(wcsstr(pszIcon, L",-101") != nullptr);
    CoTaskMemFree(pszIcon);

    // 5. Test GetCanonicalName and Canonical CLSID Match
    GUID cmdGuid = {0};
    hr = pCmd->GetCanonicalName(&cmdGuid);
    assert(SUCCEEDED(hr));
    assert(IsEqualGUID(cmdGuid, CLSID_EvydenciaShellCommand));
    std::cout << "[PASS] GetCanonicalName matches CLSID_EvydenciaShellCommand {9F5E8E7D-5A1B-4E38-9A7B-8B3E1F9A2C4D}" << std::endl;

    // 6. Test GetToolTip
    LPWSTR pszTip = nullptr;
    hr = pCmd->GetToolTip(nullptr, &pszTip);
    assert(SUCCEEDED(hr) && pszTip != nullptr);
    std::wcout << L"[PASS] GetToolTip returned: " << pszTip << std::endl;
    CoTaskMemFree(pszTip);

    // 7. Test GetFlags
    EXPCMDFLAGS flags = ECF_DEFAULT;
    hr = pCmd->GetFlags(&flags);
    assert(SUCCEEDED(hr));
    assert(flags == ECF_DEFAULT);
    std::cout << "[PASS] GetFlags returned ECF_DEFAULT" << std::endl;

    // 8. Test GetState with nullptr array -> ECS_HIDDEN (Fail-Closed)
    EXPCMDSTATE state = ECS_ENABLED;
    hr = pCmd->GetState(nullptr, FALSE, &state);
    assert(SUCCEEDED(hr));
    assert(state == ECS_HIDDEN);
    std::cout << "[PASS] GetState(nullptr) returned ECS_HIDDEN" << std::endl;

    // 9. Test GetState with Supported Images -> ECS_ENABLED
    {
        std::vector<IShellItem*> items = {
            new MockShellItem(L"C:\\photos\\img1.jpg"),
            new MockShellItem(L"C:\\photos\\img2.PNG")
        };
        auto* array = new MockShellItemArray(std::move(items));
        state = ECS_HIDDEN;
        hr = pCmd->GetState(array, FALSE, &state);
        assert(SUCCEEDED(hr));
        assert(state == ECS_ENABLED);
        array->Release();
        std::cout << "[PASS] GetState(supported images) returned ECS_ENABLED" << std::endl;
    }

    // 10. Test GetState with Unsupported File -> ECS_HIDDEN
    {
        std::vector<IShellItem*> items = {
            new MockShellItem(L"C:\\documents\\readme.txt")
        };
        auto* array = new MockShellItemArray(std::move(items));
        state = ECS_ENABLED;
        hr = pCmd->GetState(array, FALSE, &state);
        assert(SUCCEEDED(hr));
        assert(state == ECS_HIDDEN);
        array->Release();
        std::cout << "[PASS] GetState(unsupported file) returned ECS_HIDDEN" << std::endl;
    }

    // 11. Test GetState with Mixed Selection (1 JPG + 1 TXT) -> ECS_HIDDEN (Fail-Closed)
    {
        std::vector<IShellItem*> items = {
            new MockShellItem(L"C:\\photos\\img1.jpg"),
            new MockShellItem(L"C:\\documents\\readme.txt")
        };
        auto* array = new MockShellItemArray(std::move(items));
        state = ECS_ENABLED;
        hr = pCmd->GetState(array, FALSE, &state);
        assert(SUCCEEDED(hr));
        assert(state == ECS_HIDDEN);
        array->Release();
        std::cout << "[PASS] GetState(mixed JPG + TXT) returned ECS_HIDDEN (Fail-Closed)" << std::endl;
    }

    // 12. Test GetState Fail-Closed when GetDisplayName fails -> ECS_HIDDEN
    {
        std::vector<IShellItem*> items = {
            new MockShellItem(L"C:\\photos\\img1.jpg", /*failDisplayName=*/true)
        };
        auto* array = new MockShellItemArray(std::move(items));
        state = ECS_ENABLED;
        hr = pCmd->GetState(array, FALSE, &state);
        assert(SUCCEEDED(hr));
        assert(state == ECS_HIDDEN);
        array->Release();
        std::cout << "[PASS] GetState(failing GetDisplayName) returned ECS_HIDDEN (Fail-Closed)" << std::endl;
    }

    // 13. Test GetState Fail-Closed when GetItemAt fails -> ECS_HIDDEN
    {
        std::vector<IShellItem*> items = {
            new MockShellItem(L"C:\\photos\\img1.jpg")
        };
        auto* array = new MockShellItemArray(std::move(items), /*failGetItem=*/true);
        state = ECS_ENABLED;
        hr = pCmd->GetState(array, FALSE, &state);
        assert(SUCCEEDED(hr));
        assert(state == ECS_HIDDEN);
        array->Release();
        std::cout << "[PASS] GetState(failing GetItemAt) returned ECS_HIDDEN (Fail-Closed)" << std::endl;
    }

    // 14. Test Extension Filtering Logic Unit Tests
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.jpg") == true);
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.JPG") == true);
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.jpeg") == true);
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.JPEG") == true);
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.png") == true);
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.PNG") == true);
    assert(IsSupportedImageExtension(L"C:\\documents\\doc.txt") == false);
    assert(IsSupportedImageExtension(L"C:\\programs\\app.exe") == false);
    assert(IsSupportedImageExtension(L"C:\\photos\\no_extension") == false);
    std::cout << "[PASS] IsSupportedImageExtension filtered all extensions correctly" << std::endl;

    pCmd->Release();
    CoUninitialize();

    std::cout << "\n>>> ALL WINDOWS SHELL CONTRACT TESTS PASSED (14/14) <<<\n" << std::endl;
    return 0;
}
