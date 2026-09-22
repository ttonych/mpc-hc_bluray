"""Compile actual compatibility value helpers and dialog draft operations.

Native controls/profile I/O are replaced by in-memory fixtures; no Java or disc.
"""
from pathlib import Path
import json
import re
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
player = root / 'src/mpc-hc'
source = (player / 'BlurayCompatibilityDlg.cpp').read_text(encoding='utf-8')


def block(signature):
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


ids = {k: int(v) for k, v in re.findall(r'#define\s+(IDS_BD_\w+)\s+(\d+)',
        (player / 'resource.h').read_text(encoding='utf-8-sig'))}
resource_bytes = (player / 'mpc-hc.rc').read_bytes()
resource_text = resource_bytes.decode('utf-16' if resource_bytes.startswith(b'\xff\xfe') else 'utf-8-sig')
en = dict(re.findall(r'^\s*(IDS_BD_\w+)\s+"((?:""|[^"\n])*)"\s*$', resource_text, re.M))
po = (player / 'mpcresources/PO/mpc-hc.ru.strings.po').read_text(encoding='utf-8-sig')
ru = {k: json.loads(v) for k, v in re.findall(r'msgctxt "(IDS_BD_\w+)"\nmsgid [^\n]*\nmsgstr ("[^\n]*")', po)}
code = r'''
#include <windows.h>
#include <atlstr.h>
#include <cassert>
#include <cstdio>
#include <map>
#include <vector>
#include "BlurayAdvancedSettings.h"
#include "resource.h"
int errors = 0;
void AfxMessageBox(const CStringW&, UINT) { ++errors; }
std::map<UINT, CStringW> labels;
CStringW ResStr(UINT id) { return labels.at(id); }
struct CComboBox {
    std::vector<CStringW> items;
    CStringW text;
    int selected = -1;
    void ResetContent() { items.clear(); selected=-1; text.Empty(); }
    void AddString(const CStringW& s) { items.push_back(s); }
    int FindStringExact(int, const CStringW& s) { for (size_t i=0;i<items.size();++i) if(items[i]==s) return int(i); return -1; }
    void SetCurSel(int i) { selected=i; }
    int GetCurSel() { return selected; }
    void SetWindowTextW(const CStringW& s) { text=s; selected=-1; }
    void GetWindowTextW(CStringW& s) { s=text; }
    void GetLBText(int i, CStringW& s) { s=items.at(i); }
    void LimitText(int) {}
    void SetFocus() {}
};
namespace BlurayUi {
using Choices = std::vector<std::pair<CStringW, BlurayAdvanced::Value>>;
'''
code += source[source.index('Choices ValueChoices('):source.index('\n}\n\nCBlurayCompatibilityDlg::')]
code += r'''
}
struct List { void SetItemText(int, int, const CStringW&) {} };
struct Base { bool accepted=false; void OnOK() { accepted=true; } };
struct CBlurayCompatibilityDlg : Base {
    BlurayAdvanced::Values m_values{};
    CComboBox m_value;
    List m_list;
    int m_selected = -1;
    bool m_loading = false;
    void ShowValue() { if(m_selected>=0) BlurayUi::FillValue(m_value,m_selected,m_values[m_selected]); }
    bool CommitValue();
    void OnDefault();
    void OnDefaults();
    void OnOK();
};
'''
for signature in ('bool CBlurayCompatibilityDlg::CommitValue()', 'void CBlurayCompatibilityDlg::OnDefault()',
                  'void CBlurayCompatibilityDlg::OnDefaults()', 'void CBlurayCompatibilityDlg::OnOK()'):
    code += block(signature) + '\n'
code += r'''
void checkValues() {
    using namespace BlurayAdvanced;
    for (int field=0;field<Count;++field) {
        for (const auto& choice : BlurayUi::ValueChoices(field)) {
            CComboBox combo;
            BlurayUi::FillValue(combo,field,choice.second);
            Value actual{true,99};
            assert(BlurayUi::ReadValue(combo,field,actual));
            if (actual.enabled!=choice.second.enabled) fwprintf(stderr,L"choice mismatch field=%d label=%s expected=%d actual=%d\n",field,choice.first.GetString(),choice.second.enabled,actual.enabled);
            assert(actual.enabled==choice.second.enabled);
            assert(!actual.enabled || actual.number==choice.second.number);
        }
        CComboBox combo; Value value;
        BlurayUi::FillValue(combo,field,{});
        assert(BlurayUi::ReadValue(combo,field,value) && !value.enabled);
    }
    for (const auto text : {L"",L"-1",L"+1",L"4294967296",L"0x100000000",L"0x",L"12junk",L"12 3",L"0xGG"}) {
        CComboBox combo; combo.SetWindowTextW(text); Value v{true,42};
        assert(!BlurayUi::ReadValue(combo,Hdr,v)); assert(v.enabled && v.number==42);
    }
    for (const auto text : {L" 0xffffffff ",L"4294967295"}) {
        CComboBox combo; combo.SetWindowTextW(text); Value v;
        assert(BlurayUi::ReadValue(combo,Hdr,v) && v.enabled && v.number==UINT32_MAX);
    }
    for (const auto field : {Age,Profile,Restrictions,Output,Decode}) {
        CComboBox combo; combo.SetWindowTextW(L"256"); Value v;
        if (field==Profile) assert(BlurayUi::ReadValue(combo,field,v));
        else assert(!BlurayUi::ReadValue(combo,field,v));
    }
    CBlurayCompatibilityDlg dialog;
    dialog.m_selected=Age; dialog.m_value.SetWindowTextW(L"256");
    dialog.OnOK(); assert(!dialog.accepted && !dialog.m_values[Age].enabled);
    dialog.m_value.SetWindowTextW(L"18"); dialog.OnOK();
    assert(dialog.accepted && dialog.m_values[Age].enabled && dialog.m_values[Age].number==18);
    dialog.m_value.SetWindowTextW(L"invalid"); dialog.OnDefault();
    assert(!dialog.m_values[Age].enabled && dialog.CommitValue());
    dialog.m_values[Hdr]={true,UINT32_MAX}; dialog.m_values[Profile]={true,0x310};
    dialog.OnDefaults(); for (const auto& v:dialog.m_values) assert(!v.enabled);
}
int main() {
'''
for language in (en, ru):
    code += 'labels = {\n'
    for key, value in language.items():
        if key in ids:
            # C++ strings use the decoded labels (resource doubled quotes are literal quotes).
            code += '{' + str(ids[key]) + ', L' + json.dumps(value.replace('""', '"'), ensure_ascii=False) + '},\n'
    code += '};\ncheckValues();\nlabels[IDS_BD_DEFAULT_VALUE] = labels[IDS_BD_UNLIMITED];\ncheckValues();\n'
code += 'puts("PASS: production EN/RU choices, numeric bounds, invalid draft, defaults and dialog acceptance.");\n}\n'
assert shutil.which('cl'), 'Run from the MSVC x64 environment.'
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)
cpp = out / 'bluray-compatibility.cpp'
cpp.write_text(code, encoding='utf-8')
exe = out / 'bluray-compatibility.exe'
subprocess.run(['cl', '/nologo', '/EHsc', '/std:c++17', '/O2', '/utf-8', '/D_UNICODE', '/DUNICODE',
                '/I' + str(player), str(cpp), '/Fe:' + str(exe)], cwd=out, check=True)
subprocess.run([str(exe)], check=True)
