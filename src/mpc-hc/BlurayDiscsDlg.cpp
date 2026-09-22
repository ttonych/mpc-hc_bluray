// SPDX-License-Identifier: GPL-3.0-or-later
// Adapted from pinned MPC-BE BlurayDialogs; see bluray/imports.json.
#include "stdafx.h"
#include "BlurayDiscsDlg.h"
#include "resource.h"

static bool Contains(CStringW text, CStringW filter) {
    text.MakeLower(); filter.MakeLower(); return filter.IsEmpty() || text.Find(filter) >= 0;
}
BEGIN_MESSAGE_MAP(CBlurayDiscsDlg, CMPCThemeDialog)
    ON_NOTIFY(LVN_ITEMCHANGED, IDC_BD_DISC_LIST, OnChanged)
    ON_NOTIFY(LVN_BEGINLABELEDIT, IDC_BD_DISC_LIST, OnBeginRename)
    ON_NOTIFY(LVN_ENDLABELEDIT, IDC_BD_DISC_LIST, OnEndRename)
    ON_BN_CLICKED(IDC_BD_DISC_OPEN, OnOpen)
    ON_BN_CLICKED(IDC_BD_DISC_CACHE, OnOpenCache)
    ON_BN_CLICKED(IDC_BD_DISC_RENAME, OnRename)
    ON_BN_CLICKED(IDC_BD_DISC_REFRESH, OnRefresh)
    ON_BN_CLICKED(IDC_BD_RESET_DISC, OnReset)
    ON_EN_CHANGE(IDC_BD_FILTER, OnFilter)
    ON_MESSAGE(WM_APP + 1, OnRefreshList)
