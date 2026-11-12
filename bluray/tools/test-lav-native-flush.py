"""Exercise the D3D11 decoder's real surface wait and cancellation on Windows."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
out = root / 'bluray/build/tests'
out.mkdir(parents=True, exist_ok=True)
source = root / 'src/thirdparty/LAVFilters/src/decoder/LAVVideo/decoders/d3d11/D3D11SurfaceAllocator.cpp'
text = source.read_text()
start = text.index('HRESULT CD3D11SurfaceAllocator::GetDecoderBuffer(')
method = text[start:text.index('\n}', start) + 2]

harness = r'''
#include <windows.h>
#include <dshow.h>
#include <cassert>
#include <future>
#include <mutex>

struct CD3D11SurfaceAllocator {
    std::mutex mutex;
    HANDLE m_hSem = CreateSemaphore(nullptr, 0, 64, nullptr);
    HANDLE registered = CreateEvent(nullptr, FALSE, FALSE, nullptr);
    long m_lWaiting = 0;
    bool free = false, committed = true;

    HRESULT GetDecoderBuffer(IMediaSample**, HANDLE);
    HRESULT GetBuffer(IMediaSample**, void*, void*, DWORD flags) {
        assert(flags == AM_GBF_NOWAIT);
        std::lock_guard<std::mutex> lock(mutex);
        if (!committed) return VFW_E_NOT_COMMITTED;
        if (free) { free = false; return S_OK; }
        ++m_lWaiting;
        SetEvent(registered);
        return VFW_E_TIMEOUT;
    }
    void notify() { // Caller owns the lock, as in CBaseAllocator::NotifySample.
        assert(m_lWaiting == 1);
        assert(ReleaseSemaphore(m_hSem, m_lWaiting, nullptr));
        m_lWaiting = 0;
    }
};
struct CAutoLock : std::lock_guard<std::mutex> {
    explicit CAutoLock(CD3D11SurfaceAllocator* a) : std::lock_guard<std::mutex>(a->mutex) {}
};
'''
main = r'''
int main() {
    CD3D11SurfaceAllocator allocator;
    HANDLE flush = CreateEvent(nullptr, TRUE, FALSE, nullptr);
    auto waitForSurface = [&] { return allocator.GetDecoderBuffer(nullptr, flush); };

    allocator.free = true;
    assert(waitForSurface() == S_OK);
    for (int mode = 0; mode < 4; ++mode) {
        ResetEvent(flush);
        auto pending = std::async(std::launch::async, waitForSurface);
        assert(WaitForSingleObject(allocator.registered, 2000) == WAIT_OBJECT_0);
        {
            std::lock_guard<std::mutex> lock(allocator.mutex);
            if (mode == 0 || mode == 1) SetEvent(flush);
            if (mode == 2) allocator.free = true;
            if (mode == 3) allocator.committed = false;
            if (mode != 0) allocator.notify();
        }
        assert(pending.wait_for(std::chrono::seconds(2)) == std::future_status::ready);
        HRESULT result = pending.get();
        assert(result == (mode < 2 ? VFW_E_WRONG_STATE : mode == 2 ? S_OK : VFW_E_NOT_COMMITTED));
        assert(allocator.m_lWaiting == 0);
        assert(WaitForSingleObject(allocator.m_hSem, 0) == WAIT_TIMEOUT);
    }
    CloseHandle(flush);
    CloseHandle(allocator.m_hSem);
    CloseHandle(allocator.registered);
}
'''
cpp = out / 'lav-native-flush.cpp'
exe = cpp.with_suffix('.exe')
cpp.write_text(harness + method + main)
subprocess.run(['cl', '/nologo', '/EHsc', '/std:c++17', '/Fe:' + str(exe), str(cpp)], cwd=out, check=True)
subprocess.run([str(exe)], cwd=out, check=True, timeout=12)
print('PASS: native surface availability, input flush, concurrent release and decommit')
