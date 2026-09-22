// Local COM smoke test: no registration, video window, audio output or profile writes.
#include <windows.h>
#include <dshow.h>
#include <atlbase.h>
#include <cstdio>
#include <string>
#include <IBlurayStreamSelect.h>
#include <LAVSplitterSettings.h>
#include <LAVVideoSettings.h>

static void check(HRESULT hr, const char* operation) {
    if (FAILED(hr)) {
        std::fprintf(stderr, "%s: 0x%08lx\n", operation, hr);
        std::exit(1);
    }
}
static CComPtr<IBaseFilter> create(const std::wstring& file, const wchar_t* clsid) {
    HMODULE module = LoadLibraryExW(file.c_str(), nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    if (!module) check(HRESULT_FROM_WIN32(GetLastError()), "load LAV DLL");
    auto get = reinterpret_cast<HRESULT(STDAPICALLTYPE*)(REFCLSID, REFIID, void**)>(GetProcAddress(module, "DllGetClassObject"));
    if (!get) check(E_NOINTERFACE, "DllGetClassObject");
    CLSID id; check(CLSIDFromString(clsid, &id), "CLSID");
    CComPtr<IClassFactory> factory;
    check(get(id, IID_PPV_ARGS(&factory)), "factory");
    CComPtr<IBaseFilter> filter;
    check(factory->CreateInstance(nullptr, IID_PPV_ARGS(&filter)), "create LAV filter");
    return filter;
}
static CComPtr<IPin> pin(IBaseFilter* filter, PIN_DIRECTION wanted) {
    CComPtr<IEnumPins> pins; check(filter->EnumPins(&pins), "enum pins");
    CComPtr<IPin> item;
    while (pins->Next(1, &item, nullptr) == S_OK) {
        PIN_DIRECTION direction;
        check(item->QueryDirection(&direction), "pin direction");
        if (direction == wanted) return item;
        item.Release();
    }
    check(E_FAIL, "missing pin"); return nullptr;
}
int wmain(int argc, wchar_t** argv) {
    if (argc != 3) return 2;
    check(CoInitializeEx(nullptr, COINIT_MULTITHREADED), "COM");
    SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    AddDllDirectory(argv[1]);
    const std::wstring folder = std::wstring(argv[1]) + L"\\";
    auto source = create(folder + L"LAVSplitter.ax", L"{B98D13E7-55DB-4385-A33D-09FD1BA26338}");
    auto decoder = create(folder + L"LAVVideo.ax", L"{EE30215D-164F-4A92-A4EB-9D4C13390F9F}");
    CComQIPtr<ILAVFSettings> sourceSettings(source);
    CComQIPtr<ILAVVideoSettings> videoSettings(decoder);
    if (!sourceSettings || !videoSettings) check(E_NOINTERFACE, "runtime settings");
    check(sourceSettings->SetRuntimeConfig(TRUE), "splitter runtime settings");
    check(videoSettings->SetRuntimeConfig(TRUE), "decoder runtime settings");
    check(videoSettings->SetHWAccel(HWAccel_None), "software decoder");
    CComQIPtr<IBlurayStreamSelect> mapping(source);
    CComQIPtr<IBlurayPlaybackControl> control(source);
    if (!mapping || !control) check(E_NOINTERFACE, "Blu-ray adapter interfaces");
    CComQIPtr<IFileSourceFilter> file(source);
    check(file->Load(argv[2], nullptr), "load canvas MKV");
    CComQIPtr<IAMStreamSelect> streams(source);
    DWORD count = 0;
    check(streams->Count(&count), "stream count");
    if (!count) check(E_FAIL, "empty source");
    DWORD index, group, ordinal;
    if (mapping->FindStream(0x1100, &index, &group, &ordinal) != VFW_E_NOT_FOUND) check(E_FAIL, "non-TS PID lookup");
    if (control->SetPlayItemStop(1) != E_NOTIMPL) check(E_FAIL, "non-BD play item limit");
    CComPtr<IGraphBuilder> graph;
    check(graph.CoCreateInstance(CLSID_FilterGraph), "graph");
    CComPtr<IBaseFilter> sink;
    // DirectShow Null Renderer CLSID, explicitly avoids any video renderer.
    CLSID nullRenderer; check(CLSIDFromString(L"{C1F400A4-3F08-11D3-9F0B-006008039E37}", &nullRenderer), "sink CLSID");
    check(sink.CoCreateInstance(nullRenderer), "null renderer");
    check(graph->AddFilter(source, L"Local LAV source"), "add source");
    check(graph->AddFilter(decoder, L"Local LAV software decoder"), "add decoder");
    check(graph->AddFilter(sink, L"Null output"), "add sink");
    check(graph->ConnectDirect(pin(source, PINDIR_OUTPUT), pin(decoder, PINDIR_INPUT), nullptr), "connect source");
    check(graph->ConnectDirect(pin(decoder, PINDIR_OUTPUT), pin(sink, PINDIR_INPUT), nullptr), "connect decoder");
    CComQIPtr<IMediaFilter> mediaFilter(graph);
    check(mediaFilter->SetSyncSource(nullptr), "disable playback clock for decode test");
    CComQIPtr<IMediaControl> media(graph);
    CComQIPtr<IMediaEvent> events(graph);
    check(media->Run(), "run");
    long event = 0;
    check(events->WaitForCompletion(15000, &event), "decode completion");
    check(media->Stop(), "stop");
    if (event != EC_COMPLETE) check(E_FAIL, "decode end event");
    std::puts("PASS: local LAV COM interfaces, MKV demux, software decode and EOS through Null Renderer.");
    return 0;
}
