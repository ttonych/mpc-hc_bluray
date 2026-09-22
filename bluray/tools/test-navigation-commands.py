"""Check actual HC command handlers in Blu-ray, DVD and ordinary-file modes."""
import argparse
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--baseline', action='store_true', help='Require the original HC handlers to fail the Blu-ray regression')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
source_path = 'src/mpc-hc/MainFrm.cpp'
text = (subprocess.check_output(['git', 'show', 'HEAD:' + source_path], cwd=root).decode('utf-8-sig')
        if args.baseline else (root / source_path).read_text(encoding='utf-8-sig'))

def extract(name):
    start = text.index('void CMainFrame::' + name + '(')
    pos = text.index('{', start)
    depth = 1
    end = pos + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]

code = r'''
#include <windows.h>
#include <dshow.h>
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include "resource.h"
struct CCmdUI {
    UINT m_nID;
    bool enabled = false;
    void Enable(BOOL value) { enabled = !!value; }
};
struct Menu {
    UINT key = 0;
    bool top = true, popup = true, active = true;
    bool Key(UINT value) { key = value; return true; }
    bool CanShowMenu(bool isPopup) { return isPopup ? popup : top; }
    bool MenuActive() { return active; }
};
struct DVD {
    ULONG restrictions = 0;
    HRESULT result = S_OK;
    int shown = 0, selected = 0, activated = 0, returned = 0, resumed = 0;
    HRESULT GetCurrentUOPS(ULONG* value) { *value = restrictions; return result; }
    void ShowMenu(DVD_MENU_ID id, DWORD, void*) { shown = id; }
    void SelectRelativeButton(DVD_RELATIVE_BUTTON id) { selected = id; }
    void ActivateButton() { ++activated; }
    void ReturnFromSubmenu(DWORD, void*) { ++returned; }
    void Resume(DWORD, void*) { ++resumed; }
};
enum { PM_FILE, PM_DVD };
class CMainFrame {
public:
    enum class MLS { CLOSED, LOADING, LOADED };
    MLS load = MLS::LOADED;
    int mode = PM_FILE;
    OAFilterState mediaState = State_Paused;
    DVD_DOMAIN m_iDVDDomain = DVD_DOMAIN_Title;
    double m_dSpeedRate = 2.0;
    Menu* m_blurayMenu = nullptr;
    DVD dvd;
    DVD* m_pDVDI = &dvd;
    DVD* m_pDVDC = &dvd;
    unsigned plays = 0;
    MLS GetLoadState() { return load; }
    int GetPlaybackMode() { return mode; }
    OAFilterState GetMediaState() { return mediaState; }
    void SendMessage(UINT message, UINT id) { assert(message == WM_COMMAND && id == ID_PLAY_PLAY); ++plays; }
    void OnPlayPlay() { ++plays; }
    void OnNavigateMenu(UINT);
    void OnUpdateNavigateMenu(CCmdUI*);
    void OnNavigateMenuItem(UINT);
    void OnUpdateNavigateMenuItem(CCmdUI*);
};
'''
for name in ['OnNavigateMenu', 'OnUpdateNavigateMenu', 'OnNavigateMenuItem', 'OnUpdateNavigateMenuItem']:
    code += extract(name) + '\n'
