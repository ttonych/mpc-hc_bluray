// SPDX-License-Identifier: GPL-3.0-or-later
// Menu/language and Java-path handling adapted from MPC-BE (see bluray/imports.json).
#include "stdafx.h"
#include "PPageBluray.h"
#include "BlurayCompatibilityDlg.h"
#include "BlurayDiscsDlg.h"
#include "BlurayMenu.h"
#include "../DSUtil/ISOLang.h"
#include <filesystem>

IMPLEMENT_DYNAMIC(CPPageBluray, CMPCThemePPageBase)
CPPageBluray::CPPageBluray() : CMPCThemePPageBase(IDD, IDD) {}

BEGIN_MESSAGE_MAP(CPPageBluray, CMPCThemePPageBase)
    ON_CONTROL_RANGE(CBN_SELCHANGE, IDC_BD_OPENING, IDC_BD_CACHE_ROOT, OnChanged)
    ON_CONTROL_RANGE(CBN_EDITCHANGE, IDC_BD_OPENING, IDC_BD_CACHE_ROOT, OnChanged)
    ON_CONTROL_RANGE(BN_CLICKED, IDC_BD_BROWSE_JAVA, IDC_BD_BROWSE_CACHE, OnBrowse)
    ON_BN_CLICKED(IDC_BD_PERSISTENT, OnPersistent)
    ON_BN_CLICKED(IDC_BD_COMPATIBILITY, OnCompatibility)
    ON_BN_CLICKED(IDC_BD_DISCS, OnDiscs)
    ON_BN_CLICKED(IDC_BD_CHECK_JAVA, OnCheckJava)
    ON_WM_TIMER()
    ON_WM_DESTROY()
END_MESSAGE_MAP()

void CPPageBluray::DoDataExchange(CDataExchange* pDX) {
    __super::DoDataExchange(pDX);
    DDX_Control(pDX, IDC_BD_OPENING, m_opening);
    DDX_Control(pDX, IDC_BD_REGION, m_region);
    DDX_Control(pDX, IDC_BD_COUNTRY, m_country);
    DDX_Control(pDX, IDC_BD_MENU_LANG, m_menuLanguage);
    DDX_Control(pDX, IDC_BD_AUDIO_LANG, m_audioLanguage);
    DDX_Control(pDX, IDC_BD_SUB_LANG, m_subtitleLanguage);
    DDX_Control(pDX, IDC_BD_JAVA_HOME, m_java);
    DDX_Control(pDX, IDC_BD_PERSIST_ROOT, m_persistentRoot);
    DDX_Control(pDX, IDC_BD_CACHE_ROOT, m_cacheRoot);
    DDX_Control(pDX, IDC_BD_PERSISTENT, m_persistent);
    DDX_Control(pDX, IDC_BD_BROWSE_JAVA, m_browseJava);
    DDX_Control(pDX, IDC_BD_BROWSE_PERSIST, m_browsePersistent);
    DDX_Control(pDX, IDC_BD_BROWSE_CACHE, m_browseCache);
    DDX_Control(pDX, IDC_BD_DISCS, m_discs);
    DDX_Control(pDX, IDC_BD_CHECK_JAVA, m_checkJava);
    DDX_Control(pDX, IDC_BD_COMPATIBILITY, m_compatibility);
}

void CPPageBluray::FillCombo(CComboBox& combo, const std::vector<std::pair<CStringW, CStringW>>& choices, const CStringW& value) {
    for (const auto& choice : choices) combo.AddString(choice.second);
    for (size_t i = 0; i < choices.size(); ++i) {
        if (value.CompareNoCase(choices[i].first) == 0) {
            combo.SetCurSel(int(i));
            return;
        }
    }
    combo.SetWindowTextW(value);
}

