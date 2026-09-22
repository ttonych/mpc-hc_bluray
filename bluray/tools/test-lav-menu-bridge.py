"""Exercise the actual LAV adapter methods with deterministic demux fixtures."""
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
lav = root / 'src/thirdparty/LAVFilters/src'
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)

def function(path, signature):
    text = (lav / path).read_text()
    start = text.index(signature)
    brace = text.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]

code = r'''
#include <windows.h>
#include <atomic>
#include <algorithm>
#include <vector>
#include <cstdint>
#include <cassert>
#include <cstdlib>
#include <cstdio>
#define CheckPointer(p, hr) if (!(p)) return hr
#define VFW_E_NOT_FOUND HRESULT(0x80040216L)
struct CAutoLock { explicit CAutoLock(void*) {} };
struct CBaseDemuxer {
    enum StreamType {video,audio,subpic,video_el,unknown};
    struct stream { DWORD pid; };
    std::vector<stream> groups[unknown];
    std::vector<int> transport;
    auto* GetStreams(StreamType type) {return &groups[type];}
    int GetTransportPID(DWORD index) const {return index<transport.size()?transport[index]:-1;}
};
struct CLAVSplitter {
    CBaseDemuxer* m_pDemuxer=nullptr;
    struct {bool DemuxEnhancementLayer=false;} m_settings;
    HRESULT FindStream(WORD,DWORD*,DWORD*,DWORD*);
};
struct BLURAY {uint64_t position=0; int bytes=0;};
uint64_t bd_tell(BLURAY* bd) {return bd->position;}
int bd_read(BLURAY* bd,uint8_t*,int size) {bd->bytes+=size;bd->position+=size;return size;}
constexpr int AVERROR_EOF=-100;
struct CBDDemuxer {
    std::atomic<uint64_t> m_menuReadStop{UINT64_MAX};
    std::vector<uint64_t> m_clipByteStarts;
    BLURAY* m_pBD;
    HRESULT SetPlayItemStop(UINT);
    static int BDByteStreamRead(void*,uint8_t*,int);
};
'''
code += function('demuxer/LAVSplitter/LAVSplitter.cpp', 'STDMETHODIMP CLAVSplitter::FindStream(')
code += function('demuxer/Demuxers/BDDemuxer.cpp', 'HRESULT CBDDemuxer::SetPlayItemStop(')
code += function('demuxer/Demuxers/BDDemuxer.cpp', 'int CBDDemuxer::BDByteStreamRead(')
code += r'''
int main() {
    _set_error_mode(_OUT_TO_STDERR);
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
    CBaseDemuxer source;
    source.transport={0x1011,0x1100,0x1101,0x1200,0x1201,0x1012};
    source.groups[0]={{0}}; source.groups[1]={{2},{1}};
    source.groups[2]={{UINT32_MAX},{UINT32_MAX-1},{4},{3}};
    source.groups[3]={{5}};
    CLAVSplitter splitter; splitter.m_pDemuxer=&source;
    DWORD index=99, group=99, ordinal=99;
    assert(splitter.FindStream(0x1100,&index,&group,&ordinal)==S_OK);
    assert(index==2 && group==1 && ordinal==1);
    assert(splitter.FindStream(0x1200,&index,&group,&ordinal)==S_OK);
    assert(index==6 && group==2 && ordinal==3);
    assert(splitter.FindStream(0xffff,&index,&group,&ordinal)==VFW_E_NOT_FOUND);
    assert(splitter.FindStream(0x1012,&index,&group,&ordinal)==VFW_E_NOT_FOUND);
    splitter.m_settings.DemuxEnhancementLayer=true;
    assert(splitter.FindStream(0x1012,&index,&group,&ordinal)==S_OK && index==7 && group==3);
    assert(splitter.FindStream(0x1100,nullptr,&group,&ordinal)==E_POINTER);
    splitter.m_pDemuxer=nullptr;
    assert(splitter.FindStream(0x1100,&index,&group,&ordinal)==E_UNEXPECTED);
    BLURAY bd;
    CBDDemuxer demux; demux.m_pBD=&bd; demux.m_clipByteStarts={0,1920,5760};
    uint8_t buffer[4096]{};
    assert(demux.BDByteStreamRead(&demux,buffer,4096)==4096); // opt-out unchanged
    bd.position=1728; bd.bytes=0;
    assert(demux.SetPlayItemStop(1)==S_OK);
    assert(demux.BDByteStreamRead(&demux,buffer,4096)==192);
    assert(bd.position==1920 && bd.bytes==192);
    assert(demux.BDByteStreamRead(&demux,buffer,4096)==AVERROR_EOF && bd.bytes==192);
    assert(demux.SetPlayItemStop(0)==E_INVALIDARG);
    assert(demux.SetPlayItemStop(3)==E_INVALIDARG);
    assert(demux.SetPlayItemStop(2)==S_OK);
    assert(demux.BDByteStreamRead(&demux,buffer,4096)==3840);
    bd.position=6000;
    assert(demux.BDByteStreamRead(&demux,buffer,4096)==AVERROR_EOF);
    puts("PASS: actual LAV PID mapping, virtual streams, pointer checks, optional read limit and exact play-item boundary.");
}
'''
assert shutil.which('cl'), 'Run from the MSVC x64 environment.'
source = out / 'lav-menu-bridge-test.cpp'
source.write_text(code)
exe = out / 'lav-menu-bridge-test.exe'
subprocess.run(['cl', '/nologo', '/EHsc', '/std:c++17', '/O2', '/DNOMINMAX', str(source), '/Fe:' + str(exe)], cwd=out, check=True)
subprocess.run([str(exe)], check=True)