code += r'''
int main() {
    _set_error_mode(_OUT_TO_STDERR);
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
    CMainFrame frame;
    Menu menu;
    frame.m_blurayMenu = &menu; // Blu-ray uses HC's PM_FILE graph, not PM_DVD.
    frame.OnNavigateMenu(ID_NAVIGATE_TITLEMENU);
    assert(menu.key == VK_HOME && frame.dvd.shown == 0 && frame.plays == 0);
    frame.OnNavigateMenu(ID_NAVIGATE_ROOTMENU);
    assert(menu.key == VK_APPS);
    CCmdUI title{ID_NAVIGATE_TITLEMENU}, popup{ID_NAVIGATE_ROOTMENU};
    frame.OnUpdateNavigateMenu(&title); frame.OnUpdateNavigateMenu(&popup);
    assert(title.enabled && popup.enabled);
    menu.top = false;
    frame.OnUpdateNavigateMenu(&title); frame.OnUpdateNavigateMenu(&popup);
    assert(!title.enabled && popup.enabled); // Restrictions are independent.
    menu.popup = false;
    frame.OnUpdateNavigateMenu(&popup); assert(!popup.enabled);
    CCmdUI audio{ID_NAVIGATE_AUDIOMENU};
    frame.OnUpdateNavigateMenu(&audio); assert(!audio.enabled);
    menu.key = 0; frame.OnNavigateMenu(ID_NAVIGATE_AUDIOMENU); assert(menu.key == 0);
    const UINT commands[] = {ID_NAVIGATE_MENU_LEFT, ID_NAVIGATE_MENU_RIGHT,
        ID_NAVIGATE_MENU_UP, ID_NAVIGATE_MENU_DOWN, ID_NAVIGATE_MENU_ACTIVATE, ID_NAVIGATE_MENU_LEAVE};
    const UINT keys[] = {VK_LEFT, VK_RIGHT, VK_UP, VK_DOWN, VK_RETURN, VK_ESCAPE};
    for (unsigned i = 0; i < 6; ++i) {
        frame.OnNavigateMenuItem(commands[i]); assert(menu.key == keys[i]);
        CCmdUI item{commands[i]}; frame.OnUpdateNavigateMenuItem(&item); assert(item.enabled);
    }
    menu.key = 0; frame.OnNavigateMenuItem(ID_NAVIGATE_MENU_BACK); assert(menu.key == 0);
    CCmdUI back{ID_NAVIGATE_MENU_BACK}; frame.OnUpdateNavigateMenuItem(&back); assert(!back.enabled);
    menu.active = false;
    CCmdUI up{ID_NAVIGATE_MENU_UP}; frame.OnUpdateNavigateMenuItem(&up); assert(!up.enabled);
    frame.load = CMainFrame::MLS::LOADING;
    menu.top = menu.popup = menu.active = true;
    frame.OnUpdateNavigateMenu(&title); frame.OnUpdateNavigateMenuItem(&up);
    assert(!title.enabled && !up.enabled);
    frame.OnNavigateMenu(ID_NAVIGATE_TITLEMENU); frame.OnNavigateMenuItem(ID_NAVIGATE_MENU_UP);
    assert(menu.key == 0);
    frame.load = CMainFrame::MLS::LOADED;
    frame.m_blurayMenu = nullptr;
    frame.OnUpdateNavigateMenu(&title); assert(!title.enabled);
    frame.OnNavigateMenu(ID_NAVIGATE_TITLEMENU); assert(frame.dvd.shown == 0);
    frame.OnNavigateMenuItem(ID_NAVIGATE_MENU_ACTIVATE); assert(frame.plays == 1);
    frame.mode = PM_DVD;
    frame.OnNavigateMenu(ID_NAVIGATE_ROOTMENU);
    assert(frame.dvd.shown == DVD_MENU_Root && frame.plays == 2 && frame.m_dSpeedRate == 1.0);
    frame.dvd.restrictions = UOP_FLAG_ShowMenu_Title;
    frame.OnUpdateNavigateMenu(&title); frame.OnUpdateNavigateMenu(&popup);
    assert(!title.enabled && popup.enabled);
    frame.OnNavigateMenuItem(ID_NAVIGATE_MENU_LEFT); assert(frame.dvd.selected == DVD_Relative_Left);
    frame.OnNavigateMenuItem(ID_NAVIGATE_MENU_BACK); assert(frame.dvd.returned == 1);
    frame.OnNavigateMenuItem(ID_NAVIGATE_MENU_LEAVE); assert(frame.dvd.resumed == 1);
    puts("PASS: Blu-ray menu commands, availability, loading guards and unchanged DVD/file behavior.");
}
'''
assert shutil.which('cl'), 'Run from the MSVC x64 environment.'
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)
name = 'navigation-commands-baseline' if args.baseline else 'navigation-commands'
source = out / (name + '.cpp')
source.write_text(code, encoding='utf-8')
exe = out / (name + '.exe')
subprocess.run(['cl', '/nologo', '/EHsc', '/std:c++17', '/O2', '/I' + str(root / 'src/mpc-hc'),
                str(source), '/Fe:' + str(exe)], cwd=out, check=True)
result = subprocess.run([str(exe)], capture_output=args.baseline, text=True)
if args.baseline:
    assert result.returncode != 0 and 'menu.key == VK_HOME' in result.stderr, 'Negative control did not fail on the missing Blu-ray route'
    print('PASS: original HC handlers fail the missing Blu-ray command regression.')
else:
    result.check_returncode()