BOOL CPPageBluray::OnInitDialog() {
    __super::OnInitDialog();
    m_settings.Load();
    const auto& s = m_settings;
    m_opening.AddString(ResStr(IDS_BD_MAIN_MOVIE));
    m_opening.AddString(ResStr(IDS_BD_DISC_MENUS));
    m_opening.SetCurSel(s.menus ? 1 : 0);
    m_region.AddString(L"A"); m_region.AddString(L"B"); m_region.AddString(L"C");
    m_region.SetCurSel(s.region == 1 ? 0 : s.region == 4 ? 2 : 1);
    m_countries.emplace_back(L"", ResStr(IDS_BD_NO_PREFERENCE));
    EnumSystemLocalesEx([](LPWSTR locale, DWORD, LPARAM parameter) -> BOOL {
        auto& countries = *reinterpret_cast<std::vector<std::pair<CStringW, CStringW>>*>(parameter);
        wchar_t code[8]{}, name[160]{};
        if (GetLocaleInfoEx(locale, LOCALE_SISO3166CTRYNAME, code, 8) && wcslen(code) == 2 && BluraySettings::IsCode(code, 2)
                && GetLocaleInfoEx(locale, LOCALE_SLOCALIZEDCOUNTRYNAME, name, 160)) {
            const CStringW iso(code);
            if (std::none_of(countries.begin(), countries.end(), [&](const auto& c) { return c.first == iso; })) {
                countries.emplace_back(iso, CStringW(name));
            }
        }
        return TRUE;
    }, LOCALE_WINDOWS, reinterpret_cast<LPARAM>(&m_countries), nullptr);
    std::sort(m_countries.begin() + 1, m_countries.end(), [](const auto& a, const auto& b) { return a.second.CompareNoCase(b.second) < 0; });
    FillCombo(m_country, m_countries, s.country);
    m_languages.emplace_back(L"", ResStr(IDS_BD_NO_PREFERENCE));
    const char* codes[] = {"eng", "rus", "ukr", "bel", "fra", "deu", "spa", "ita", "por", "pol", "ces", "slk", "slv", "hrv", "srp", "bul", "ron", "hun", "ell", "nld", "dan", "swe", "nor", "fin", "isl", "est", "lav", "lit", "tur", "ara", "heb", "hin", "jpn", "kor", "zho", "tha", "vie", "ind", "msa"};
    for (const auto code : codes) {
        CStringW name = ISOLang::ISO6392ToLanguage(code);
        wchar_t localized[160]{};
        const auto lcid = ISOLang::ISO6392ToLcid(code);
        if (lcid && GetLocaleInfoW(lcid, LOCALE_SLOCALIZEDLANGUAGENAME, localized, 160)) name = localized;
        m_languages.emplace_back(CStringW(code), name);
    }
    FillCombo(m_menuLanguage, m_languages, s.menuLanguage);
    FillCombo(m_audioLanguage, m_languages, s.audioLanguage);
    FillCombo(m_subtitleLanguage, m_languages, s.subtitleLanguage);
    for (CComboBox* combo : {&m_country, &m_menuLanguage, &m_audioLanguage, &m_subtitleLanguage}) combo->LimitText(160);
    auto fillPath = [](CComboBox& combo, UINT label, const CStringW& value) {
        combo.AddString(ResStr(label)); combo.LimitText(32760);
        if (value.IsEmpty()) combo.SetCurSel(0); else combo.SetWindowTextW(value);
    };
    fillPath(m_java, IDS_BD_AUTO_SEARCH, s.javaHome);
    fillPath(m_persistentRoot, IDS_BD_PLAYER_FOLDER, s.persistentRoot);
    fillPath(m_cacheRoot, IDS_BD_PLAYER_FOLDER, s.cacheRoot);
    m_persistent.SetCheck(s.persistent ? BST_CHECKED : BST_UNCHECKED);
    m_loading = false;
    UpdateJavaStatus();
    return TRUE;
}

CStringW CPPageBluray::PathValue(CComboBox& combo, UINT defaultLabel) const {
    CStringW value;
    if (combo.GetCurSel() >= 0) combo.GetLBText(combo.GetCurSel(), value); else combo.GetWindowTextW(value);
    value.Trim();
    if (value == ResStr(defaultLabel)) value.Empty();
    return value;
}

