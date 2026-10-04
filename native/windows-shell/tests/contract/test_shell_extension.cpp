#include <windows.h>
#include <shobjidl_core.h>
#include <iostream>
#include <cassert>

#include "../../src/Guids.h"
#include "../../src/ExplorerCommand.h"

// Forward declaration of DllGetClassObject from DllMain
STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, LPVOID* ppv);

int main() {
    std::cout << "[TEST] Starting Windows Shell Extension Contract Tests..." << std::endl;

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

    // 4. Test GetCanonicalName
    GUID cmdGuid = {0};
    hr = pCmd->GetCanonicalName(&cmdGuid);
    assert(SUCCEEDED(hr));
    assert(IsEqualGUID(cmdGuid, CLSID_EvydenciaShellCommand));
    std::cout << "[PASS] GetCanonicalName returned expected GUID" << std::endl;

    // 5. Test GetToolTip
    LPWSTR pszTip = nullptr;
    hr = pCmd->GetToolTip(nullptr, &pszTip);
    assert(SUCCEEDED(hr) && pszTip != nullptr);
    std::wcout << L"[PASS] GetToolTip returned: " << pszTip << std::endl;
    CoTaskMemFree(pszTip);

    // 6. Test GetFlags
    EXPCMDFLAGS flags = ECF_DEFAULT;
    hr = pCmd->GetFlags(&flags);
    assert(SUCCEEDED(hr));
    assert(flags == ECF_DEFAULT);
    std::cout << "[PASS] GetFlags returned ECF_DEFAULT" << std::endl;

    // 7. Test GetState with nullptr IShellItemArray -> ECS_HIDDEN
    EXPCMDSTATE state = ECS_ENABLED;
    hr = pCmd->GetState(nullptr, FALSE, &state);
    assert(SUCCEEDED(hr));
    assert(state == ECS_HIDDEN);
    std::cout << "[PASS] GetState(nullptr) returned ECS_HIDDEN" << std::endl;

    // 8. Test Extension Filtering Logic
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.jpg") == true);
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.JPG") == true);
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.jpeg") == true);
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.JPEG") == true);
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.png") == true);
    assert(IsSupportedImageExtension(L"C:\\photos\\img01.PNG") == true);
    assert(IsSupportedImageExtension(L"C:\\documents\\doc.txt") == false);
    assert(IsSupportedImageExtension(L"C:\\programs\\app.exe") == false);
    assert(IsSupportedImageExtension(L"C:\\photos\\no_extension") == false);
    std::cout << "[PASS] IsSupportedImageExtension filtered extensions correctly" << std::endl;

    pCmd->Release();
    CoUninitialize();

    std::cout << "\n>>> ALL WINDOWS SHELL CONTRACT TESTS PASSED <<<\n" << std::endl;
    return 0;
}
