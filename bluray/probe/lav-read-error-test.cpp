// SPDX-License-Identifier: GPL-3.0-or-later
// Real LAV, process-local ReadFile failures, generated inputs and a memory sink.
// No filter registration, player profiles, renderer or shared storage changes.
#include <windows.h>
#include <dshow.h>
#include <atlbase.h>
#include <streams.h>
#include <MinHook.h>
#include <LAVSplitterSettings.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include <mutex>

HINSTANCE g_hInst = nullptr;
static void check(HRESULT hr, const char* what) {
    if (FAILED(hr)) { std::fprintf(stderr,"%s: 0x%08lx\n",what,hr); std::exit(1); }
}
static CComPtr<IBaseFilter> source(const std::wstring& path) {
    HMODULE mod=LoadLibraryExW(path.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    if (!mod) check(HRESULT_FROM_WIN32(GetLastError()),"load LAV");
    auto get=reinterpret_cast<HRESULT(STDAPICALLTYPE*)(REFCLSID,REFIID,void**)>(GetProcAddress(mod,"DllGetClassObject"));
    if (!get) check(E_NOINTERFACE,"LAV factory export");
    CLSID id; check(CLSIDFromString(L"{B98D13E7-55DB-4385-A33D-09FD1BA26338}",&id),"CLSID");
    CComPtr<IClassFactory> f; check(get(id,IID_PPV_ARGS(&f)),"factory");
    CComPtr<IBaseFilter> result; check(f->CreateInstance(nullptr,IID_PPV_ARGS(&result)),"source"); return result;
}
static CComPtr<IPin> pin(IBaseFilter* f,PIN_DIRECTION wanted) {
    CComPtr<IEnumPins> pins;check(f->EnumPins(&pins),"pins"); CComPtr<IPin> p;
    while(pins->Next(1,&p,nullptr)==S_OK) { PIN_DIRECTION direction;check(p->QueryDirection(&direction),"direction");if(direction==wanted)return p;p.Release(); }
    check(E_FAIL,"missing pin");return nullptr;
}
struct Sample { REFERENCE_TIME start,stop; long size; unsigned long long hash; };
class Sink final : public CBaseRenderer {
public:
    std::vector<Sample> samples;
    Sink(HRESULT* hr):CBaseRenderer(CLSID_NULL,L"Read-error test sink",nullptr,hr) {}
    HRESULT CheckMediaType(const CMediaType* mt) override {return mt->majortype==MEDIATYPE_Video?S_OK:VFW_E_TYPE_NOT_ACCEPTED;}
    HRESULT DoRenderSample(IMediaSample* s) override {
        Sample a{};a.start=a.stop=-1;s->GetTime(&a.start,&a.stop);a.size=s->GetActualDataLength();
        BYTE* data=nullptr;check(s->GetPointer(&data),"sample data");
        a.hash=14695981039346656037ull;
        for(long i=0;i<a.size;++i)a.hash=(a.hash^data[i])*1099511628211ull;
        samples.push_back(a);return S_OK;
    }
};
using ReadFn=BOOL(WINAPI*)(HANDLE,LPVOID,DWORD,LPDWORD,LPOVERLAPPED);
static ReadFn realRead=nullptr;
static std::wstring target;
static std::atomic<bool> armed{false};
static std::atomic<unsigned> injected{0}, attempts{0};
static LONGLONG threshold=0;
static bool persistent=false;
struct IO {LONGLONG offset;DWORD requested,returned,error;};
static std::mutex ioLock;
static std::vector<IO> trace;
static BOOL WINAPI failingRead(HANDLE f,LPVOID buf,DWORD size,LPDWORD got,LPOVERLAPPED ov) {
    if (!armed.load())return realRead(f,buf,size,got,ov);
    wchar_t name[32768];DWORD n=GetFinalPathNameByHandleW(f,name,_countof(name),FILE_NAME_NORMALIZED);
    if(!n||n>=_countof(name)||_wcsicmp(name,target.c_str()))return realRead(f,buf,size,got,ov);
    LARGE_INTEGER zero{},pos{};
    if(ov) {pos.LowPart=ov->Offset;pos.HighPart=ov->OffsetHigh;}
    else if(!SetFilePointerEx(f,zero,&pos,FILE_CURRENT))return realRead(f,buf,size,got,ov);
    ++attempts;
    if(pos.QuadPart>=threshold && (persistent||injected.load()==0)) {
        ++injected;if(got)*got=0;
        {std::lock_guard<std::mutex> guard(ioLock);trace.push_back({pos.QuadPart,size,0,ERROR_CRC});}
        SetLastError(ERROR_CRC);return FALSE;
    }
    BOOL result=realRead(f,buf,size,got,ov);DWORD error=result?ERROR_SUCCESS:GetLastError();
    {std::lock_guard<std::mutex> guard(ioLock);trace.push_back({pos.QuadPart,size,got?*got:0,error});}
    SetLastError(error);return result;
}
int wmain(int argc,wchar_t** argv) {
    // LAV folder, input MPLS/M2TS, target clip, none/once/persistent, byte offset, output prefix.
    if(argc!=7)return 2;
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    check(CoInitializeEx(nullptr,COINIT_MULTITHREADED),"COM");
    SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);AddDllDirectory(argv[1]);
    HANDLE probe=CreateFileW(argv[3],GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,0,nullptr);
    if(probe==INVALID_HANDLE_VALUE)check(HRESULT_FROM_WIN32(GetLastError()),"fixture target");
    wchar_t full[32768];DWORD n=GetFinalPathNameByHandleW(probe,full,_countof(full),FILE_NAME_NORMALIZED);
    if(!n||n>=_countof(full))check(E_FAIL,"target canonical path");target=full;CloseHandle(probe);
    const bool inject=wcscmp(argv[4],L"none")!=0;persistent=wcscmp(argv[4],L"persistent")==0;
    if(inject&&!persistent&&wcscmp(argv[4],L"once"))return 2;
    threshold=_wcstoi64(argv[5],nullptr,10);
    if(MH_Initialize()!=MH_OK||MH_CreateHookApi(L"kernel32.dll","ReadFile",failingRead,reinterpret_cast<void**>(&realRead))!=MH_OK||MH_EnableHook(MH_ALL_HOOKS)!=MH_OK)check(E_FAIL,"ReadFile hook");
    auto src=source(std::wstring(argv[1])+L"\\LAVSplitter.ax");
    CComQIPtr<ILAVFSettings> settings(src);if(!settings)check(E_NOINTERFACE,"settings");check(settings->SetRuntimeConfig(TRUE),"runtime config");
    CComQIPtr<IFileSourceFilter> file(src);check(file->Load(argv[2],nullptr),"load fixture");
    CComPtr<IGraphBuilder> graph;check(graph.CoCreateInstance(CLSID_FilterGraph),"graph");
    HRESULT hr=S_OK;Sink* stats=new Sink(&hr);check(hr,"sink");CComPtr<IBaseFilter> sink=stats;
    check(graph->AddFilter(src,L"Isolated LAV"),"add source");check(graph->AddFilter(sink,L"Memory sink"),"add sink");
    check(graph->ConnectDirect(pin(src,PINDIR_OUTPUT),pin(sink,PINDIR_INPUT),nullptr),"connect");
    CComQIPtr<IMediaFilter> filter(graph);check(filter->SetSyncSource(nullptr),"clock");
    CComQIPtr<IMediaControl> media(graph);CComQIPtr<IMediaEvent> events(graph);CComQIPtr<IMediaSeeking> seek(graph);
    // Explicit seek discards probe look-ahead before faults are armed for delivery.
    LONGLONG zero=0;check(seek->SetPositions(&zero,AM_SEEKING_AbsolutePositioning,nullptr,AM_SEEKING_NoPositioning),"seek start");
    armed=inject;ULONGLONG began=GetTickCount64();check(media->Run(),"run");
    long event=0;HRESULT completion=events->WaitForCompletion(10000,&event);
    ULONGLONG elapsed=GetTickCount64()-began;
    ULONGLONG stopping=GetTickCount64();check(media->Stop(),"stop");
    ULONGLONG stopElapsed=GetTickCount64()-stopping;armed=false;
    FILE* out=nullptr;std::wstring prefix=argv[6];
    _wfopen_s(&out,(prefix+L".samples").c_str(),L"w");if(!out)check(E_FAIL,"sample output");
    for(const auto& s:stats->samples)std::fprintf(out,"%lld,%lld,%ld,%016llx\n",s.start,s.stop,s.size,s.hash);std::fclose(out);
    _wfopen_s(&out,(prefix+L".io").c_str(),L"w");if(!out)check(E_FAIL,"I/O output");
    for(const auto& i:trace)std::fprintf(out,"%lld,%lu,%lu,%lu\n",i.offset,i.requested,i.returned,i.error);std::fclose(out);
    _wfopen_s(&out,(prefix+L".json").c_str(),L"w");if(!out)check(E_FAIL,"result output");
    std::fprintf(out,"{\"completion_hr\":%ld,\"event\":%ld,\"elapsed_ms\":%llu,\"stop_ms\":%llu,\"attempts\":%u,\"injected\":%u,\"samples\":%zu}\n",completion,event,elapsed,stopElapsed,attempts.load(),injected.load(),stats->samples.size());std::fclose(out);
    std::printf("event=%ld hr=%08lx samples=%zu injected=%u attempts=%u elapsed=%llums\n",event,completion,stats->samples.size(),injected.load(),attempts.load(),elapsed);
    MH_DisableHook(MH_ALL_HOOKS);MH_Uninitialize();
    if(FAILED(completion)|| (inject&&!injected))return 1;
    // Keep the same graph and demuxer, remove the injected storage fault and
    // explicitly restart. A stale read-error latch must not poison the session.
    if(persistent) {
        stats->samples.clear();
        check(seek->SetPositions(&zero,AM_SEEKING_AbsolutePositioning,nullptr,AM_SEEKING_NoPositioning),"recovery seek");
        check(media->Run(),"recovery run");event=0;
        check(events->WaitForCompletion(10000,&event),"recovery completion");check(media->Stop(),"recovery stop");
        if(event!=EC_COMPLETE)check(E_FAIL,"recovery event");
        _wfopen_s(&out,(prefix+L".recovered.samples").c_str(),L"w");if(!out)check(E_FAIL,"recovery output");
        for(const auto& s:stats->samples)std::fprintf(out,"%lld,%lld,%ld,%016llx\n",s.start,s.stop,s.size,s.hash);std::fclose(out);
    }
    return 0;
}
