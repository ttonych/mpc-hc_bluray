"""Compile LAV's actual parser/still methods against deterministic packet fixtures.

The fixtures exercise eligibility, cadence, cancellation, errors and cache lifetime;
they do not claim to test FFmpeg decoding or a renderer. Run the runtime checks too.
"""
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
lav = root / 'src/thirdparty/LAVFilters/src'
source = (lav / 'decoder/LAVVideo/decoders/avcodec.cpp').read_text()


def method(signature):
    start = source.index(signature)
    brace = source.index('{', start)
    end, depth = brace + 1, 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


code = r'''
#include <windows.h>
#include <cstdint>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
#include <limits>
using REFERENCE_TIME = int64_t;
constexpr int64_t AV_NOPTS_VALUE = INT64_MIN, UNITS = 10000000;
constexpr int AV_CODEC_ID_MPEG2VIDEO = 2, AV_PICTURE_TYPE_I = 1;
constexpr int AV_INPUT_BUFFER_PADDING_SIZE = 64;
#define DbgLog(...) ((void)0)
struct IMediaSample { bool preroll = false; HRESULT IsPreroll() { return preroll ? S_OK : S_FALSE; } };
struct Parser { int pict_type = AV_PICTURE_TYPE_I; };
struct Context {};
struct AVPacket { std::vector<BYTE> data; int64_t pts = AV_NOPTS_VALUE; };
int packets = 0;
AVPacket* av_packet_alloc() { ++packets; return new AVPacket; }
void av_packet_free(AVPacket** p) { delete *p; *p = nullptr; --packets; }
void* av_fast_realloc(void*, unsigned*, size_t) { assert(false); return nullptr; }
int av_parser_parse2(Parser*, Context*, uint8_t** out, int* len, const uint8_t* in,
                     int size, int64_t, int64_t, int) {
    *out = const_cast<uint8_t*>(in); *len = size; return size;
}
struct Callback { bool flushing = false; BOOL IsInputFlushing() { return flushing; } };
struct Recorded { std::vector<BYTE> data; int64_t start, stop; };
class CDecAvcodec {
public:
    std::vector<BYTE> m_mpeg2StillPacket;
    REFERENCE_TIME m_rtMpeg2Still = AV_NOPTS_VALUE, m_rtStartCache = AV_NOPTS_VALUE;
    Parser parser; Context context; Callback callback;
    Parser* m_pParser = &parser;
    Context* m_pAVCtx = &context;
    Callback* m_pCallback = &callback;
    int m_nCodecId = AV_CODEC_ID_MPEG2VIDEO;
    bool m_bInputPadded = true;
    BYTE* m_pFFBuffer = nullptr; unsigned m_nFFBufferSize = 0;
    REFERENCE_TIME step = 417083;
    int failAt = -1, cancelAt = -1;
    std::vector<Recorded> decoded;
    REFERENCE_TIME GetFrameDuration() { return step; }
    HRESULT FillAVPacketData(AVPacket* p, const BYTE* b, int n, IMediaSample*, bool) {
        p->data.assign(b, b + n); return S_OK;
    }
    HRESULT DecodePacket(AVPacket* p, REFERENCE_TIME a, REFERENCE_TIME b) {
        if (int(decoded.size()) == failAt) return E_FAIL;
        decoded.push_back({p ? p->data : std::vector<BYTE>{}, a, b});
        if (int(decoded.size()) == cancelAt) callback.flushing = true;
        return S_OK;
    }
    void ClearMpeg2Still();
    HRESULT DecodeMpeg2Still(const BYTE*, int, REFERENCE_TIME, REFERENCE_TIME);
    HRESULT RepeatMpeg2Still(REFERENCE_TIME);
    HRESULT ParsePacket(const BYTE*, int, REFERENCE_TIME, REFERENCE_TIME, IMediaSample*);
    HRESULT feed(int64_t time, bool eos = true, IMediaSample* sample = nullptr) {
        const BYTE picture[] = {0, 0, 1, 0, 0x17, 0, 0, 1, 0xb7};
        return ParsePacket(picture, eos ? sizeof(picture) : 5, time, time + 1, sample);
    }
    size_t pictures() const {
        size_t n = 0; for (const auto& p : decoded) if (p.data.size() > 4) ++n; return n;
    }
};
'''
for signature in ('void CDecAvcodec::ClearMpeg2Still()',
                  'HRESULT CDecAvcodec::DecodeMpeg2Still(',
                  'HRESULT CDecAvcodec::RepeatMpeg2Still(',
                  'STDMETHODIMP CDecAvcodec::ParsePacket('):
    code += method(signature) + '\n'

