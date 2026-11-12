"""Check early and late PGS packets with the built LAV FFmpeg. Run in an x64 MSVC shell."""
import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
lav = root / 'src/thirdparty/LAVFilters/src'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--lav', type=Path, default=lav / 'bin_x64', help='directory with the built LAV DLLs')
parser.add_argument('--ffmpeg-root', type=Path, default=lav / 'ffmpeg', help='configured LAV FFmpeg source and import libraries')
parser.add_argument('--ffmpeg', default='ffmpeg', help='FFmpeg executable for generating synthetic inputs')
args = parser.parse_args()
src = args.ffmpeg_root.resolve()
env = dict(os.environ, PATH=str(args.lav.resolve()) + os.pathsep + os.environ['PATH'])
assert shutil.which('cl'), 'Run in an x64 MSVC shell.'

program = r"""
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <libavformat/avformat.h>
#include <libavutil/opt.h>

int main(int argc, char **argv) {
    AVFormatContext *ctx = NULL;
    int64_t default_probe;
    if (argc != 3 || avformat_open_input(&ctx, argv[1], NULL, NULL) < 0 ||
        av_opt_get_int(ctx, "probe_pgs_size", 0, &default_probe) < 0 || default_probe != 1)
        return 1;
    ctx->max_analyze_duration = 30000000;
    ctx->probesize = 75000000;
    ctx->skip_estimate_duration_from_pts = 1;
    if (av_opt_set_int(ctx, "probe_pgs_size", atoi(argv[2]), 0) < 0 ||
        avformat_find_stream_info(ctx, NULL) < 0 || ctx->nb_streams != 2)
        return 2;
    int pg = av_find_best_stream(ctx, AVMEDIA_TYPE_SUBTITLE, -1, -1, NULL, 0);
    int video = av_find_best_stream(ctx, AVMEDIA_TYPE_VIDEO, -1, -1, NULL, 0);
    if (pg < 0 || video < 0 || ctx->streams[pg]->codecpar->codec_id != AV_CODEC_ID_HDMV_PGS_SUBTITLE ||
        ctx->streams[video]->codecpar->width != 320 || ctx->streams[video]->codecpar->height != 180)
        return 3;
    printf("%"PRId64" %d", ctx->pb->bytes_read, ctx->streams[pg]->codecpar->width);
    AVPacket *pkt = av_packet_alloc();
    if (!pkt) return 4;
    int count = 0, ret;
    while ((ret = av_read_frame(ctx, pkt)) >= 0) {
        if (pkt->stream_index == pg) {
            uint64_t hash = UINT64_C(14695981039346656037);
            for (int i = 0; i < pkt->size; ++i)
                hash = (hash ^ pkt->data[i]) * UINT64_C(1099511628211);
            printf(" %"PRId64"/%d/%"PRIx64, pkt->pts, pkt->size, hash);
            ++count;
        }
        av_packet_unref(pkt);
    }
    puts("");
    av_packet_free(&pkt);
    avformat_close_input(&ctx);
    return ret == AVERROR_EOF && count > 0 ? 0 : 5;
}
"""

with tempfile.TemporaryDirectory() as temp:
    work = Path(temp)
    (work / 'probe.c').write_text(program)
    libs = [src / folder / name for folder, name in (
        ('libavformat', 'avformat-lav.lib'), ('libavutil', 'avutil-lav.lib'), ('libavcodec', 'avcodec-lav.lib'))]
    subprocess.run(['cl', '/nologo', '/std:c11', '/MD', '/I' + str(src), 'probe.c', *libs], cwd=work, check=True)
    # An empty presentation at 1920x1080 followed by END, repeated one second later.
    sup = bytearray()
    for pts in (0, 90000):
        pcs = struct.pack('>HHBHBBBB', 1920, 1080, 0x10, 1, 0x80, 0, 0, 0)
        for kind, payload in ((0x16, pcs), (0x80, b'')):
            sup += b'PG' + struct.pack('>IIBH', pts, pts, kind, len(payload)) + payload
    (work / 'test.sup').write_bytes(sup)
    for delay in (0, 8):
        subprocess.run([args.ffmpeg, '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                        'testsrc2=size=320x180:rate=24', '-itsoffset', str(delay), '-f', 'sup', '-i', 'test.sup',
                        '-map', '0:v', '-map', '1:s', '-t', '12', '-c:v', 'mpeg2video', '-threads', '1',
                        '-b:v', '1600k', '-c:s', 'copy', '-mpegts_m2ts_mode', '1', '-f', 'mpegts', 'clip.m2ts'],
                       cwd=work, check=True)
        def run(probe_size):
            return subprocess.check_output([work / 'probe.exe', 'clip.m2ts', str(probe_size)],
                                           cwd=work, env=env, text=True).split()
        baseline, fast = run(1), run(0)
        assert baseline[1] == '1920' and baseline[2:] == fast[2:], (baseline, fast)
        if delay:
            assert fast[1] == '0' and int(fast[0]) * 3 < int(baseline[0]), (baseline, fast)
        print(f'PGS at {delay}s: read {baseline[0]} / {fast[0]} bytes, {len(fast)-2} matching packets')
