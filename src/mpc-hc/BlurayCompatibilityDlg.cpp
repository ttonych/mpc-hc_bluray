// SPDX-License-Identifier: GPL-3.0-or-later
#include "stdafx.h"
#include "BlurayCompatibilityDlg.h"
#include "resource.h"

namespace BlurayUi {
Choices ValueChoices(int field) {
    using namespace BlurayAdvanced;
    Choices choices{{ResStr(IDS_BD_DEFAULT_VALUE + field), {}}};
    auto add = [&](const CStringW& label, uint32_t value) { choices.push_back({label, {true, value}}); };
    switch (field) {
    case Age:
        for (auto age : {4u, 6u, 12u, 16u, 18u}) {
            CStringW label; label.Format(L"%u", age); add(label, age);
        }
        add(ResStr(IDS_BD_UNLIMITED), 255); break;
    case Profile: {
        const unsigned values[] = {0x100, 0x10110, 0x30200, 0x80200, 0x130240, 0x300, 0x310};
        for (int i = 0; i < 7; ++i) add(ResStr(IDS_BD_PROFILE_CHOICE + i), values[i]);
        break;
    }
    case Restrictions: {
        const unsigned values[] = {0, 5, 10, 20};
        for (int i = 0; i < 4; ++i) add(ResStr(IDS_BD_UO_CHOICE + i), values[i]);
        break;
    }
    case Output: add(L"2D", 0); add(L"3D", 1); break;
    case Decode: add(ResStr(IDS_BD_OFF), 0); add(ResStr(IDS_BD_ON), 1); break;
    case Audio: add(ResStr(IDS_BD_AUDIO_STEREO), 0x5555); add(ResStr(IDS_BD_AUDIO_SURROUND), 0xaaaa); break;
    default: break;
    }
    return choices;
}
CStringW DisplayValue(int field, BlurayAdvanced::Value value) {
    for (const auto& choice : ValueChoices(field)) {
        if (value.enabled == choice.second.enabled && (!value.enabled || value.number == choice.second.number)) return choice.first;
    }
    CStringW text; text.Format(BlurayAdvanced::Specs[field].hex ? L"0x%08X" : L"%u", value.number);
    return text;
}
void FillValue(CComboBox& combo, int field, BlurayAdvanced::Value value) {
    combo.ResetContent();
    for (const auto& choice : ValueChoices(field)) combo.AddString(choice.first);
    combo.LimitText(160);
    const auto choices = ValueChoices(field);
    for (size_t i = 0; i < choices.size(); ++i) {
        const auto candidate = choices[i].second;
        if (value.enabled == candidate.enabled && (!value.enabled || value.number == candidate.number)) {
            combo.SetCurSel(int(i));
            return;
        }
    }
    combo.SetWindowTextW(DisplayValue(field, value));
}
bool ReadValue(CComboBox& combo, int field, BlurayAdvanced::Value& value) {
    CStringW text;
    const auto choices = ValueChoices(field);
    const int selected = combo.GetCurSel();
    if (selected >= 0 && size_t(selected) < choices.size()) {
        value = choices[selected].second;
        return true;
    }
    combo.GetWindowTextW(text);
    text.Trim();
    for (const auto& choice : ValueChoices(field)) if (text == choice.first) { value = choice.second; return true; }
    uint32_t number;
    if (!BlurayAdvanced::Parse(text.GetString(), number) || !BlurayAdvanced::Valid(field, number)) {
        AfxMessageBox(ResStr(IDS_BD_BAD_NUMBER), MB_ICONEXCLAMATION); combo.SetFocus(); return false;
    }
    value = {true, number}; return true;
}
}

CBlurayCompatibilityDlg::CBlurayCompatibilityDlg(const BlurayAdvanced::Values& values, CWnd* parent)
    : CMPCThemeDialog(IDD_BD_COMPATIBILITY, parent), m_values(values) {}

BEGIN_MESSAGE_MAP(CBlurayCompatibilityDlg, CMPCThemeDialog)
    ON_NOTIFY(LVN_ITEMCHANGING, IDC_BD_ADV_LIST, OnChanging)
    ON_NOTIFY(LVN_ITEMCHANGED, IDC_BD_ADV_LIST, OnChanged)
    ON_BN_CLICKED(IDC_BD_ADV_DEFAULT, OnDefault)
    ON_BN_CLICKED(IDC_BD_ADV_DEFAULTS, OnDefaults)
    ON_BN_CLICKED(IDC_BD_ADV_DETAILS, OnDetails)
