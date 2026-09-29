"""Check a built libbluray DLL with four tiny synthetic playlist clips.

Exercises the bd_read API used by LAV, without a renderer, Java or user media.
The fixture is for byte reading only; it does not contain decodable video/menus.
"""
import argparse
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile


def check(dll, directory):
    spec = importlib.util.spec_from_file_location(
        'fixture', Path(__file__).with_name('make-read-error-fixture.py'))
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    root = directory / 'disc'
    for name in ('STREAM', 'CLIPINF', 'PLAYLIST'):
        (root / 'BDMV' / name).mkdir(parents=True)
    expected = bytearray()
    clips = []
    for index in range(4):
        name = f'{index:05d}'
        # 64 unencrypted null transport packets, 12288 bytes per clip.
        data = b''.join(bytes(4) + b'\x47\x1f\xff' + bytes([0x10 | (n % 16)])
                        + bytes([0x30 + index]) * 184 for n in range(64))
        expected.extend(data)
        (root / f'BDMV/STREAM/{name}.m2ts').write_bytes(data)
        (root / f'BDMV/CLIPINF/{name}.clpi').write_bytes(fixture.clpi(64, 0, 45000))
        clips.append((name, 0, 45000))
    (root / 'BDMV/PLAYLIST/00000.mpls').write_bytes(fixture.playlist(clips))

    lib = ctypes.CDLL(str(dll))
    lib.bd_open.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    lib.bd_open.restype = ctypes.c_void_p
    lib.bd_close.argtypes = [ctypes.c_void_p]
    lib.bd_close.restype = None
    lib.bd_select_playlist.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    lib.bd_select_playlist.restype = ctypes.c_int
    lib.bd_read.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
    lib.bd_read.restype = ctypes.c_int
    lib.bd_get_title_size.argtypes = [ctypes.c_void_p]
    lib.bd_get_title_size.restype = ctypes.c_uint64
    requests = (1, 191, 192, 193, 6143, 6144, 6145, 12287, 12288, 12289,
                24576, 49152, 122880)
    read_calls = 0
    for count in requests:
        bd = lib.bd_open(str(root).encode('utf-8'), None)
        if not bd:
            raise RuntimeError('bd_open failed for generated fixture')
        try:
            assert lib.bd_select_playlist(bd, 0) == 1
            assert lib.bd_get_title_size(bd) == len(expected)
            actual = bytearray()
            # Extra trailing space catches the donor's cumulative-offset bug
            # without deliberately writing into unrelated process memory.
            buffer = (ctypes.c_ubyte * (64 + count * 4 + 64))()
            for _ in range(len(expected) + 2):
                ctypes.memset(buffer, 0xcd, len(buffer))
                got = lib.bd_read(bd, ctypes.byref(buffer, 64), count)
                read_calls += 1
                assert 0 <= got <= count, (count, got)
                view = bytes(buffer)
                assert view[:64] == b'\xcd' * 64, ('prefix guard', count)
                assert view[64 + got:] == b'\xcd' * (len(buffer) - 64 - got), ('suffix guard', count, got)
                actual.extend(view[64:64 + got])
                assert len(actual) <= len(expected), ('extra data', count)
                if got == 0:
                    break
            else:
                raise AssertionError('read did not reach EOF')
            assert actual == expected, ('playlist bytes', count, len(actual))
        finally:
            lib.bd_close(bd)
    return {'dll_sha256': hashlib.sha256(dll.read_bytes()).hexdigest(),
            'clips': 4, 'bytes_per_clip': 12288, 'request_sizes': list(requests),
            'read_calls': read_calls, 'exact_bytes_and_guards': 'pass'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dll', required=True, type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bluray-multipart-') as temp:
        result = check(args.dll.resolve(strict=True), Path(temp))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
