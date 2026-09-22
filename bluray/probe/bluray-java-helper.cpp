// Child fixture for the Java probe; never installed in a runtime package.
#include <windows.h>
#include <fstream>
#include <iostream>
#include <string>
int main(int argc, char** argv) {
    if (argc != 2 || std::string(argv[1]) != "-version") return 3;
    if (GetEnvironmentVariableW(L"JAVA_TOOL_OPTIONS", nullptr, 0)) return 4;
    std::string mode; std::ifstream("mode.txt") >> mode;
    if (mode == "fail") return 17;
    if (mode == "flood") { for (int i = 0; i < 100000; ++i) std::cerr << "long output from fixture\n"; }
    if (mode == "wait") { std::ofstream("pid.txt") << GetCurrentProcessId(); Sleep(60000); }
    std::cerr << "fixture Java version\n"; return 0;
}