END_MESSAGE_MAP()

void CBlurayCompatibilityDlg::DoDataExchange(CDataExchange* dx) {
    __super::DoDataExchange(dx);
    DDX_Control(dx, IDC_BD_ADV_LIST, m_list);
    DDX_Control(dx, IDC_BD_ADV_VALUE, m_value);
    fulfillThemeReqs();
}
BOOL CBlurayCompatibilityDlg::OnInitDialog() {
    __super::OnInitDialog();
    m_loading = true;
    m_list.SetExtendedStyle(LVS_EX_FULLROWSELECT | LVS_EX_DOUBLEBUFFER | LVS_EX_LABELTIP);
    CRect rect; m_list.GetClientRect(rect);
    const int width = rect.Width() - GetSystemMetrics(SM_CXVSCROLL) - 4;
    m_list.InsertColumn(0, ResStr(IDS_BD_PARAMETER), LVCFMT_LEFT, width / 2);
    m_list.InsertColumn(1, ResStr(IDS_BD_VALUE), LVCFMT_LEFT, width - width / 2);
    for (int field = 0; field < BlurayAdvanced::Count; ++field) {
        const int row = m_list.InsertItem(field, ResStr(IDS_BD_ADV_NAME + field));
        m_list.SetItemData(row, field);
        m_list.SetItemText(row, 1, BlurayUi::DisplayValue(field, m_values[field]));
    }
    m_loading = false;
    m_list.SetItemState(0, LVIS_SELECTED | LVIS_FOCUSED, LVIS_SELECTED | LVIS_FOCUSED);
    return TRUE;
}
bool CBlurayCompatibilityDlg::CommitValue() {
    if (m_loading || m_selected < 0) return true;
    BlurayAdvanced::Value value;
    if (!BlurayUi::ReadValue(m_value, m_selected, value)) return false;
    m_values[m_selected] = value;
    m_list.SetItemText(m_selected, 1, BlurayUi::DisplayValue(m_selected, value));
    return true;
}
void CBlurayCompatibilityDlg::ShowValue() {
    if (m_selected < 0) return;
    m_loading = true;
    BlurayUi::FillValue(m_value, m_selected, m_values[m_selected]);
    SetDlgItemTextW(IDC_BD_ADV_DESCRIPTION, ResStr(IDS_BD_SHORT_DESC + m_selected));
    SetDlgItemTextW(IDC_BD_ADV_TECHNICAL, ResStr(IDS_BD_ADV_DESC + m_selected));
    OnDetails();
    m_loading = false;
}
void CBlurayCompatibilityDlg::OnChanging(NMHDR* header, LRESULT* result) {
    const auto* n = reinterpret_cast<NMLISTVIEW*>(header); *result = 0;
    if (!m_loading && (n->uChanged & LVIF_STATE) && (n->uOldState & LVIS_SELECTED)
            && !(n->uNewState & LVIS_SELECTED) && !CommitValue()) *result = TRUE;
}
void CBlurayCompatibilityDlg::OnChanged(NMHDR* header, LRESULT* result) {
    const auto* n = reinterpret_cast<NMLISTVIEW*>(header); *result = 0;
    if (!m_loading && (n->uChanged & LVIF_STATE) && (n->uNewState & LVIS_SELECTED)) {
        m_selected = int(m_list.GetItemData(n->iItem));
        ShowValue();
    }
}
void CBlurayCompatibilityDlg::OnDefault() {
    if (m_selected < 0) return;
    m_values[m_selected] = {};
    m_list.SetItemText(m_selected, 1, BlurayUi::DisplayValue(m_selected, {}));
    ShowValue();
}
void CBlurayCompatibilityDlg::OnDefaults() {
    m_values = {};
    for (int field = 0; field < BlurayAdvanced::Count; ++field)
        m_list.SetItemText(field, 1, BlurayUi::DisplayValue(field, {}));
    ShowValue();
}
void CBlurayCompatibilityDlg::OnDetails() {
    GetDlgItem(IDC_BD_ADV_TECHNICAL)->ShowWindow(IsDlgButtonChecked(IDC_BD_ADV_DETAILS) == BST_CHECKED ? SW_SHOW : SW_HIDE);
}
void CBlurayCompatibilityDlg::OnOK() {
    if (CommitValue()) __super::OnOK();
}
