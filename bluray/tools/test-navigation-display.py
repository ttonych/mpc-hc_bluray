"""Exercise production chapter/caption methods with deterministic disc/UI fixtures."""
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
main = (root / 'src/mpc-hc/MainFrm.cpp').read_text(encoding='utf-8-sig')
bridge = (root / 'src/mpc-hc/MainFrmBluray.cpp').read_text(encoding='utf-8-sig')


def extract(text, name):
    start = text.index('void CMainFrame::' + name + '(')
    pos = text.index('{', start)
    depth, end = 1, pos + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


code = r'''
#include <windows.h>
#include <atlstr.h>
#include <cassert>
#include <cstdio>
#include <initializer_list>
#define VERIFY(value) (void)(value)
#include "resource.h"
#include "../../../include/BlurayVersion.h"
struct Bag { int count = 3; int ChapGetCount() { return count; } };
struct Bar {
    Bag* bag = nullptr;
    unsigned updates = 0;
    void SetChapterBag(Bag* value) { bag = value; ++updates; }
    void RemoveChapters() { SetChapterBag(nullptr); }
};
struct Menu {
    bool active = true;
    CString name;
    bool MenuActive() { return active; }
    CString DiscName() { return name; }
};
struct MRU { unsigned writes = 0; void SetCurrentTitle(CString) { ++writes; } };
struct CAppSettings {
    bool fShowChapters = true, fTitleBarTextTitle = true;
    int iTitleBarTextStyle = 1;
    MRU MRU;
} settings;
CAppSettings& AfxGetAppSettings() { return settings; }
CString StrRes(int) { return L"MPC-HC"; }
CString volumeLabel;
CString GetDriveLabel(TCHAR) { return volumeLabel; }
using CPath = CString;
CString GetDriveLabel(CPath) { return L"DVD volume"; }
bool IsNameSimilar(CString a, CString b) { return a == b; }
enum { PM_FILE, PM_DVD, PM_CAPTURE };
struct DVD {
    HRESULT GetDVDDirectory(wchar_t*, unsigned, ULONG* len) { *len = 0; return E_FAIL; }
};
struct Playlist { CString GetCurFileNameTitle() { return L"C:\\fixture\\movie.mkv"; } };
struct LCD { CString title; void SetMediaTitle(CString value) { title = value; } };
class CMainFrame {
public:
    Menu* m_blurayMenu = nullptr;
    bool m_blurayChaptersHidden = false;
    CString m_blurayTitle, caption;
    Bag* m_pCB = nullptr;
    Bar m_wndSeekBar, m_OSD;
    Playlist m_wndPlaylistBar;
    LCD m_Lcd;
    DVD* m_pDVDI = nullptr;
    int mode = PM_FILE;
    bool IsPlaybackCaptureMode() { return mode == PM_CAPTURE; }
    CString GetCaptureTitle() { return L"Capture device"; }
    int GetPlaybackMode() { return mode; }
    CString getBestTitle(bool) { return L"File metadata"; }
    CString GetFileName() { return L"movie.mkv"; }
    void SetWindowText(CString value) { caption = value; }
    void UpdateSeekbarChapterBag(bool force = true);
    void UpdateBlurayTitle(const CString& root);
    void OpenSetupWindowTitle(bool reset = false);
};
'''
code += extract(main, 'UpdateSeekbarChapterBag') + '\n'
code += extract(bridge, 'UpdateBlurayTitle') + '\n'
code += extract(main, 'OpenSetupWindowTitle') + '\n'
code += r'''
int main() {
    CMainFrame f;
    Bag film, replacement;
    f.m_pCB = &film;
    f.UpdateSeekbarChapterBag();
    assert(f.m_wndSeekBar.bag == &film && f.m_OSD.bag == &film);
    Menu menu;
    f.m_blurayMenu = &menu;
    f.UpdateSeekbarChapterBag(false);
    assert(!f.m_wndSeekBar.bag && !f.m_OSD.bag);
    unsigned updates = f.m_wndSeekBar.updates;
    f.UpdateSeekbarChapterBag(false);
    assert(updates == f.m_wndSeekBar.updates); // No 50-Hz repaint on unchanged state.
    f.m_pCB = &replacement;
    f.UpdateSeekbarChapterBag();
    assert(!f.m_wndSeekBar.bag && !f.m_OSD.bag); // Graph rebuild while in menu.
    menu.active = false;
    f.UpdateSeekbarChapterBag(false);
    assert(f.m_wndSeekBar.bag == &replacement && f.m_OSD.bag == &replacement);
    settings.fShowChapters = false;
    f.UpdateSeekbarChapterBag();
    menu.active = true; f.UpdateSeekbarChapterBag(false);
    menu.active = false; f.UpdateSeekbarChapterBag(false);
    assert(!f.m_wndSeekBar.bag && !f.m_OSD.bag); // Respect HC display preference.
    settings.fShowChapters = true;
    replacement.count = 0; f.UpdateSeekbarChapterBag();
    assert(!f.m_wndSeekBar.bag && !f.m_OSD.bag);
    f.m_pCB = nullptr; f.UpdateSeekbarChapterBag();
    assert(!f.m_wndSeekBar.bag);
    menu.name = L"  Disc metadata  ";
    volumeLabel = L"VOLUME";
    f.UpdateBlurayTitle(L"Q:");
    assert(f.m_blurayTitle == L"Disc metadata");
    for (int style : {0, 1}) {
        settings.iTitleBarTextStyle = style;
        f.OpenSetupWindowTitle();
        assert(f.caption == L"Disc metadata" && f.m_Lcd.title == f.caption);
        assert(settings.MRU.writes == 0);
    }
    menu.name.Empty();
    f.UpdateBlurayTitle(L"Q:\\");
    assert(f.m_blurayTitle == L"VOLUME"); // Same drive, different disc; no cached name.
    volumeLabel.Empty(); f.UpdateBlurayTitle(L"Q:");
    assert(f.m_blurayTitle == L"Blu-ray");
    f.UpdateBlurayTitle(L"C:/fixtures/Folder title/");
    assert(f.m_blurayTitle == L"Folder title");
    settings.iTitleBarTextStyle = 2; f.OpenSetupWindowTitle();
    assert(f.caption == MPCHC_BLURAY_NAME L" " MPCHC_BLURAY_VERSION_STR);
    settings.iTitleBarTextStyle = 1; f.OpenSetupWindowTitle(true);
    assert(f.caption == MPCHC_BLURAY_NAME L" " MPCHC_BLURAY_VERSION_STR);
    f.m_blurayMenu = nullptr;
    f.OpenSetupWindowTitle(); assert(f.caption == L"File metadata");
    assert(settings.MRU.writes == 1);
    settings.iTitleBarTextStyle = 0; f.OpenSetupWindowTitle();
    assert(f.caption == L"C:\\fixture\\movie.mkv");
    settings.iTitleBarTextStyle = 1; f.mode = PM_DVD; f.OpenSetupWindowTitle();
    assert(f.caption == L"DVD");
    f.mode = PM_CAPTURE; f.OpenSetupWindowTitle(); assert(f.caption == L"Capture device");
    puts("PASS: menu/film chapter transitions, rebuilds, preferences, disc title/fallbacks and ordinary captions.");
}
'''
assert shutil.which('cl'), 'Run from the MSVC x64 environment.'
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)
source = out / 'navigation-display.cpp'
source.write_text(code, encoding='utf-8')
exe = out / 'navigation-display.exe'
subprocess.run(['cl', '/nologo', '/EHsc', '/std:c++17', '/O2', '/MD', '/D_UNICODE', '/DUNICODE',
                '/I' + str(root / 'src/mpc-hc'), str(source), '/Fe:' + str(exe)], cwd=out, check=True)
subprocess.run([str(exe)], check=True)
