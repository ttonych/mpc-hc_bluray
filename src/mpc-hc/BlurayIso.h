// SPDX-License-Identifier: GPL-3.0-or-later
// Native ISO mounting adapted from MPC-BE DiskImage.cpp (2014-2023, Authors.txt),
// donor 270cfdd4369224dd4108d0b1d1b8a4ab7b8fc56d. See bluray/imports.json.
#pragma once
#include <windows.h>
#include <virtdisk.h>
#include <winioctl.h>
#include <atlstr.h>
#include <shlwapi.h>

class CBlurayIso {
    HMODULE m_module = nullptr;
    HANDLE m_disk = INVALID_HANDLE_VALUE;
    CStringW m_root, m_source;

    static bool DeviceNumber(const wchar_t* path, STORAGE_DEVICE_NUMBER& number) {
        const HANDLE device = CreateFileW(path, 0, FILE_SHARE_READ | FILE_SHARE_WRITE,
            nullptr, OPEN_EXISTING, 0, nullptr);
        if (device == INVALID_HANDLE_VALUE) return false;
        DWORD bytes = 0;
        const bool ok = DeviceIoControl(device, IOCTL_STORAGE_GET_DEVICE_NUMBER,
            nullptr, 0, &number, sizeof(number), &bytes, nullptr) && bytes >= sizeof(number);
        CloseHandle(device);
        return ok;
    }

    static CStringW FindRoot(const STORAGE_DEVICE_NUMBER& disk) {
        const DWORD drives = GetLogicalDrives();
        for (unsigned i = 0; i < 26; ++i) {
            if (!(drives & (1u << i))) continue;
            wchar_t root[] = L"A:\\";
            root[0] += wchar_t(i);
            if (GetDriveTypeW(root) != DRIVE_CDROM) continue;
            wchar_t device[] = L"\\\\.\\A:";
            device[4] = root[0];
            STORAGE_DEVICE_NUMBER candidate{};
            if (DeviceNumber(device, candidate) && candidate.DeviceType == disk.DeviceType
                    && candidate.DeviceNumber == disk.DeviceNumber) return root;
        }
        return CStringW();
    }

public:
    CBlurayIso() = default;
    CBlurayIso(const CBlurayIso&) = delete;
    CBlurayIso& operator=(const CBlurayIso&) = delete;
    ~CBlurayIso() {
        // Only release our handle. Never detach an image mounted by someone else.
        // A new non-permanent attachment ends when its last owning handle closes.
        if (m_disk && m_disk != INVALID_HANDLE_VALUE) CloseHandle(m_disk);
        if (m_module) FreeLibrary(m_module);
    }

    static bool IsImage(const CStringW& path) {
        return !path.IsEmpty() && !PathIsURLW(path)
            && !CStringW(PathFindExtensionW(path)).CompareNoCase(L".iso");
    }

    bool Contains(const CStringW& path) const {
        CStringW normal(path);
        normal.Replace(L'/', L'\\');
        return !m_root.IsEmpty() && normal.Left(m_root.GetLength()).CompareNoCase(m_root) == 0;
    }
    const CStringW& Root() const { return m_root; }
    const CStringW& Source() const { return m_source; }

    DWORD Open(const CStringW& path) {
        if (m_disk != INVALID_HANDLE_VALUE || !IsImage(path)) return ERROR_INVALID_PARAMETER;
        wchar_t absolute[32768]{};
        const DWORD length = GetFullPathNameW(path, _countof(absolute), absolute, nullptr);
        if (!length) return GetLastError();
        if (length >= _countof(absolute)) return ERROR_FILENAME_EXCED_RANGE;
        m_source = absolute;
        m_module = LoadLibraryExW(L"virtdisk.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
        if (!m_module) return GetLastError();
        const auto open = reinterpret_cast<decltype(&OpenVirtualDisk)>(GetProcAddress(m_module, "OpenVirtualDisk"));
        const auto attach = reinterpret_cast<decltype(&AttachVirtualDisk)>(GetProcAddress(m_module, "AttachVirtualDisk"));
        const auto physical = reinterpret_cast<decltype(&GetVirtualDiskPhysicalPath)>(GetProcAddress(m_module, "GetVirtualDiskPhysicalPath"));
        if (!open || !attach || !physical) return ERROR_NOT_SUPPORTED;

        VIRTUAL_STORAGE_TYPE storage{};
        storage.DeviceId = VIRTUAL_STORAGE_TYPE_DEVICE_ISO;
        // SDK Microsoft virtual-storage provider GUID, without a static DLL dependency.
        storage.VendorId = {0xec984aec, 0xa0f9, 0x47e9, {0x90, 0x1f, 0x71, 0x41, 0x5a, 0x66, 0x34, 0x5b}};
        OPEN_VIRTUAL_DISK_PARAMETERS parameters{};
        parameters.Version = OPEN_VIRTUAL_DISK_VERSION_1;
        DWORD result = open(&storage, m_source, VIRTUAL_DISK_ACCESS_READ,
            OPEN_VIRTUAL_DISK_FLAG_NONE, &parameters, &m_disk);
        if (result != ERROR_SUCCESS) return result;

        wchar_t device[32768]{};
        ULONG bytes = sizeof(device); // This API takes bytes, not wchar_t elements.
        result = physical(m_disk, &bytes, device);
        if (result != ERROR_SUCCESS) {
            ATTACH_VIRTUAL_DISK_PARAMETERS options{};
            options.Version = ATTACH_VIRTUAL_DISK_VERSION_1;
            result = attach(m_disk, nullptr, ATTACH_VIRTUAL_DISK_FLAG_READ_ONLY,
                0, &options, nullptr);
            if (result != ERROR_SUCCESS) return result;
            bytes = sizeof(device);
            result = physical(m_disk, &bytes, device);
            if (result != ERROR_SUCCESS) return result;
        }

        STORAGE_DEVICE_NUMBER number{};
        if (!DeviceNumber(device, number)) return ERROR_NOT_READY;
        // Drive-letter notification can lag behind a successful attachment.
        for (unsigned attempt = 0; attempt < 50; ++attempt) {
            m_root = FindRoot(number);
            if (!m_root.IsEmpty()) return ERROR_SUCCESS;
            Sleep(100);
        }
        return ERROR_NOT_READY;
    }
};
