#pragma once

#include <windows.h>
#include <shobjidl_core.h>
#include <atomic>
#include <string>
#include <string_view>
#include <vector>

bool IsSupportedImageExtension(std::wstring_view path);

class ExplorerCommand final : public IExplorerCommand, public IObjectWithSite {
public:
    ExplorerCommand();
    ~ExplorerCommand();

    // IUnknown
    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppvObject) override;
    IFACEMETHODIMP_(ULONG) AddRef() override;
    IFACEMETHODIMP_(ULONG) Release() override;

    // IExplorerCommand
    IFACEMETHODIMP GetTitle(IShellItemArray* psiItemArray, LPWSTR* ppszName) override;
    IFACEMETHODIMP GetIcon(IShellItemArray* psiItemArray, LPWSTR* ppszIcon) override;
    IFACEMETHODIMP GetToolTip(IShellItemArray* psiItemArray, LPWSTR* ppszInfo) override;
    IFACEMETHODIMP GetCanonicalName(GUID* pguidCommandName) override;
    IFACEMETHODIMP GetState(IShellItemArray* psiItemArray, BOOL fOkToBeSlow, EXPCMDSTATE* pCmdState) override;
    IFACEMETHODIMP Invoke(IShellItemArray* psiItemArray, IBindCtx* pbc) override;
    IFACEMETHODIMP GetFlags(EXPCMDFLAGS* pFlags) override;
    IFACEMETHODIMP EnumSubCommands(IEnumExplorerCommand** ppEnum) override;

    // IObjectWithSite
    IFACEMETHODIMP SetSite(IUnknown* pUnkSite) override;
    IFACEMETHODIMP GetSite(REFIID riid, void** ppvSite) override;

    // Internal helpers
    static bool LaunchApplication(const std::vector<std::wstring>& files);

private:
    std::atomic<ULONG> m_refCount{1};
    IUnknown* m_site{nullptr};
};
