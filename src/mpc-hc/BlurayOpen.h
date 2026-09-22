// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <afxstr.h>
#include <shlwapi.h>

namespace BlurayOpen {
// Only disc entry points select navigation. Individual playlists/clips and DVDs
// keep the ordinary HC path, including playlists opened by the navigator itself.
inline bool DiscRoot(CStringW path, CStringW& root) {
    root.Empty();
    if (path.IsEmpty() || PathIsURLW(path)) return false;
    path.Replace(L'/', L'\\');
    wchar_t absolute[32768]{};
    const DWORD length = GetFullPathNameW(path, _countof(absolute), absolute, nullptr);
    if (!length || length >= _countof(absolute)) return false;
    path = absolute;
    const DWORD attributes = GetFileAttributesW(path);
    if (attributes == INVALID_FILE_ATTRIBUTES) return false;
    if (!(attributes & FILE_ATTRIBUTE_DIRECTORY)) {
        const CStringW name(PathFindFileNameW(path));
        if (name.CompareNoCase(L"index.bdmv") && name.CompareNoCase(L"MovieObject.bdmv")) return false;
        path.Truncate(path.ReverseFind(L'\\'));
        if (CStringW(PathFindFileNameW(path)).CompareNoCase(L"BDMV")) return false;
    }
    path.TrimRight(L"\\");
    if (CStringW(PathFindFileNameW(path)).CompareNoCase(L"BDMV") == 0
            && PathFileExistsW(path + L"\\index.bdmv")) {
        path.Truncate(path.ReverseFind(L'\\'));
    }
    path += L"\\";
    const DWORD index = GetFileAttributesW(path + L"BDMV\\index.bdmv");
    if (index == INVALID_FILE_ATTRIBUTES || (index & FILE_ATTRIBUTE_DIRECTORY)) return false;
    root = path;
    return true;
}
}
