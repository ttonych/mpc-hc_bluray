"""Compile actual HC overlay updates and HDR selection with synthetic graphics."""
import argparse
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, default=root / 'src/mpc-hc/BlurayMenu.cpp')
args = parser.parse_args()
source = args.source.read_text(encoding='utf-8-sig')

def section(start, end):
    begin = source.index(start)
    return source[begin:source.index(end, begin)]

# Keep production Paint/OnOverlay and the metadata/dirtying part of Present.
# Win32 bitmap allocation and madVR presentation require the separate GUI test.
code = (section('    void Paint(', '    static void Overlay(')
        + section('    void OnOverlay(', '    void Present(')
        + section('    void Present(', '        bool redraw = false;') + '    }\n')
fixture = r'''
#include <windows.h>
#include <cstdlib>
#include <cassert>
#include <cstdio>
#include <vector>
#include "BlurayMenuColor.h"
#include "BlurayMenuRle.h"
enum { IDS_BD_UNSUPPORTED_OVERLAY_SIZE=1, IDS_BD_INVALID_OVERLAY_REGION,
       IDS_BD_INVALID_OVERLAY_RLE };
int ResStr(int value) { return value; }
struct IMadVROsdServices {};
template<class T> using CComPtr = T*;
struct State {
    struct Plane {
        UINT width=0, height=0;
        std::vector<uint8_t> indices, pixels;
        std::array<BD_PG_PALETTE_ENTRY,256> palette{};
        bool dirty=false;
        int64_t flushPts=-1;
    };
    std::array<Plane,3> planes;
    IMadVROsdServices service;
    CComPtr<IMadVROsdServices> osd=&service;
    bool presenting=false, waitingGraph=false, bdjActive=false;
    bool graphicsPq2020=false, bdjPq2020=false;
    BLURAY_TITLE_INFO* title=nullptr;
    unsigned playitem=0, playlist=0;
    int error=0;
    template<class... T> void Log(T...) {}
// PRODUCTION
};
int main() {
    _set_error_mode(_OUT_TO_STDERR);
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
    State state;
    BD_OVERLAY event{};
    event.plane=BD_OVERLAY_IG; event.cmd=BD_OVERLAY_INIT; event.w=4; event.h=1;
    state.OnOverlay(&event);
    auto& p=state.planes[BD_OVERLAY_IG];
    auto blank=[&] { for(size_t i=3;i<p.pixels.size();i+=4) assert(!p.pixels[i]); };
    blank();
    std::array<BD_PG_PALETTE_ENTRY,256> palette{};
    palette[1]={159,128,128,64}; palette[255]={235,128,128,255};
    BD_PG_RLE_ELEM run{4,1};
    event.cmd=BD_OVERLAY_DRAW; event.img=&run; event.palette=palette.data();
    state.OnOverlay(&event);
    assert(p.pixels[0]==159 && p.pixels[1]==128 && p.pixels[2]==128 && p.pixels[3]==64);
    // Reuse the index with another palette in a different region.
    event.x=2; event.w=2; run.len=2; palette[1]={16,128,128,255};
    state.OnOverlay(&event);
    assert(p.pixels[0]==159 && p.pixels[4]==159 && p.pixels[8]==16 && p.pixels[12]==16);
    // A palette-only redraw is restricted to the requested rectangle.
    event.img=nullptr; event.w=1; palette[1]={235,128,128,255};
    state.OnOverlay(&event);
    assert(p.pixels[0]==159 && p.pixels[4]==159 && p.pixels[8]==235 && p.pixels[12]==16);
    BLURAY_STREAM_INFO video{};
    BLURAY_CLIP_INFO clip{}; clip.video_stream_count=1; clip.video_streams=&video;
    BLURAY_TITLE_INFO title{}; title.clip_count=1; title.clips=&clip;
    state.title=&title;
    std::array<uint8_t,16> sdr{}, hdr{}, restored{};
    BlurayMenuColor::CopyYcbcrToOsd(sdr.data(),p.pixels.data(),p.pixels.size(),false);
    assert(sdr[0]==167 && sdr[3]==64 && sdr[8]==255 && sdr[12]==0);
    video.color_space=BLURAY_COLOR_SPACE_BT2020;
    video.dynamic_range_type=BLURAY_DYNAMIC_RANGE_HDR10;
    p.dirty=false; state.Present(); // HDMV: bdjActive remains false.
    assert(state.graphicsPq2020 && p.dirty && !state.presenting);
    BlurayMenuColor::CopyYcbcrToOsd(hdr.data(),p.pixels.data(),p.pixels.size(),state.graphicsPq2020);
    assert(hdr[0]==255 && hdr[3]==64 && hdr[8]==255 && hdr[12]==0);
    video.color_space=BLURAY_COLOR_SPACE_BT709;
    p.dirty=false; state.Present();
    assert(!state.graphicsPq2020 && p.dirty);
    BlurayMenuColor::CopyYcbcrToOsd(restored.data(),p.pixels.data(),p.pixels.size(),state.graphicsPq2020);
    assert(restored==sdr);
    event.cmd=BD_OVERLAY_WIPE; state.OnOverlay(&event);
    assert(p.pixels[3]==64 && p.pixels[11]==0 && p.pixels[15]==255);
    event.cmd=BD_OVERLAY_DRAW; event.img=&run; run.len=1; run.color=255;
    state.OnOverlay(&event); assert(!p.pixels[11] && p.indices[2]==255);
    event.cmd=BD_OVERLAY_CLEAR; state.OnOverlay(&event); blank();
    event.cmd=BD_OVERLAY_DRAW; run.color=1; state.OnOverlay(&event); assert(p.pixels[11]==255);
    event.cmd=BD_OVERLAY_HIDE; state.OnOverlay(&event); blank();
    event.cmd=BD_OVERLAY_FLUSH; event.pts=123; state.OnOverlay(&event);
    assert(p.dirty && p.flushPts==123);
    event.cmd=BD_OVERLAY_CLOSE; state.OnOverlay(&event);
    assert(!p.width && !p.height && p.dirty && p.flushPts==-1 && !state.error);
    puts("PASS: actual HC Paint/OnOverlay, regional palette retention, HDMV HDR/SDR metadata, alpha, wipe/clear/hide/close");
}
'''
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)
cpp = out / 'hdmv-overlay-color.cpp'
exe = cpp.with_suffix('.exe')
cpp.write_text(fixture.replace('// PRODUCTION', code), encoding='utf-8')
subprocess.run(['cl.exe', '/nologo', '/EHsc', '/std:c++17', '/MT', '/W4', '/O2',
                '/DNOMINMAX', '/I' + str(root / 'src/mpc-hc'),
                '/I' + str(root / 'bluray/out/libbluray-1.5.0-x64/include'),
                '/Fe:' + str(exe), str(cpp)], cwd=out, check=True)
subprocess.run([str(exe)], check=True)
