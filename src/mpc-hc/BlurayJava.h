// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <windows.h>
#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace BlurayJava {
namespace fs = std::filesystem;
enum class Status { Missing, Invalid, WrongArchitecture, Ready };
#if defined(_M_ARM64)
inline constexpr WORD Machine = IMAGE_FILE_MACHINE_ARM64;
#elif defined(_WIN64)
inline constexpr WORD Machine = IMAGE_FILE_MACHINE_AMD64;
#else
inline constexpr WORD Machine = IMAGE_FILE_MACHINE_I386;
#endif
inline Status Image(const fs::path& path, bool dll) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input) return Status::Missing;
    const auto size = uint64_t(std::streamoff(input.tellg()));
    IMAGE_DOS_HEADER dos{}; input.seekg(0);
    if (!input.read(reinterpret_cast<char*>(&dos), sizeof(dos)) || dos.e_magic != IMAGE_DOS_SIGNATURE
        || dos.e_lfanew < int64_t(sizeof(dos)) || dos.e_lfanew > 1024 * 1024
        || uint64_t(dos.e_lfanew) + sizeof(DWORD) + sizeof(IMAGE_FILE_HEADER) + sizeof(WORD) > size)
        return Status::Invalid;
    input.seekg(dos.e_lfanew);
    DWORD signature = 0; IMAGE_FILE_HEADER header{}; WORD magic = 0;
    if (!input.read(reinterpret_cast<char*>(&signature), sizeof(signature)) || signature != IMAGE_NT_SIGNATURE
        || !input.read(reinterpret_cast<char*>(&header), sizeof(header))
        || !input.read(reinterpret_cast<char*>(&magic), sizeof(magic)) || !header.NumberOfSections
        || !(header.Characteristics & IMAGE_FILE_EXECUTABLE_IMAGE)
        || bool(header.Characteristics & IMAGE_FILE_DLL) != dll
        || (magic != IMAGE_NT_OPTIONAL_HDR32_MAGIC && magic != IMAGE_NT_OPTIONAL_HDR64_MAGIC)
        || header.SizeOfOptionalHeader < (magic == IMAGE_NT_OPTIONAL_HDR64_MAGIC ? sizeof(IMAGE_OPTIONAL_HEADER64) : sizeof(IMAGE_OPTIONAL_HEADER32))
        || uint64_t(dos.e_lfanew) + sizeof(DWORD) + sizeof(header) + header.SizeOfOptionalHeader
            + uint64_t(header.NumberOfSections) * sizeof(IMAGE_SECTION_HEADER) > size)
        return Status::Invalid;
    if (header.Machine != Machine || (magic == IMAGE_NT_OPTIONAL_HDR64_MAGIC) != (sizeof(void*) == 8))
        return Status::WrongArchitecture;
    return Status::Ready;
}
struct Installation {
    Status status = Status::Missing;
    fs::path jvm, launcher;
};
inline Installation Inspect(const fs::path& home) {
    Installation result;
    if (home.empty()) return result;
    for (const auto folder : {L"bin", L"jre/bin"}) {
        const auto jvm = home / folder / L"server/jvm.dll";
        const auto attributes = GetFileAttributesW(jvm.c_str());
        if (attributes == INVALID_FILE_ATTRIBUTES || (attributes & FILE_ATTRIBUTE_DIRECTORY)) continue;
        result.jvm = jvm; result.launcher = home / folder / L"java.exe";
        result.status = Image(jvm, true);
        return result;
    }
    return result;
}

