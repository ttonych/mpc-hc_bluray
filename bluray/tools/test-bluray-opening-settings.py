"""Exercise production Blu-ray entry routing and transactional settings Apply.

Filesystem fixtures are artificial; the profile adapter is in-memory. This test
does not load Java, play a disc or write any installed player's settings.
"""
from pathlib import Path
import struct
import shutil
import subprocess
import uuid

root = Path(__file__).resolve().parents[2]
player = root / 'src/mpc-hc'


def block(text, signature):
    start = text.index(signature)
    brace = text.index('{', start)
    end, depth = brace + 1, 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


settings = (player / 'BluraySettings.h').read_text(encoding='utf-8')
settings = settings.replace('#include <afxwin.h>', '').replace('#pragma once', '')
opening = (player / 'BlurayOpen.h').read_text(encoding='utf-8').replace('#include <afxstr.h>', '').replace('#pragma once', '')
page = (player / 'PPageBluray.cpp').read_text(encoding='utf-8')
frame = (player / 'MainFrm.cpp').read_text(encoding='utf-8-sig')
code = r'''
#include <windows.h>
#include <atlstr.h>
#include <shlwapi.h>
#include <cassert>
#include <cstdio>
#include <map>
#include <vector>
#include <string>
struct Profile {
    std::map<std::wstring, std::wstring> values;
    int writes = 0;
    unsigned GetProfileInt(const wchar_t*, const wchar_t* key, unsigned fallback) {
        auto p = values.find(key); return p == values.end() ? fallback : unsigned(std::stoull(p->second));
    }
    CStringW GetProfileString(const wchar_t*, const wchar_t* key, const wchar_t* fallback) {
        auto p = values.find(key); return p == values.end() ? fallback : p->second.c_str();
    }
    void WriteProfileInt(const wchar_t*, const wchar_t* key, int value) {
        ++writes; values[key] = std::to_wstring(value);
    }
    void WriteProfileString(const wchar_t*, const wchar_t* key, const wchar_t* value) {
        ++writes; if (value) values[key] = value; else values.erase(key);
    }
} profile;
Profile* AfxGetApp() { return &profile; }
'''
code += settings + '\n' + opening + '\n'
code += r'''
#include "resource.h"
struct CComboBox {
    int selected = -1;
    CStringW text;
    std::vector<CStringW> items;
    int GetCurSel() { return selected; }
    void GetLBText(int i, CStringW& v) { v = items.at(i); }
    void GetWindowTextW(CStringW& v) { v = text; }
    void SetFocus() {}
    void edit(const wchar_t* value) { selected = -1; text = value; }
};
struct Button { int state = BST_CHECKED; int GetCheck() { return state; } };
CStringW ResStr(UINT id) { CStringW value; value.Format(L"label-%u", id); return value; }
int errors = 0;
void AfxMessageBox(const CStringW&, UINT) { ++errors; }
struct Base { BOOL OnApply() { return TRUE; } };
struct CBlurayCompatibilityDlg {
    static inline int result = IDCANCEL;
    static inline BlurayAdvanced::Values next{};
    CBlurayCompatibilityDlg(const BlurayAdvanced::Values&, void*) {}
    int DoModal() { return result; }
    BlurayAdvanced::Values Values() { return next; }
};
struct CPPageBluray : Base {
    BluraySettings m_settings;
    CComboBox m_opening, m_region, m_country, m_menuLanguage, m_audioLanguage, m_subtitleLanguage;
    CComboBox m_java, m_persistentRoot, m_cacheRoot;
    Button m_persistent;
    std::vector<std::pair<CStringW, CStringW>> m_countries, m_languages;
    CPPageBluray() {
        m_opening.selected = 1; m_region.selected = 2;
        m_countries = {{L"RU",L"Country"}};
        m_languages = {{L"rus",L"Language"}};
        m_country.edit(L"Country"); m_menuLanguage.edit(L"Language");
        m_audioLanguage.edit(L" ENG "); m_subtitleLanguage.edit(L"");
    }
    CStringW PathValue(CComboBox&, UINT) const;
    bool ReadCode(CComboBox&, const std::vector<std::pair<CStringW, CStringW>>&, int, CStringW&);
    BOOL OnApply();
    void OnCompatibility();
    void SetModified() {}
};
'''
for signature in ('CStringW CPPageBluray::PathValue(', 'bool CPPageBluray::ReadCode(', 'BOOL CPPageBluray::OnApply()', 'void CPPageBluray::OnCompatibility()'):
    code += block(page, signature) + '\n'
