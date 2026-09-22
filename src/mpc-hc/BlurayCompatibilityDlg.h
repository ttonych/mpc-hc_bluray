// SPDX-License-Identifier: GPL-3.0-or-later
// Value choices adapted from the pinned MPC-BE BlurayDialogs (bluray/imports.json).
#pragma once
#include "CMPCThemeDialog.h"
#include "CMPCThemePlayerListCtrl.h"
#include "CMPCThemeComboBox.h"
#include "BlurayAdvancedSettings.h"
#include <vector>

namespace BlurayUi {
using Choices = std::vector<std::pair<CStringW, BlurayAdvanced::Value>>;
Choices ValueChoices(int field);
CStringW DisplayValue(int field, BlurayAdvanced::Value value);
void FillValue(CComboBox& combo, int field, BlurayAdvanced::Value value);
bool ReadValue(CComboBox& combo, int field, BlurayAdvanced::Value& value);
}

class CBlurayCompatibilityDlg : public CMPCThemeDialog {
    CMPCThemePlayerListCtrl m_list;
    CMPCThemeComboBox m_value;
    BlurayAdvanced::Values m_values;
    int m_selected = -1;
    bool m_loading = false;
    bool CommitValue();
    void ShowValue();
public:
    CBlurayCompatibilityDlg(const BlurayAdvanced::Values& values, CWnd* parent);
    const BlurayAdvanced::Values& Values() const { return m_values; }
protected:
    void DoDataExchange(CDataExchange* dx) override;
    BOOL OnInitDialog() override;
    void OnOK() override;
    afx_msg void OnChanging(NMHDR*, LRESULT*);
    afx_msg void OnChanged(NMHDR*, LRESULT*);
    afx_msg void OnDefault();
    afx_msg void OnDefaults();
    afx_msg void OnDetails();
    DECLARE_MESSAGE_MAP()
};
