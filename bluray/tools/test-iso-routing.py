"""Compile the production ISO entry handler against an in-memory graph/mount fixture.

Checks that failed/unsupported images never fall through to ordinary LAV opening,
and that successful menu/movie/DVD opens retain the mount for graph lifetime.
"""
from pathlib import Path
import subprocess

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


frame = (player / 'MainFrm.cpp').read_text(encoding='utf-8-sig')
adapter = (player / 'MainFrmBluray.cpp').read_text(encoding='utf-8-sig')
code = r'''
#include "BlurayIso.h"
#include "resource.h"
#include <memory>
#include <cassert>
#include <cstdio>
#ifdef NDEBUG
#error These tests require assertions
#endif
using CString = CStringW;
struct FakeIso {
    static inline DWORD error = 0;
    static inline int live = 0, opens = 0;
    CStringW source;
    FakeIso() { ++live; } ~FakeIso() { --live; }
    static bool IsImage(const CStringW& path) { return CBlurayIso::IsImage(path); }
    DWORD Open(const CStringW& path) { ++opens; source = path; return error; }
    CStringW Root() const { return L"V:\\"; }
    CStringW Source() const { return source; }
};
#define CBlurayIso FakeIso
int discKind = 1, messages = 0;
struct Profile {
    bool menus = true;
    int GetProfileInt(const wchar_t*, const wchar_t*, int) { return menus; }
} profile;
Profile* AfxGetApp() { return &profile; }
CStringW ResStr(UINT) { return L"Error %lu"; }
void AfxMessageBox(const CStringW&, UINT) { ++messages; }
struct CWaitCursor {};
namespace BlurayOpen {
bool DiscRoot(const CStringW& path, CStringW& out) { out = path; return discKind == 1; }
}
BOOL FakeExists(const wchar_t*) { return discKind == 2; }
#define PathFileExistsW FakeExists
struct CMainFrame {
    bool m_bluraySwitching = false, closeAllowed = true, openAllowed = true;
    int menus = 0, movies = 0, dvds = 0, fallback = 0;
    std::unique_ptr<CBlurayIso> m_discImage;
    CStringW m_LastOpenBDPath;
    bool CloseMediaBeforeOpen() {
        if (!closeAllowed) return false;
        m_discImage.reset(); return true;
    }
    bool OpenBlurayMenu(const CStringW&) { ++menus; assert(FakeIso::live == 1); return openAllowed; }
    bool OpenBD(const CStringW&) { ++movies; assert(FakeIso::live == 1); return openAllowed; }
    void OpenDVDOrBD(const CStringW&) { ++dvds; assert(FakeIso::live == 1); }
    bool OpenDiscImage(const CString&);
    bool route(CString Path) {
'''
code += block(frame, 'if (!m_bluraySwitching && CBlurayIso::IsImage(Path))')
code += r'''
        ++fallback; return false;
    }
};
'''
code += block(adapter, 'bool CMainFrame::OpenDiscImage(')
code += r'''
int main() {
    {
        CMainFrame f;
        FakeIso::error = ERROR_FILE_NOT_FOUND;
        assert(f.route(L"missing.ISO"));
        assert(f.fallback == 0 && !f.m_discImage && messages == 1 && !FakeIso::live);
        FakeIso::error = 0;
        discKind = 0;
        assert(f.route(L"data.iso"));
        assert(f.fallback == 0 && !f.m_discImage && messages == 2 && !FakeIso::live);
        discKind = 1;
        f.closeAllowed = false;
        const int opens = FakeIso::opens;
        assert(f.route(L"cancel.iso") && FakeIso::opens == opens);
        f.closeAllowed = true;
        assert(f.route(L"menu.iso"));
        assert(f.menus == 1 && f.movies == 0 && f.m_discImage && FakeIso::live == 1);
        assert(f.m_LastOpenBDPath == L"menu.iso");
        profile.menus = false;
        assert(f.route(L"movie.iso"));
        assert(f.movies == 1 && f.m_discImage && FakeIso::live == 1);
        f.openAllowed = false;
        assert(f.route(L"bad-video.iso"));
        assert(!f.m_discImage && !FakeIso::live && !f.fallback);
        discKind = 2;
        assert(f.route(L"dvd.iso"));
        assert(f.dvds == 1 && f.m_discImage && FakeIso::live == 1);
        assert(!f.route(L"ordinary.mkv") && f.fallback == 1);
    }
    assert(!FakeIso::live);
    puts("PASS: production ISO dispatch, consumed failures, menu/movie/DVD selection and mount lifetime");
}
'''
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)
cpp, exe = out / 'iso-routing.cpp', out / 'iso-routing.exe'
cpp.write_text(code, encoding='utf-8')
subprocess.run(['cl', '/nologo', '/EHsc', '/std:c++17', '/utf-8', '/D_UNICODE', '/DUNICODE',
                '/I' + str(player), str(cpp), '/Fe:' + str(exe), '/link', 'shlwapi.lib'], cwd=out, check=True)
subprocess.run([str(exe)], check=True)
