// SPDX-License-Identifier: GPL-3.0-or-later
#include "BlurayIso.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>

int wmain(int argc, wchar_t** argv)
{
    assert(CBlurayIso::IsImage(L"disc.ISO"));
    assert(CBlurayIso::IsImage(L"folder/disc.iso"));
    for (const auto path : {L"", L"disc.mkv", L"disc.iso.mkv", L"https://example.invalid/disc.iso"}) {
        assert(!CBlurayIso::IsImage(path));
    }
    CBlurayIso invalid;
    assert(invalid.Open(L"ordinary.mkv") == ERROR_INVALID_PARAMETER);
    assert(!invalid.Contains(L"C:\\"));
    puts("PASS: ISO classification and invalid-input rejection");
    if (argc == 2) {
        // Optional local integration check. Never print the supplied private path.
        CStringW root;
        const DWORD drivesBefore = GetLogicalDrives();
        {
            CBlurayIso owner;
            const DWORD error = owner.Open(argv[1]);
            printf("Native ISO open: Windows error %lu\n", error);
            if (error) return 1;
            root = owner.Root();
            assert(GetDriveTypeW(root) == DRIVE_CDROM);
            assert(owner.Contains(root + L"BDMV/index.bdmv"));
            assert(!owner.Contains(L"Z:\\unrelated.mkv"));
            {
                CBlurayIso borrowed;
                assert(borrowed.Open(argv[1]) == ERROR_SUCCESS);
                assert(borrowed.Root() == root);
            }
            assert(GetDriveTypeW(root) == DRIVE_CDROM);
            puts("PASS: closing a second reader preserves the existing attachment");
        }
        const DWORD bit = 1u << (root[0] - L'A');
        if (!(drivesBefore & bit)) {
            for (unsigned i = 0; i < 50 && (GetLogicalDrives() & bit); ++i) Sleep(100);
            assert(!(GetLogicalDrives() & bit));
            puts("PASS: owned attachment released on close");
        } else {
            assert(GetDriveTypeW(root) == DRIVE_CDROM);
            puts("PASS: pre-existing attachment preserved");
        }
    }
}
