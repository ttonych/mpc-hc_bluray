"""Compile the actual graph-event branch and check Blu-ray-only error handling."""
import argparse
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--baseline', action='store_true')
a = p.parse_args()
name = 'src/mpc-hc/MainFrm.cpp'
text = (subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=root).decode('utf-8-sig')
        if a.baseline else (root / name).read_text(encoding='utf-8-sig'))
branch = text[text.index('            case EC_ERRORABORT:'):text.index('            case EC_BUFFERING_DATA:')]
code = r'''
#include <windows.h>
#include <dshow.h>
#include <atlstr.h>
#include <cassert>
#include <cstdlib>
#include "resource.h"
#define TRACE(...) ((void)0)
struct Playlist { CString name; CString GetCurFileName() { return name; } };
struct Frame {
    bool m_blurayMenu = false, m_bIsBDPlay = false;
    Playlist m_wndPlaylistBar;
    int closed = 0, message = 0, updated = 0;
    void UpdateCachedMediaState() { ++updated; }
    void PostMessage(UINT msg, UINT command) {
        assert(msg == WM_COMMAND && command == ID_FILE_CLOSEMEDIA); ++closed;
    }
    void SetClosingError(UINT id) { message = id; }
    void Event(LONG_PTR evParam1) { switch (EC_ERRORABORT) {
''' + branch + r'''
    } }
};
int main() {
    _set_error_mode(_OUT_TO_STDERR);
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
    for (int mode = 0; mode < 4; ++mode) {
        Frame f;
        f.m_blurayMenu = mode == 0; f.m_bIsBDPlay = mode == 1;
        f.m_wndPlaylistBar.name = mode == 2 ? L"00000.MPLS" : L"ordinary.mkv";
        f.Event(E_FAIL); assert(!f.closed && !f.message && f.updated == 1);
        f.Event(HRESULT_FROM_WIN32(ERROR_READ_FAULT));
        assert(f.closed == (mode < 3) && f.updated == 2);
        assert(f.message == (mode < 3 ? IDS_BD_DISC_READ_ERROR : 0));
    }
}
'''
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)
source = out / 'read-error-ui-test.cpp'
source.write_text(code, encoding='utf-8')
exe = out / 'read-error-ui-test.exe'
subprocess.run(['cl.exe', '/nologo', '/EHsc', '/std:c++17', '/MT', '/W4', '/DUNICODE', '/D_UNICODE',
                '/I' + str(root / 'src/mpc-hc'), '/Fe:' + str(exe), str(source)], cwd=out, check=True)
run = subprocess.run([str(exe)], capture_output=True, timeout=10)
assert (run.returncode != 0) if a.baseline else (run.returncode == 0), run.stderr
print('HC read-error event: ' + ('negative control rejected' if a.baseline else 'PASS'))
