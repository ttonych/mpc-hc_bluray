"""Regress authored sparse-frame timing through LAV's actual timestamp filter."""
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
lav = root / 'src/thirdparty/LAVFilters/src'


def block(text, signature):
    start = text.index(signature)
    brace = text.index('{', start)
    end, depth = brace + 1, 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


header = (lav / 'demuxer/Demuxers/BDDemuxer.h').read_text()
splitter = (lav / 'demuxer/LAVSplitter/LAVSplitter.cpp').read_text()
definitions = (lav / 'demuxer/Demuxers/BaseDemuxer.h').read_text()
definitions += (lav / 'demuxer/LAVSplitter/LAVSplitter.h').read_text()
macros = '\n'.join(line for line in definitions.splitlines() if line.startswith(
    ('#define MAX_PTS_SHIFT ', '#define LAVFMT_TS_DISCONT ', '#define LAVFMT_TS_DISCONT_NO_DOWNSTREAM ')))
code = r'''
#include <windows.h>
#include <atomic>
#include <cstdint>
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include <set>
using REFERENCE_TIME = int64_t;
constexpr int64_t AV_NOPTS_VALUE = INT64_MIN;
#define DbgLog(...) ((void)0)
'''
code += macros + '\n'
code += 'struct CBDDemuxer { std::atomic<uint64_t> m_menuReadStop{UINT64_MAX};\n'
code += block(header, 'virtual DWORD GetContainerFlags()') + '\n};\n'
code += r'''
struct Packet { REFERENCE_TIME rtStart, rtStop; int StreamId = 0; };
struct Pin {
    REFERENCE_TIME m_rtPrev = AV_NOPTS_VALUE;
    bool IsSubtitlePin() { return false; }
};
struct Fixture {
    CBDDemuxer* m_pDemuxer;
    REFERENCE_TIME m_rtOffset = AV_NOPTS_VALUE;
    Pin pin;
    std::set<int> m_bDiscontinuitySent;
    int64_t deliver(int64_t time) {
        Packet packet{time, time + 417083};
        auto* pPacket = &packet;
        auto* pPin = &pin;
'''
code += block(splitter, 'if (m_pDemuxer->GetContainerFlags() & LAVFMT_TS_DISCONT)')
code += r'''
        return packet.rtStart;
    }
};
int main() {
    CBDDemuxer demux;
    Fixture ordinary{&demux};
    assert(ordinary.deliver(3) == 3);
    assert(ordinary.deliver(70070003) == 3); // Negative control: original gap repair.
    demux.m_menuReadStop = 19200; // Explicit navigator read limit enables authored time.
    Fixture navigation{&demux};
    assert(navigation.deliver(3) == 3);
    assert(navigation.deliver(70070003) == 70070003);
    assert(navigation.deliver(70487086) == 70487086);
    Fixture seek{&demux};
    assert(seek.deliver(-417083) == -417083); // Preserve decoder preroll after seek.
    assert(seek.deliver(0) == 0);
    assert(seek.deliver(90000000) == 90000000);
    demux.m_menuReadStop = UINT64_MAX;
    Fixture normalAgain{&demux};
    assert(normalAgain.deliver(3) == 3 && normalAgain.deliver(70070003) == 3);
    puts("PASS: authored sparse-frame gaps, seek preroll, and unchanged non-navigation timestamp repair.");
}
'''
assert shutil.which('cl'), 'Run from the MSVC x64 environment.'
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)
source = out / 'lav-navigation-timestamps.cpp'
source.write_text(code)
exe = out / 'lav-navigation-timestamps.exe'
subprocess.run(['cl', '/nologo', '/EHsc', '/std:c++17', '/O2', str(source), '/Fe:' + str(exe)], cwd=out, check=True)
subprocess.run([str(exe)], check=True)