void CPPageBluray::UpdateJavaStatus() {
    KillTimer(1); m_javaProbe.Cancel();
    const auto path = PathValue(m_java, IDS_BD_AUTO_SEARCH);
    const auto installation = BlurayJava::Inspect(path.GetString());
    UINT status = IDS_BD_JAVA_AUTO;
    if (!path.IsEmpty()) {
        switch (installation.status) {
        case BlurayJava::Status::Ready: status = IDS_BD_JAVA_FOUND; break;
        case BlurayJava::Status::WrongArchitecture: status = IDS_BD_JAVA_WRONG_ARCH; break;
        case BlurayJava::Status::Invalid: status = IDS_BD_JAVA_INVALID; break;
        default: status = IDS_BD_JAVA_NOT_FOUND; break;
        }
    }
    SetDlgItemTextW(IDC_BD_JAVA_STATUS, ResStr(status));
    m_checkJava.EnableWindow(!path.IsEmpty() && installation.status == BlurayJava::Status::Ready);
}

void CPPageBluray::OnCheckJava() {
    const auto installation = BlurayJava::Inspect(PathValue(m_java, IDS_BD_AUTO_SEARCH).GetString());
    if (installation.status != BlurayJava::Status::Ready) { UpdateJavaStatus(); return; }
    if (BlurayJava::Image(installation.launcher, false) != BlurayJava::Status::Ready) {
        SetDlgItemTextW(IDC_BD_JAVA_STATUS, ResStr(IDS_BD_JAVA_LAUNCHER)); return;
    }
    if (!m_javaProbe.Start(installation.launcher)) {
        SetDlgItemTextW(IDC_BD_JAVA_STATUS, ResStr(IDS_BD_JAVA_FAILED)); return;
    }
    m_checkJava.EnableWindow(FALSE);
    SetDlgItemTextW(IDC_BD_JAVA_STATUS, ResStr(IDS_BD_JAVA_CHECKING));
    if (!SetTimer(1, 100, nullptr)) {
        m_javaProbe.Cancel(); m_checkJava.EnableWindow(TRUE);
        SetDlgItemTextW(IDC_BD_JAVA_STATUS, ResStr(IDS_BD_JAVA_FAILED));
    }
}

void CPPageBluray::OnTimer(UINT_PTR id) {
    if (id != 1) { __super::OnTimer(id); return; }
    const auto result = m_javaProbe.Poll();
    if (result == BlurayJava::Probe::Result::Running) return;
    KillTimer(1); m_checkJava.EnableWindow(TRUE);
    const UINT status = result == BlurayJava::Probe::Result::Passed ? IDS_BD_JAVA_PASSED
        : result == BlurayJava::Probe::Result::TimedOut ? IDS_BD_JAVA_TIMEOUT : IDS_BD_JAVA_FAILED;
    SetDlgItemTextW(IDC_BD_JAVA_STATUS, ResStr(status));
    CStringW details(ResStr(status));
    // java -version writes to stderr; the bounded child pipe captures both streams.
    if (!m_javaProbe.output.empty()) {
        const int length = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, m_javaProbe.output.data(), int(m_javaProbe.output.size()), nullptr, 0);
        const UINT encoding = length ? CP_UTF8 : CP_ACP;
        const int count = MultiByteToWideChar(encoding, 0, m_javaProbe.output.data(), int(m_javaProbe.output.size()), nullptr, 0);
        CStringW output;
        MultiByteToWideChar(encoding, 0, m_javaProbe.output.data(), int(m_javaProbe.output.size()), output.GetBuffer(count), count);
        output.ReleaseBuffer(count); details += L"\r\n\r\n" + output.Left(4000);
    }
    AfxMessageBox(details, result == BlurayJava::Probe::Result::Passed ? MB_ICONINFORMATION : MB_ICONEXCLAMATION);
}

void CPPageBluray::OnDestroy() {
    KillTimer(1); m_javaProbe.Cancel(); __super::OnDestroy();
}

void CPPageBluray::OnDiscs() {
    // Immediate catalogue operations always use applied paths, not the page draft.
    BluraySettings active; active.Load();
    CBlurayDiscsDlg dialog(CBlurayMenu::DataDirectory().GetString(), active.persistentRoot.GetString(), active.cacheRoot.GetString(), this);
    dialog.DoModal();
}