code += r'''
struct CMainFrame {
    bool m_bluraySwitching = false, result = true;
    int calls = 0;
    bool OpenBlurayMenu(const CString&) { ++calls; return result; }
    bool route(CString Path) {
        CString root;
'''
code += block(frame, 'if (!m_bluraySwitching && AfxGetApp()->GetProfileInt')
code += r'''
        return false;
    }
};
int wmain(int argc, wchar_t** argv) {
    assert(argc == 2);
    const CStringW base(argv[1]);
    CStringW actual;
    const CStringW disc = base + L"\\disc";
    for (const auto& path : {disc, disc + L"\\", disc + L"\\BDMV", disc + L"\\bdmv\\",
                            disc + L"\\BDMV\\index.bdmv", disc + L"\\BDMV\\MovieObject.bdmv"}) {
        assert(BlurayOpen::DiscRoot(path, actual));
        assert(actual.CompareNoCase(disc + L"\\") == 0);
    }
    CStringW forward = disc; forward.Replace(L'\\',L'/');
    assert(BlurayOpen::DiscRoot(forward, actual));
    for (const auto& path : {base + L"\\dvd", base + L"\\empty", base + L"\\absent",
                            disc + L"\\BDMV\\PLAYLIST\\00001.mpls", disc + L"\\BDMV\\STREAM\\00001.m2ts",
                            disc + L"\\BDMV\\BACKUP\\index.bdmv", base + L"\\index.bdmv"}) {
        assert(!BlurayOpen::DiscRoot(path, actual) && actual.IsEmpty());
    }
    assert(!BlurayOpen::DiscRoot(L"https://example.invalid/index.bdmv", actual));
    assert(BlurayOpen::DiscRoot(base + L"\\BDMV", actual)); // Root itself named BDMV.
    CMainFrame frame;
    assert(!frame.route(disc)); // Original default is main movie.
    profile.values[L"BluRayMenus"] = L"1";
    assert(frame.route(disc) && frame.calls == 1);
    frame.result = false;
    assert(frame.route(disc) && frame.calls == 2); // No silent movie/DVD fallback on menu failure.
    frame.m_bluraySwitching = true;
    assert(!frame.route(disc) && frame.calls == 2);
    frame.m_bluraySwitching = false;
    assert(!frame.route(disc + L"\\BDMV\\PLAYLIST\\00001.mpls"));

    assert(BluraySettings::IsPath(L"") && BluraySettings::IsPath(base));
    for (const auto value : {L"relative",L"C:relative",L"\\rooted",L"C:\\bad\npath",L"C:\\bad\rpath",L"C:\\bad\"path"})
        assert(!BluraySettings::IsPath(value));
    assert(BluraySettings::HasJavaRuntime(base + L"\\java"));
    assert(BluraySettings::HasJavaRuntime(base + L"\\jdk8"));
    assert(!BluraySettings::HasJavaRuntime(base + L"\\fake-java")); // jvm.dll is a directory.
    assert(!BluraySettings::HasJavaRuntime(L""));

    profile.values[L"BluRayHdrPreference"] = L"3";
    CPPageBluray good; good.m_settings.Load();
    good.m_java.edit(base + L"\\java");
    good.m_persistentRoot.edit(base + L"\\new-saves");
    good.m_cacheRoot.items = {ResStr(IDS_BD_PLAYER_FOLDER)}; good.m_cacheRoot.selected = 0;
    assert(good.OnApply());
    assert(profile.values[L"BluRayMenus"] == L"1" && profile.values[L"BluRayRegion"] == L"4");
    assert(profile.values[L"BluRayCountry"] == L"RU" && profile.values[L"BluRayMenuLanguage"] == L"rus");
    assert(profile.values[L"BluRayAudioLanguage"] == L"eng" && profile.values[L"BluRaySubtitleLanguage"].empty());
    assert(profile.values[L"BluRayCacheRoot"].empty() && profile.values[L"BluRayHdrPreference"] == L"3");
    assert(GetFileAttributesW(base + L"\\new-saves") == INVALID_FILE_ATTRIBUTES); // Apply does not create/move data.
    const auto saved = profile.values;
    const int writes = profile.writes;
    for (int bad = 0; bad < 6; ++bad) {
        CPPageBluray page; page.m_settings.Load(); page.m_opening.selected = 0;
        if (bad == 0) page.m_country.edit(L"BAD");
        if (bad == 1) page.m_menuLanguage.edit(L"12x");
        if (bad == 2) page.m_java.edit(L"relative");
        if (bad == 3) page.m_java.edit(base + L"\\empty");
        if (bad == 4) page.m_cacheRoot.edit(L"C:\\bad\npath");
        if (bad == 5) page.m_region.selected = -1;
        assert(!page.OnApply());
        assert(profile.values == saved && profile.writes == writes);
        assert(page.m_settings.menus); // Invalid draft never replaces loaded state.
    }
    { CPPageBluray cancelled; cancelled.m_settings.Load(); cancelled.m_country.edit(L"US"); }
    assert(profile.values == saved && profile.writes == writes);
    CPPageBluray nested; nested.m_settings.Load();
    CBlurayCompatibilityDlg::next = nested.m_settings.advanced;
    CBlurayCompatibilityDlg::next[BlurayAdvanced::Hdr] = {true, 7};
    nested.OnCompatibility(); // Cancel child.
    assert(nested.m_settings.advanced[BlurayAdvanced::Hdr].number == 3);
    assert(profile.values == saved && profile.writes == writes);
    CBlurayCompatibilityDlg::result = IDOK;
    nested.OnCompatibility(); // Accept child, but not outer Apply yet.
    assert(nested.m_settings.advanced[BlurayAdvanced::Hdr].number == 7);
    assert(profile.values == saved && profile.writes == writes);
    nested.m_country.edit(L"BAD"); assert(!nested.OnApply());
    assert(profile.values == saved && profile.writes == writes);
    nested.m_country.edit(L"RU"); assert(nested.OnApply());
    assert(profile.values[L"BluRayHdrPreference"] == L"7");
    for (const auto n : {0u, 0x7fffffffu, 0x80000000u, 0xffffffffu}) {
        BluraySettings settings;
        for (const auto field : {BlurayAdvanced::Audio, BlurayAdvanced::Video, BlurayAdvanced::Display,
                BlurayAdvanced::Stereo, BlurayAdvanced::Uhd, BlurayAdvanced::UhdDisplay,
                BlurayAdvanced::Hdr, BlurayAdvanced::Sdr, BlurayAdvanced::Text})
            settings.advanced[field] = {true, n};
        settings.Save();
        BluraySettings reloaded; reloaded.Load();
        for (size_t field = 0; field < settings.advanced.size(); ++field) {
            assert(reloaded.advanced[field].enabled == settings.advanced[field].enabled);
            if (settings.advanced[field].enabled) assert(reloaded.advanced[field].number == n);
        }
    }
    BluraySettings defaults; defaults.Save(); defaults.Load();
    for (const auto& value : defaults.advanced) assert(!value.enabled);
    puts("PASS: production disc-root routing, menu-failure handling, Java/path validation, atomic Apply, uint32 profile round trips, defaults and Cancel.");
}
'''
assert shutil.which('cl'), 'Run from the MSVC x64 environment.'
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)
fixture = out / ('opening-fixture-' + uuid.uuid4().hex)
for name in ('disc/BDMV/index.bdmv', 'disc/BDMV/MovieObject.bdmv', 'disc/BDMV/PLAYLIST/00001.mpls',
             'disc/BDMV/STREAM/00001.m2ts', 'disc/BDMV/BACKUP/index.bdmv', 'BDMV/BDMV/index.bdmv',
             'dvd/VIDEO_TS/VIDEO_TS.IFO', 'index.bdmv', 'java/bin/server/jvm.dll', 'jdk8/jre/bin/server/jvm.dll'):
    p = fixture / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b'fixture')
# A structurally valid AMD64 DLL header; this fixture is never loaded.
image = bytearray(512)
struct.pack_into('<H', image, 0, 0x5a4d)
struct.pack_into('<I', image, 60, 64)
struct.pack_into('<IHHIIIHH', image, 64, 0x4550, 0x8664, 1, 0, 0, 0, 240, 0x2002)
struct.pack_into('<H', image, 88, 0x20b)
for name in ('java/bin/server/jvm.dll', 'jdk8/jre/bin/server/jvm.dll'):
    (fixture / name).write_bytes(image)
(fixture / 'empty').mkdir()
(fixture / 'fake-java/bin/server/jvm.dll').mkdir(parents=True)
cpp = out / 'bluray-opening-settings.cpp'
cpp.write_text(code, encoding='utf-8')
exe = out / 'bluray-opening-settings.exe'
subprocess.run(['cl', '/nologo', '/EHsc', '/std:c++17', '/O2', '/utf-8', '/D_UNICODE', '/DUNICODE', '/I' + str(player), str(cpp), '/Fe:' + str(exe), '/link', 'shlwapi.lib'], cwd=out, check=True)
subprocess.run([str(exe), str(fixture)], check=True)