END_MESSAGE_MAP()
void CBlurayDiscsDlg::DoDataExchange(CDataExchange* dx) { __super::DoDataExchange(dx); DDX_Control(dx, IDC_BD_DISC_LIST, m_list); fulfillThemeReqs(); }
int CBlurayDiscsDlg::Selected() const {
    const int row = m_list.GetNextItem(-1, LVNI_SELECTED);
    return row < 0 ? -1 : int(m_list.GetItemData(row));
}
BOOL CBlurayDiscsDlg::OnInitDialog() {
    __super::OnInitDialog();
    m_list.SetExtendedStyle(LVS_EX_FULLROWSELECT | LVS_EX_DOUBLEBUFFER | LVS_EX_LABELTIP);
    CRect rect; m_list.GetClientRect(rect);
    m_list.InsertColumn(0, ResStr(IDS_BD_DISC_TITLE), LVCFMT_LEFT, rect.Width() * 2 / 3);
    m_list.InsertColumn(1, ResStr(IDS_BD_DISC_LAST), LVCFMT_LEFT, rect.Width() / 3 - GetSystemMetrics(SM_CXVSCROLL) - 4);
    m_tooltip.Create(this); m_tooltip.SetMaxTipWidth(600); m_tooltip.Activate(TRUE);
    m_tooltip.AddTool(GetDlgItem(IDC_BD_DISC_OPEN), L" ");
    m_tooltip.AddTool(GetDlgItem(IDC_BD_DISC_CACHE), L" ");
    Refresh(); return TRUE;
}
static CStringW LocalDiscTime(const std::wstring& value) {
    SYSTEMTIME utc{}, local{};
    if (value.size() != 23 || value.substr(19) != L" UTC"
        || swscanf_s(value.c_str(), L"%hu-%hu-%hu %hu:%hu:%hu", &utc.wYear, &utc.wMonth, &utc.wDay,
            &utc.wHour, &utc.wMinute, &utc.wSecond) != 6
        || !SystemTimeToTzSpecificLocalTime(nullptr, &utc, &local)) return value.c_str();
    wchar_t date[128]{}, time[128]{};
    if (!GetDateFormatEx(LOCALE_NAME_USER_DEFAULT, DATE_SHORTDATE, &local, nullptr, date, _countof(date), nullptr)
        || !GetTimeFormatEx(LOCALE_NAME_USER_DEFAULT, TIME_NOSECONDS, &local, nullptr, time, _countof(time))) return value.c_str();
    return CStringW(date) + L" " + time;
}
void CBlurayDiscsDlg::Refresh(bool reload) {
    m_loading = true; m_list.SetRedraw(FALSE); m_list.DeleteAllItems();
    if (reload) m_entries = BlurayCatalog::List(m_data, m_legacy);
    CStringW filter; GetDlgItemTextW(IDC_BD_FILTER, filter); filter.Trim();
    int selection = 0;
    for (size_t i = 0; i < m_entries.size(); ++i) {
        const auto& e = m_entries[i]; CStringW label(e.Label().c_str());
        if (!Contains(label, filter)) continue;
        if (e.legacy) label += L" \u2014 " + ResStr(IDS_BD_LEGACY);
        const int row = m_list.InsertItem(m_list.GetItemCount(), label);
        m_list.SetItemData(row, i); m_list.SetItemText(row, 1, LocalDiscTime(e.seen));
        if (e.id == m_selectedId) selection = row;
    }
    m_loading = false;
    if (m_list.GetItemCount()) m_list.SetItemState(selection, LVIS_SELECTED | LVIS_FOCUSED, LVIS_SELECTED | LVIS_FOCUSED);
    m_list.SetRedraw(TRUE); m_list.Invalidate(); ShowSelection();
    CStringW count;
    count.Format(ResStr(filter.IsEmpty() ? IDS_BD_DISC_COUNT : IDS_BD_DISC_FILTER_COUNT), m_list.GetItemCount(), int(m_entries.size()));
    SetDlgItemTextW(IDC_BD_DISC_COUNT, count);
}
bool CBlurayDiscsDlg::DataFolder(const BlurayCatalog::Entry& entry, std::filesystem::path& path, bool useCache) const {
    if (entry.legacy) { path = entry.folder; return !useCache && !path.empty(); }
    // After Reset use the new generation, not the stale catalogue path. Before
    // any reset the recorded folder is where this disc was actually last opened.
    std::filesystem::path persistent, cache;
    if (!BlurayDiscStorage::Resolve(m_data, entry.id, persistent, cache)) return false;
    if (!useCache && persistent == m_data / L"persistent") { path = entry.folder; return !path.empty(); }
    if (!BlurayDiscStorage::Resolve(m_data, entry.id, persistent, cache, m_persistentRoot, m_cacheRoot)) return false;
    path = useCache ? cache : persistent;
    return !path.empty();
}
void CBlurayDiscsDlg::ShowSelection() {
    const int index = Selected();
    const bool selected = index >= 0 && size_t(index) < m_entries.size();
    GetDlgItem(IDC_BD_DISC_RENAME)->EnableWindow(selected);
    GetDlgItem(IDC_BD_RESET_DISC)->EnableWindow(selected && !m_entries[index].legacy && BlurayDiscStorage::ValidKey(m_entries[index].id));
    std::filesystem::path folder;
    const bool available = selected && DataFolder(m_entries[index], folder) && PathIsDirectoryW(folder.c_str());
    GetDlgItem(IDC_BD_DISC_OPEN)->EnableWindow(available);
    std::filesystem::path cache;
    const bool cacheAvailable = selected && DataFolder(m_entries[index], cache, true) && PathIsDirectoryW(cache.c_str());
    GetDlgItem(IDC_BD_DISC_CACHE)->EnableWindow(cacheAvailable);
    m_tooltip.UpdateTipText(cache.empty() ? L" " : cache.c_str(), GetDlgItem(IDC_BD_DISC_CACHE));
    SetDlgItemTextW(IDC_BD_DISC_NOTE, selected && m_entries[index].legacy ? ResStr(IDS_BD_LEGACY_NOTE) : ResStr(IDS_BD_DISC_NOTE));
    CStringW tip(folder.c_str());
    if (selected) {
        m_selectedId = m_entries[index].id;
        if (m_entries[index].legacy || std::count_if(m_entries.begin(), m_entries.end(), [&](const auto& e) {
            std::filesystem::path other; return DataFolder(e, other) && other == folder;
        }) > 1) tip = ResStr(IDS_BD_SHARED_FOLDER) + L"\r\n" + tip;
    }
    m_tooltip.UpdateTipText(tip.IsEmpty() ? L" " : tip.GetString(), GetDlgItem(IDC_BD_DISC_OPEN));
}
void CBlurayDiscsDlg::OnChanged(NMHDR*, LRESULT* result) { *result = 0; if (!m_loading) ShowSelection(); }
void CBlurayDiscsDlg::OnOpen() { OpenFolder(false); }
void CBlurayDiscsDlg::OnOpenCache() { OpenFolder(true); }
void CBlurayDiscsDlg::OpenFolder(bool cache) {
    const int index = Selected(); if (index < 0) return;
    std::filesystem::path path;
    if (!DataFolder(m_entries[index], path, cache) || !PathIsDirectoryW(path.c_str())
        || (INT_PTR)ShellExecuteW(m_hWnd, L"open", path.c_str(), nullptr, nullptr, SW_SHOWNORMAL) <= 32)
        AfxMessageBox(ResStr(IDS_BD_STORAGE_ERROR), MB_ICONERROR);
}
void CBlurayDiscsDlg::OnRename() {
    const int row = m_list.GetNextItem(-1, LVNI_SELECTED);
    if (row >= 0) { m_list.SetFocus(); m_list.EditLabel(row); }
}
void CBlurayDiscsDlg::OnBeginRename(NMHDR* header, LRESULT* result) {
    const auto* info = reinterpret_cast<NMLVDISPINFO*>(header); *result = 0;
    const auto& entry = m_entries[m_list.GetItemData(info->item.iItem)];
    if (auto* edit = m_list.GetEditControl()) { edit->SetLimitText(250); edit->SetWindowTextW(entry.Label().c_str()); }
}
void CBlurayDiscsDlg::OnEndRename(NMHDR* header, LRESULT* result) {
    const auto* info = reinterpret_cast<NMLVDISPINFO*>(header); *result = FALSE;
    if (!info->item.pszText) return;
    const int index = int(m_list.GetItemData(info->item.iItem));
    auto entry = BlurayCatalog::Read(m_data, m_entries[index].id);
    if (entry.name.empty()) entry = m_entries[index];
    CStringW alias(info->item.pszText); alias.Trim(); entry.alias = alias.GetString();
    if (!BlurayCatalog::Write(m_data, entry)) { AfxMessageBox(ResStr(IDS_BD_STORAGE_ERROR), MB_ICONERROR); return; }
    m_selectedId = entry.id; m_entries[index] = entry;
    PostMessage(WM_APP + 1); // Refilter only after the native label editor closes.
}
void CBlurayDiscsDlg::OnReset() {
    const int index = Selected(); if (index < 0) return;
    const auto entry = m_entries[index];
    if (entry.legacy || !BlurayDiscStorage::ValidKey(entry.id)) return;
    CStringW question; question.Format(ResStr(IDS_BD_RESET_DATA_CONFIRM), entry.Label().c_str());
    if (AfxMessageBox(question, MB_YESNO | MB_ICONQUESTION | MB_DEFBUTTON2) != IDYES) return;
    if (!BlurayDiscStorage::Reset(m_data, entry.id)) { AfxMessageBox(ResStr(IDS_BD_STORAGE_ERROR), MB_ICONERROR); return; }
    std::filesystem::path folder, cache;
    if (BlurayDiscStorage::Resolve(m_data, entry.id, folder, cache, m_persistentRoot, m_cacheRoot)) {
        // Custom roots' generation directories normally appear on disc open.
        // Create the persistent directory now so Open data folder works at once.
        // Create only newly selected generations; previous data is retained.
        if ((SHCreateDirectoryExW(m_hWnd, folder.c_str(), nullptr) != ERROR_SUCCESS && !PathIsDirectoryW(folder.c_str()))
            || (SHCreateDirectoryExW(m_hWnd, cache.c_str(), nullptr) != ERROR_SUCCESS && !PathIsDirectoryW(cache.c_str()))) {
            AfxMessageBox(ResStr(IDS_BD_STORAGE_ERROR), MB_ICONERROR); return;
        }
    }
    ShowSelection(); AfxMessageBox(ResStr(IDS_BD_RESET_DATA_DONE), MB_ICONINFORMATION);
}
void CBlurayDiscsDlg::OnRefresh() { Refresh(); }
void CBlurayDiscsDlg::OnFilter() { if (!m_loading) Refresh(false); }
LRESULT CBlurayDiscsDlg::OnRefreshList(WPARAM, LPARAM) { Refresh(false); return 0; }
BOOL CBlurayDiscsDlg::PreTranslateMessage(MSG* message) {
    m_tooltip.RelayEvent(message);
    if (message->message == WM_KEYDOWN) {
        if (auto* edit = m_list.GetEditControl()) {
            if (message->wParam == VK_RETURN) { m_list.SetFocus(); return TRUE; }
            if (message->wParam == VK_ESCAPE) { m_list.SendMessage(LVM_CANCELEDITLABEL); return TRUE; }
        } else if (message->wParam == VK_F2 && ::GetFocus() == m_list.m_hWnd) { OnRename(); return TRUE; }
    }
    return __super::PreTranslateMessage(message);
}
