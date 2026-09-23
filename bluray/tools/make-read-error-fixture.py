"""Generate a synthetic two-clip playlist for LAV I/O tests; no disc content.

Minimal MPLS/CLPI layout follows the pinned libbluray parsers. No CPI map is
needed: both whole clips run from packet zero to num_source_packets. This is a
demuxer fixture, not an authored HDMV/BD-J menu or a conformance test disc.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import subprocess

def u16(n): return struct.pack('>H', n)
def u32(n): return struct.pack('>I', n)
def block(b): return u32(len(b)) + b

def clpi(packets, begin, end):
    clip = block(bytes(2) + b'\x01\x01' + bytes(4) + u32(4000000) + u32(packets) + bytes(128) + u16(0))
    sequence = block(b'\0\1' + u32(0) + b'\1\0' + u16(0x1011) + u32(0) + u32(begin) + u32(end))
    attr = b'\x02\x51\x30\0\0' + bytes(12)
    program = block(b'\0\1' + u32(0) + u16(0x100) + b'\1\0' + u16(0x1011) + bytes([len(attr)]) + attr)
    seq_pos = 40 + len(clip)
    prog_pos = seq_pos + len(sequence)
    cpi_pos = prog_pos + len(program)
    header = b'HDMV0200' + u32(seq_pos) + u32(prog_pos) + u32(cpi_pos) + u32(0) + u32(0)
    return header.ljust(40, b'\0') + clip + sequence + program + u32(0)

def playlist(clips):
    items = b''
    for name,begin,end in clips:
        # One video stream, MPEG-2; no still, angle, audio, subtitle or subpath.
        stream = b'\3\1' + u16(0x1011) + b'\2\x02\x51'
        stn = bytes(2) + b'\1' + bytes(7) + bytes(4) + stream
        item = name.encode('ascii') + b'M2TS' + u16(1) + b'\0' + u32(begin) + u32(end) + bytes(12) + u16(len(stn)) + stn
        items += u16(len(item)) + item
    body = block(bytes(2) + u16(len(clips)) + u16(0) + items)
    app = block(b'\0\1' + bytes(12))
    list_pos = 40 + len(app)
    marks = block(u16(len(clips)) + b''.join(b'\0\1'+u16(i)+u32(c[1])+u16(0xffff)+u32(0) for i,c in enumerate(clips)))
    return (b'MPLS0200' + u32(list_pos) + u32(list_pos+len(body)) + u32(0)).ljust(40,b'\0') + app + body + marks

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ffmpeg',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    # Never overwrite arbitrary directories or an earlier fixture.
    a.output.mkdir(parents=True,exist_ok=False)
    for n in ('STREAM','CLIPINF','PLAYLIST'):
        (a.output/'BDMV'/n).mkdir(parents=True)
    clips=[]
    for index in range(2):
        name=f'{index:05d}'
        dest=a.output/'BDMV/STREAM'/f'{name}.m2ts'
        subprocess.run([str(a.ffmpeg),'-v','error','-nostdin','-f','lavfi','-i',
            'testsrc2=size=640x360:rate=24:duration=12', '-vf',f'hue=h={index*120}', '-an','-c:v','mpeg2video',
            '-g','12','-bf','0','-q:v','2','-threads','1','-fflags','+bitexact',
            '-flags:v','+bitexact','-streamid','0:4113','-f','mpegts','-mpegts_m2ts_mode','1',
            '-muxdelay','0','-muxpreload','0','-output_ts_offset',str(index*7),str(dest)],check=True,timeout=60)
        probe=a.ffmpeg.with_name('ffprobe'+a.ffmpeg.suffix)
        info=json.loads(subprocess.check_output([str(probe),'-v','error','-select_streams','v:0',
            '-show_entries','stream=start_time,duration','-of','json',str(dest)],text=True))['streams'][0]
        begin=round(float(info['start_time'])*45000)
        end=begin+round(float(info['duration'])*45000)
        assert dest.stat().st_size%192==0 and dest.stat().st_size>1024*1024
        (a.output/'BDMV/CLIPINF'/f'{name}.clpi').write_bytes(clpi(dest.stat().st_size//192,begin,end))
        clips.append((name,begin,end))
    (a.output/'BDMV/PLAYLIST/00000.mpls').write_bytes(playlist(clips))
    record={'kind':'generated demuxer fixture, no menus','clips':clips,
        'generator_sha256':hashlib.sha256(a.ffmpeg.read_bytes()).hexdigest(),
        'files':{str(f.relative_to(a.output)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest()
                 for f in sorted(a.output.rglob('*')) if f.is_file()}}
    (a.output/'fixture.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({'clips':clips,'files':len(record['files'])}))

if __name__=='__main__': main()