code += r'''
int main() {
    CDecAvcodec sparse;
    assert(sparse.feed(3) == S_OK && sparse.pictures() == 1);
    const auto original = sparse.decoded.front().data;
    assert(sparse.feed(70070003) == S_OK && sparse.pictures() == 169);
    int count = 0;
    for (const auto& p : sparse.decoded) if (p.data.size() > 4) {
        assert(p.data == original); // Exact compressed picture, no re-encoding.
        if (count < 168) assert(p.start == 3 + count * sparse.step);
        else assert(p.start == 70070003);
        assert(p.stop > p.start);
        ++count;
    }
    // Ordinary MPEG-2, other codecs, non-I pictures and preroll do not repeat.
    for (int mode = 0; mode < 5; ++mode) {
        CDecAvcodec normal; IMediaSample sample;
        if (mode == 1) normal.m_nCodecId = 27;
        if (mode == 2) normal.parser.pict_type = 2;
        if (mode == 3) sample.preroll = true;
        assert(normal.feed(mode == 4 ? -100 : 3, mode != 0, &sample) == S_OK);
        assert(normal.feed(70070003) == S_OK && normal.pictures() == 2);
    }
    for (int64_t next : {int64_t(3), int64_t(-1), int64_t(417086), int64_t(610000003), INT64_MIN}) {
        CDecAvcodec invalid; invalid.feed(3); invalid.RepeatMpeg2Still(next);
        assert(invalid.pictures() == 1);
    }
    for (int64_t step : {int64_t(0), int64_t(-1), int64_t(1)}) {
        CDecAvcodec invalid; invalid.feed(3); invalid.step = step;
        assert(invalid.RepeatMpeg2Still(70070003) == S_OK && invalid.pictures() == 1);
    }
    CDecAvcodec cleared; cleared.feed(3); cleared.ClearMpeg2Still();
    assert(cleared.feed(70070003) == S_OK && cleared.pictures() == 2);
    CDecAvcodec eos; eos.feed(3);
    assert(eos.ParsePacket(nullptr, 0, AV_NOPTS_VALUE, AV_NOPTS_VALUE, nullptr) == S_OK);
    assert(eos.m_mpeg2StillPacket.empty() && eos.m_rtMpeg2Still == AV_NOPTS_VALUE);
    CDecAvcodec cancel; cancel.feed(3); cancel.cancelAt = 4;
    assert(cancel.feed(70070003) == S_FALSE && cancel.pictures() == 2);
    assert(cancel.m_mpeg2StillPacket.empty());
    CDecAvcodec failure; failure.feed(3); failure.failAt = 3;
    assert(failure.feed(70070003) == E_FAIL && failure.m_mpeg2StillPacket.empty());
    CDecAvcodec nearLimit; nearLimit.feed(3);
    nearLimit.m_rtMpeg2Still = INT64_MAX - 70000000;
    assert(nearLimit.RepeatMpeg2Still(INT64_MAX) == S_OK);
    for (const auto& p : nearLimit.decoded) if (p.data.size() > 4)
        assert(p.stop > p.start && p.stop <= INT64_MAX);
    assert(packets == 0);
    puts("PASS: actual LAV parser/still methods: sparse I/EOS cadence, ordinary/preroll exclusion, invalid bounds, cancellation, failure, cache reset, timestamp limits.");
}
'''
# Both entry points must invalidate the cache before decoding a new segment.
for signature in ('STDMETHODIMP CDecAvcodec::Flush()', 'STDMETHODIMP CDecAvcodec::DestroyDecoder()'):
    assert 'ClearMpeg2Still();' in method(signature)
assert shutil.which('cl'), 'Run from the MSVC x64 environment.'
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)
cpp = out / 'lav-mpeg2-stills.cpp'
cpp.write_text(code)
exe = out / 'lav-mpeg2-stills.exe'
subprocess.run(['cl', '/nologo', '/EHsc', '/std:c++17', '/O2', str(cpp), '/Fe:' + str(exe)], cwd=out, check=True)
subprocess.run([str(exe)], check=True)