void CPPageBluray::OnChanged(UINT) {
    if (!m_loading) { UpdateJavaStatus(); SetModified(); }
}

void CPPageBluray::OnPersistent() { SetModified(); }

void CPPageBluray::OnCompatibility() {
    // The child edits a copy; only outer Apply/OK writes the player's profile.
    CBlurayCompatibilityDlg dialog(m_settings.advanced, this);
    if (dialog.DoModal() == IDOK) {
        m_settings.advanced = dialog.Values();
        SetModified();
    }
}

void CPPageBluray::OnBrowse(UINT id) {
    CComboBox* combos[] = {&m_java, &m_persistentRoot, &m_cacheRoot};
    auto& combo = *combos[id - IDC_BD_BROWSE_JAVA];
    const auto path = PathValue(combo, id == IDC_BD_BROWSE_JAVA ? IDS_BD_AUTO_SEARCH : IDS_BD_PLAYER_FOLDER);
    CFolderPickerDialog picker(path.IsEmpty() ? nullptr : path.GetString(), FOS_PATHMUSTEXIST, this);
    if (picker.DoModal() == IDOK) {
        combo.SetCurSel(-1); combo.SetWindowTextW(picker.GetPathName()); OnChanged(0);
    }
}

bool CPPageBluray::ReadCode(CComboBox& combo, const std::vector<std::pair<CStringW, CStringW>>& choices, int length, CStringW& code) {
    if (combo.GetCurSel() >= 0) combo.GetLBText(combo.GetCurSel(), code); else combo.GetWindowTextW(code);
    code.Trim();
    for (const auto& choice : choices) if (code.CompareNoCase(choice.second) == 0) { code = choice.first; break; }
    if (length == 2) code.MakeUpper(); else code.MakeLower();
    if (!BluraySettings::IsCode(code, length)) {
        AfxMessageBox(ResStr(length == 2 ? IDS_BD_BAD_COUNTRY : IDS_BD_BAD_LANGUAGE), MB_ICONEXCLAMATION);
        combo.SetFocus();
        return false;
    }
    return true;
}

BOOL CPPageBluray::OnApply() {
    BluraySettings draft = m_settings;
    draft.menus = m_opening.GetCurSel() == 1;
    const int regions[] = {1, 2, 4};
    const int region = m_region.GetCurSel();
    if (region < 0 || region >= 3) return FALSE;
    draft.region = regions[region];
    if (!ReadCode(m_country, m_countries, 2, draft.country)
            || !ReadCode(m_menuLanguage, m_languages, 3, draft.menuLanguage)
            || !ReadCode(m_audioLanguage, m_languages, 3, draft.audioLanguage)
            || !ReadCode(m_subtitleLanguage, m_languages, 3, draft.subtitleLanguage)) return FALSE;
    CStringW values[] = {PathValue(m_java, IDS_BD_AUTO_SEARCH), PathValue(m_persistentRoot, IDS_BD_PLAYER_FOLDER), PathValue(m_cacheRoot, IDS_BD_PLAYER_FOLDER)};
    CComboBox* combos[] = {&m_java, &m_persistentRoot, &m_cacheRoot};
    for (int i = 0; i < 3; ++i) {
        if (!BluraySettings::IsPath(values[i])) {
            AfxMessageBox(ResStr(IDS_BD_BAD_PATH), MB_ICONEXCLAMATION); combos[i]->SetFocus(); return FALSE;
        }
    }
    if (!values[0].IsEmpty() && !BluraySettings::HasJavaRuntime(values[0])) {
        AfxMessageBox(ResStr(IDS_BD_BAD_JAVA), MB_ICONEXCLAMATION); m_java.SetFocus(); return FALSE;
    }
    draft.javaHome = values[0]; draft.persistentRoot = values[1]; draft.cacheRoot = values[2];
    draft.persistent = m_persistent.GetCheck() == BST_CHECKED;
    // Validation changes only this draft. Cancel or a failed Apply writes nothing.
    draft.Save();
    m_settings = draft;
    return __super::OnApply();
}
