"""Check HEVC probe parameters, ordinary decoding and multi-slice fallback in a built LAV codec."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
lav = root / 'src/thirdparty/LAVFilters/src'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--lav', type=Path, default=lav / 'bin_x64')
parser.add_argument('--ffmpeg-root', type=Path, default=lav / 'ffmpeg')
parser.add_argument('--ffmpeg', default='ffmpeg', help='fixture encoder with libx265')
parser.add_argument('--reference-lav', type=Path, help='also compare decoded frames with a previous LAV build')
args = parser.parse_args()

def inspect(path, enabled):
    env = dict(os.environ, PATH=str(path.resolve()) + os.pathsep + os.environ['PATH'])
    text = subprocess.check_output([exe, 'clip.hevc', str(int(enabled))], cwd=work, env=env, text=True)
    probe, playback = text.split('playback\n')
    params = next(line for line in probe.splitlines() if line.startswith('parameters '))
    return probe, playback, params

with tempfile.TemporaryDirectory() as tmp:
    work = Path(tmp)
    exe = work / 'probe.exe'
    src = args.ffmpeg_root.resolve()
    libs = [src / folder / name for folder, name in (
        ('libavformat', 'avformat-lav.lib'), ('libavcodec', 'avcodec-lav.lib'), ('libavutil', 'avutil-lav.lib'))]
    subprocess.run(['cl', '/nologo', '/std:c11', '/MD', '/I' + str(src),
                    root / 'bluray/probe/lav-hevc-probe-test.c', '/Fe:' + str(exe), *libs], cwd=work, check=True)
    for name, fmt, slices in [('SDR', 'yuv420p', 1), ('HDR10', 'yuv420p10le', 1), ('multi-slice', 'yuv420p10le', 2)]:
        params = f'log-level=error:frame-threads=1:pools=2:bframes=0:repeat-headers=1:slices={slices}'
        if name == 'HDR10':
            params += (':colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc:hdr10=1:max-cll=1000,400'
                       ':master-display=G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,5)')
        subprocess.run([args.ffmpeg, '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                        f'testsrc2=size=634x354:rate=24000/1001,setsar=4/3,format={fmt}', '-frames:v', '2',
                        '-c:v', 'libx265', '-preset', 'ultrafast', '-x265-params', params, 'clip.hevc'],
                       cwd=work, check=True)
        regular, normal, expected = inspect(args.lav, False)
        probe, playback, actual = inspect(args.lav, True)
        assert expected == actual and regular == normal == playback and 'frames 1\n' in normal
        if slices == 1:
            assert 'frames 0\n' in probe
        else:
            assert probe == normal
        if name == 'HDR10':
            assert 'Mastering display metadata' in normal and 'Content light level metadata' in normal
        if args.reference_lav:
            assert inspect(args.reference_lav, False)[1] == normal
        print(f'{name}: {actual}, {probe.splitlines()[-1]}, playback matches')
