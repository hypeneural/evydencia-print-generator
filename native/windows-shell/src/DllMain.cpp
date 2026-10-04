#include <windows.h>
#include <unknwn.h>
#include <atomic>

#include "Guids.h"
#include "ExplorerCommand.h"

std::atomic<ULONG> g_refCount{0};
HMODULE g_hModule = nullptr;

class ClassFactory final : public IClassFactory {
public:
    ClassFactory() = default;

    // IUnknown
    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppvObject) override {
        if (!ppvObject) {
            return E_POINTER;
        }
        *ppvObject = nullptr;
        if (riid == IID_IUnknown || riid == IID_IClassFactory) {
            *ppvObject = static_cast<IClassFactory*>(this);
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }

    IFACEMETHODIMP_(ULONG) AddRef() override {
        return ++m_refCount;
    }

    IFACEMETHODIMP_(ULONG) Release() override {
        ULONG count = --m_refCount;
        if (count == 0) {
            delete this;
        }
        return count;
    }

    // IClassFactory
    IFACEMETHODIMP CreateInstance(IUnknown* pUnkOuter, REFIID riid, void** ppvObject) override {
        if (!ppvObject) {
            return E_POINTER;
        }
        *ppvObject = nullptr;

        if (pUnkOuter != nullptr) {
            return CLASS_E_NOAGGREGATION;
        }

        ExplorerCommand* command = new (std::nothrow) ExplorerCommand();
        if (!command) {
            return E_OUTOFMEMORY;
        }

        HRESULT hr = command->QueryInterface(riid, ppvObject);
        command->Release(); // Balance the initial ref count of 1
        return hr;
    }

    IFACEMETHODIMP LockServer(BOOL fLock) override {
        if (fLock) {
            ++g_refCount;
        } else {
            --g_refCount;
        }
        return S_OK;
    }

private:
    std::atomic<ULONG> m_refCount{1};
};

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID /*lpReserved*/) {
    if (ul_reason_for_call == DLL_PROCESS_ATTACH) {
        g_hModule = hModule;
        DisableThreadLibraryCalls(hModule);
    }
    return TRUE;
}

STDAPI DllCanUnloadNow() {
    return (g_refCount == 0) ? S_OK : S_FALSE;
}

STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, LPVOID* ppv) {
    if (!ppv) {
        return E_POINTER;
    }
    *ppv = nullptr;

    if (rclsid != CLSID_EvydenciaShellCommand) {
        return CLASS_E_CLASSNOTAVAILABLE;
    }

    ClassFactory* factory = new (std::nothrow) ClassFactory();
    if (!factory) {
        return E_OUTOFMEMORY;
    }

    HRESULT hr = factory->QueryInterface(riid, ppv);
    factory->Release();
    return hr;
}

STDAPI DllRegisterServer() {
    return S_OK;
}

STDAPI DllUnregisterServer() {
    return S_OK;
}
