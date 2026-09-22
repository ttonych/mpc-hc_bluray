// SPDX-License-Identifier: GPL-3.0-or-later
// Adapted from MPC-BE PPageBluray / BlurayDialogs at the recorded donor revision.
#pragma once
#include "CMPCThemePPageBase.h"
#include "CMPCThemeComboBox.h"
#include "BluraySettings.h"
#include <vector>

class CPPageBluray : public CMPCThemePPageBase {
    DECLARE_DYNAMIC(CPPageBluray)
    CMPCThemeComboBox m_opening, m_region, m_country;
    CMPCThemeComboBox m_menuLanguage, m_audioLanguage, m_subtitleLanguage;
    CMPCThemeComboBox m_java, m_persistentRoot, m_cacheRoot;
    CMPCThemeButton m_persistent, m_browseJava, m_browsePersistent, m_browseCache;
    std::vector<std::pair<CStringW, CStringW>> m_countries, m_languages;
    BluraySettings m_settings;
    CMPCThemeButton m_discs, m_checkJava, m_compatibility;
    BlurayJava::Probe m_javaProbe;
    bool m_loading = true;
    void FillCombo(CComboBox& combo, const std::vector<std::pair<CStringW, CStringW>>& choices, const CStringW& value);
    bool ReadCode(CComboBox& combo, const std::vector<std::pair<CStringW, CStringW>>& choices, int length, CStringW& code);
    CStringW PathValue(CComboBox& combo, UINT defaultLabel) const;
    void UpdateJavaStatus();
public:
    enum { IDD = IDD_PPAGEBLURAY };
    CPPageBluray();
protected:
    void DoDataExchange(CDataExchange* pDX) override;
    BOOL OnInitDialog() override;
    BOOL OnApply() override;
    afx_msg void OnChanged(UINT id);
    afx_msg void OnPersistent();
    afx_msg void OnCompatibility();
    afx_msg void OnDiscs();
    afx_msg void OnCheckJava();
    afx_msg void OnTimer(UINT_PTR id);
    afx_msg void OnDestroy();
    afx_msg void OnBrowse(UINT id);
    DECLARE_MESSAGE_MAP()
};