// Run only on explicit request, outside the player. Polling never waits for Java.
// The job bounds the lifetime of descendants, including when the page is closed.
class Probe {
    HANDLE m_job = nullptr, m_process = nullptr, m_read = nullptr;
    ULONGLONG m_deadline = 0;
    static void Close(HANDLE& handle) { if (handle && handle != INVALID_HANDLE_VALUE) CloseHandle(handle); handle = nullptr; }
public:
    enum class Result { Idle, Running, Passed, Failed, TimedOut, TooMuchOutput };
    Result result = Result::Idle;
    DWORD error = 0, exitCode = 0;
    std::string output;
    Probe() = default;
    Probe(const Probe&) = delete;
    Probe& operator=(const Probe&) = delete;
    ~Probe() { Cancel(); }
    void Cancel() {
        Close(m_job); Close(m_process); Close(m_read);
        if (result == Result::Running) result = Result::Idle;
    }
    bool Start(const fs::path& launcher, DWORD timeoutMs = 10000) {
        Cancel(); output.clear(); error = exitCode = 0; result = Result::Failed;
        if (!launcher.is_absolute() || launcher.wstring().find(L'"') != std::wstring::npos) { error = ERROR_INVALID_NAME; return false; }
        SECURITY_ATTRIBUTES security{sizeof(security), nullptr, TRUE};
        HANDLE write = nullptr, input = INVALID_HANDLE_VALUE;
        STARTUPINFOEXW startup{}; startup.StartupInfo.cb = sizeof(startup);
        std::vector<unsigned char> attributes;
        bool initialized = false;
        auto cleanup = [&] {
            if (initialized) DeleteProcThreadAttributeList(startup.lpAttributeList);
            Close(write); Close(input);
        };
        auto fail = [&] { error = GetLastError(); cleanup(); Cancel(); return false; };
        m_job = CreateJobObjectW(nullptr, nullptr);
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        if (!m_job || !SetInformationJobObject(m_job, JobObjectExtendedLimitInformation, &limits, sizeof(limits))
            || !CreatePipe(&m_read, &write, &security, 0) || !SetHandleInformation(m_read, HANDLE_FLAG_INHERIT, 0)) return fail();
        input = CreateFileW(L"NUL", GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, &security, OPEN_EXISTING, 0, nullptr);
        if (input == INVALID_HANDLE_VALUE) return fail();
        SIZE_T bytes = 0;
        InitializeProcThreadAttributeList(nullptr, 1, 0, &bytes); attributes.resize(bytes);
        startup.lpAttributeList = reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(attributes.data());
        if (!InitializeProcThreadAttributeList(startup.lpAttributeList, 1, 0, &bytes)) return fail();
        initialized = true;
        HANDLE handles[] = {input, write};
        if (!UpdateProcThreadAttribute(startup.lpAttributeList, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST, handles, sizeof(handles), nullptr, nullptr)) return fail();
        startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
        startup.StartupInfo.hStdInput = input;
        startup.StartupInfo.hStdOutput = startup.StartupInfo.hStdError = write;
        // Diagnostic options must not be replaced by environment-supplied agents.
        std::vector<wchar_t> environment;
        if (auto* block = GetEnvironmentStringsW()) {
            for (auto* item = block; *item; item += wcslen(item) + 1) {
                if (!_wcsnicmp(item, L"JAVA_TOOL_OPTIONS=", 18) || !_wcsnicmp(item, L"_JAVA_OPTIONS=", 14)
                    || !_wcsnicmp(item, L"JDK_JAVA_OPTIONS=", 17)) continue;
                environment.insert(environment.end(), item, item + wcslen(item) + 1);
            }
            FreeEnvironmentStringsW(block);
        } else return fail();
        environment.push_back(0);
        std::wstring command = L"\"" + launcher.wstring() + L"\" -version";
        PROCESS_INFORMATION process{};
        if (!CreateProcessW(launcher.c_str(), command.data(), nullptr, nullptr, TRUE,
                CREATE_SUSPENDED | CREATE_NO_WINDOW | EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT,
                environment.data(), launcher.parent_path().c_str(), &startup.StartupInfo, &process)) return fail();
        m_process = process.hProcess;
        if (!AssignProcessToJobObject(m_job, m_process) || ResumeThread(process.hThread) == DWORD(-1)) {
            const auto saved = GetLastError(); TerminateProcess(m_process, 1); CloseHandle(process.hThread);
            SetLastError(saved); return fail();
        }
        CloseHandle(process.hThread); cleanup();
        m_deadline = GetTickCount64() + timeoutMs; result = Result::Running; return true;
    }
    Result Poll() {
        if (result != Result::Running) return result;
        const bool exited = WaitForSingleObject(m_process, 0) == WAIT_OBJECT_0;
        DWORD available = 0;
        while (PeekNamedPipe(m_read, nullptr, 0, nullptr, &available, nullptr) && available) {
            char bytes[4096]; DWORD count = 0;
            if (!ReadFile(m_read, bytes, (std::min)(available, DWORD(sizeof(bytes))), &count, nullptr) || !count) break;
            if (output.size() + count > 64 * 1024) { result = Result::TooMuchOutput; Cancel(); return result; }
            output.append(bytes, count);
        }
        if (exited) {
            if (!GetExitCodeProcess(m_process, &exitCode)) { error = GetLastError(); result = Result::Failed; }
            else result = exitCode == 0 ? Result::Passed : Result::Failed;
        } else if (GetTickCount64() >= m_deadline) result = Result::TimedOut;
        if (result != Result::Running) Cancel();
        return result;
    }
};
}
