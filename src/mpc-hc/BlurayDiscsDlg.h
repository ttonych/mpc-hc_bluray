// SPDX-License-Identifier: GPL-3.0-or-later
// Adapted from pinned MPC-BE BlurayDialogs; see bluray/imports.json.
#pragma once
#include "CMPCThemeDialog.h"
#include "CMPCThemePlayerListCtrl.h"
#include "BlurayCatalog.h"

class CBlurayDiscsDlg : public CMPCThemeDialog {
    CMPCThemePlayerListCtrl m_list;
    CToolTipCtrl m_tooltip;
    std::filesystem::path m_data, m_legacy, m_persistentRoot, m_cacheRoot;
    std::vector<BlurayCatalog::Entry> m_entries;
    std::wstring m_selectedId;
    bool m_loading = false;
    void Refresh(bool reload = true);
    int Selected() const;
    void ShowSelection();
    bool DataFolder(const BlurayCatalog::Entry& entry, std::filesystem::path& path, bool cache = false) const;
public:
    CBlurayDiscsDlg(const std::filesystem::path& data, const std::filesystem::path& persistentRoot,
        const std::filesystem::path& cacheRoot, CWnd* parent)
        : CMPCThemeDialog(IDD_BD_DISCS, parent), m_data(data),
        m_legacy(persistentRoot.empty() ? data / L"persistent" : persistentRoot),
        m_persistentRoot(persistentRoot), m_cacheRoot(cacheRoot) {}
protected:
    void DoDataExchange(CDataExchange* dx) override;
    BOOL OnInitDialog() override;
    BOOL PreTranslateMessage(MSG* message) override;
    afx_msg void OnChanged(NMHDR*, LRESULT*);
    afx_msg void OnBeginRename(NMHDR*, LRESULT*);
    afx_msg void OnEndRename(NMHDR*, LRESULT*);
    void OpenFolder(bool cache);
    afx_msg void OnOpen();
    afx_msg void OnOpenCache();
    afx_msg void OnRename();
    afx_msg void OnRefresh();
    afx_msg void OnFilter();
    afx_msg void OnReset();
    afx_msg LRESULT OnRefreshList(WPARAM, LPARAM);
    DECLARE_MESSAGE_MAP()
};
