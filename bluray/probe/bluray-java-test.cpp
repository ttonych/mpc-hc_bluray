// Artificial PE fixtures and bounded child-process checks. No installed profiles.
#include "../../src/mpc-hc/BlurayJava.h"
#include <iostream>
#include <stdexcept>
using namespace BlurayJava;
static void check(bool ok, const char* message) { if (!ok) throw std::runtime_error(message); }
static void put(const fs::path& path, const std::string& value) { fs::create_directories(path.parent_path()); std::ofstream(path, std::ios::binary) << value; }
static void pe(const fs::path& path, WORD machine = Machine) {
    std::vector<char> bytes(512);
    IMAGE_DOS_HEADER dos{}; dos.e_magic = IMAGE_DOS_SIGNATURE; dos.e_lfanew = 64;
    memcpy(bytes.data(), &dos, sizeof(dos));
    DWORD signature = IMAGE_NT_SIGNATURE; memcpy(bytes.data() + 64, &signature, sizeof(signature));
    IMAGE_FILE_HEADER header{}; header.Machine = machine; header.NumberOfSections = 1;
    header.Characteristics = IMAGE_FILE_DLL | IMAGE_FILE_EXECUTABLE_IMAGE;
    header.SizeOfOptionalHeader = sizeof(IMAGE_OPTIONAL_HEADER64);
    memcpy(bytes.data() + 68, &header, sizeof(header));
    WORD magic = IMAGE_NT_OPTIONAL_HDR64_MAGIC; memcpy(bytes.data() + 88, &magic, sizeof(magic));
    put(path, std::string(bytes.data(), bytes.size()));
}
static Probe::Result finish(Probe& probe) {
    const auto limit = GetTickCount64() + 5000;
    while (probe.Poll() == Probe::Result::Running && GetTickCount64() < limit) Sleep(5);
    check(probe.result != Probe::Result::Running, "test exceeded its own deadline"); return probe.result;
}
int wmain(int argc, wchar_t** argv) {
    try {
        check(argc == 3, "fixture and helper required");
        const fs::path root(argv[1]); check(!fs::exists(root), "fresh fixture required");
        check(Inspect(root).status == Status::Missing, "missing JVM");
        const auto jvm = root / L"bin/server/jvm.dll";
        put(jvm, "not a PE"); check(Inspect(root).status == Status::Invalid, "corrupt JVM");
        pe(jvm, IMAGE_FILE_MACHINE_I386); check(Inspect(root).status == Status::WrongArchitecture, "wrong architecture");
        pe(jvm); check(Inspect(root).status == Status::Ready, "matching architecture");
        const auto java = root / L"bin/java.exe";
        fs::copy_file(argv[2], java); check(Image(java, false) == Status::Ready, "native launcher image");
        check(Image(java, true) == Status::Invalid, "EXE is not a JVM DLL");
        pe(root / L"jdk8/jre/bin/server/jvm.dll");
        check(Inspect(root / L"jdk8").status == Status::Ready, "nested JDK8 runtime");
        Probe probe;
        SetEnvironmentVariableW(L"JAVA_TOOL_OPTIONS", L"diagnostic-test");
        put(root / L"bin/mode.txt", "normal");
        check(probe.Start(java), "start helper");
        check(finish(probe) == Probe::Result::Passed && probe.output.find("fixture Java") != std::string::npos, "capture stderr and successful exit");
        check(GetEnvironmentVariableW(L"JAVA_TOOL_OPTIONS", nullptr, 0) > 0, "parent environment preserved");
        SetEnvironmentVariableW(L"JAVA_TOOL_OPTIONS", nullptr);
        put(root / L"bin/mode.txt", "fail"); check(probe.Start(java), "start failure helper");
        check(finish(probe) == Probe::Result::Failed && probe.exitCode == 17, "nonzero exit propagated");
        put(root / L"bin/mode.txt", "flood"); check(probe.Start(java), "start output flood");
        check(finish(probe) == Probe::Result::TooMuchOutput && probe.output.size() <= 65536, "output bounded");
        put(root / L"bin/mode.txt", "wait"); check(probe.Start(java, 150), "start timed child");
        check(finish(probe) == Probe::Result::TimedOut, "child timeout");
        fs::remove(root / L"bin/pid.txt");
        check(probe.Start(java), "start cancellable child");
        const auto deadline = GetTickCount64() + 2000;
        DWORD pid = 0;
        while (!pid && GetTickCount64() < deadline) { std::ifstream(root / L"bin/pid.txt") >> pid; Sleep(5); }
        HANDLE child = OpenProcess(SYNCHRONIZE, FALSE, pid); check(child != nullptr, "observe own child");
        probe.Cancel(); check(WaitForSingleObject(child, 2000) == WAIT_OBJECT_0, "cancel terminates own job"); CloseHandle(child);
        check(!probe.Start(root / L"absent.exe") && probe.result == Probe::Result::Failed, "start errors reported");
        std::cout << "PASS: JVM PE validation, architecture, JDK8 layout, child environment, stderr, exit, output bound, timeout and cancellation\n";
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
