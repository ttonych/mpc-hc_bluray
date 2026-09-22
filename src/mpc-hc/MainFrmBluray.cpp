// SPDX-License-Identifier: GPL-3.0-or-later
// MPC-HC graph adapter for the navigation engine from MPC-BE Blu-ray.
#include "stdafx.h"
#include "MainFrm.h"
#include "mplayerc.h"
#include "BlurayMenu.h"
#include "BlurayOpen.h"
#include "IBlurayStreamSelect.h"
#include "resource.h"

bool CMainFrame::OpenDiscImage(const CString& path)
{
    // Recognized ISO inputs are always consumed, including errors. Never probe
    // a complete disc image as an ordinary video file in LAV/FFmpeg.
    if (!CloseMediaBeforeOpen()) return true;
    m_discImage.reset();
    auto image = std::make_unique<CBlurayIso>();
    CWaitCursor wait;
    const DWORD result = image->Open(path);
    if (result != ERROR_SUCCESS) {
        CString message;
        message.Format(ResStr(IDS_BD_ISO_MOUNT_FAILED), result);
        AfxMessageBox(message, MB_ICONERROR);
        return true;
    }
    CString root;
    if (BlurayOpen::DiscRoot(image->Root(), root)) {
        const bool menus = AfxGetApp()->GetProfileInt(L"Settings", L"BluRayMenus", FALSE) != 0;
        if (menus ? OpenBlurayMenu(root) : OpenBD(root)) {
            m_LastOpenBDPath = image->Source();
            m_discImage = std::move(image);
        } else if (!menus) {
            AfxMessageBox(ResStr(IDS_BD_OPEN_FAILED), MB_ICONERROR);
        }
    } else if (PathFileExistsW(image->Root() + L"VIDEO_TS\\VIDEO_TS.IFO")) {
        OpenDVDOrBD(image->Root());
        m_LastOpenBDPath = image->Source();
        m_discImage = std::move(image);
    } else {
        AfxMessageBox(ResStr(IDS_BD_ISO_NOT_VIDEO), MB_ICONERROR);
    }
    return true;
}

bool CMainFrame::OpenBlurayMenu(const CString& path)
{
    if (!IsStateClosedOrLoaded()) return false;
    CString root;
    if (!BlurayOpen::DiscRoot(path, root)) {
        AfxMessageBox(ResStr(IDS_BD_NOT_A_DISC), MB_ICONERROR);
        return false;
    }
    if (AfxGetAppSettings().iDSVideoRendererType != VIDRNDT_DS_MADVR) {
        AfxMessageBox(ResStr(IDS_BD_RENDERER_UNSUPPORTED), MB_ICONERROR);
        return false;
    }
    auto retainedImage = m_discImage && m_discImage->Contains(root) ? std::move(m_discImage) : nullptr;
    if (!CloseMediaBeforeOpen()) {
        if (retainedImage) m_discImage = std::move(retainedImage);
        return false;
    }
    if (retainedImage) m_discImage = std::move(retainedImage);
    m_wndPlaylistBar.Empty();
    m_blurayMenu = std::make_unique<CBlurayMenu>();
    m_bluraySubtitleEnabled = AfxGetAppSettings().fEnableSubtitles;
    CString error;
    if (!m_blurayMenu->Start(root, error)) {
        m_blurayMenu.reset();
        m_discImage.reset();
        AfxMessageBox(error.IsEmpty() ? ResStr(IDS_BD_OPEN_FAILED) : error, MB_ICONERROR);
        return false;
    }
    m_LastOpenBDPath = root;
    UpdateBlurayTitle(root);
    OpenSetupWindowTitle();
    SetTimer(TIMER_BLURAY_MENU, 20, nullptr);
    TickBlurayMenu();
    return true;
}

void CMainFrame::UpdateBlurayTitle(const CString& root)
{
    // Resolve again for every disc open, even when the drive/path is unchanged.
    m_blurayTitle = m_blurayMenu->DiscName();
    m_blurayTitle.Trim();
    if (m_blurayTitle.IsEmpty()) {
        CString folder(root);
        folder.Replace(L'/', L'\\');
        folder.TrimRight(L"\\");
        if (folder.GetLength() == 2 && folder[1] == L':') {
            m_blurayTitle = GetDriveLabel(folder[0]);
        } else {
            m_blurayTitle = folder.Mid(folder.ReverseFind(L'\\') + 1);
        }
        m_blurayTitle.Trim();
    }
    if (m_blurayTitle.IsEmpty()) {
        m_blurayTitle = L"Blu-ray";
    }
}

void CMainFrame::StopBlurayMenu()
{
    KillTimer(TIMER_BLURAY_MENU);
    if (m_blurayMenu) {
        m_blurayMenu->DetachRenderer();
        m_blurayMenu.reset();
        AfxGetAppSettings().fEnableSubtitles = m_bluraySubtitleEnabled;
    }
    m_blurayMouseDown = false;
    m_blurayChaptersHidden = false;
    m_blurayTitle.Empty();
}

HRESULT CMainFrame::SetBlurayPlaybackPosition(REFERENCE_TIME position)
{
    REFERENCE_TIME stop = 0;
    UINT endPlayItem = 0;
    if (!m_pMS || !m_blurayMenu) {
        return E_UNEXPECTED;
    }
    // The initial BD-J graphics canvas has no authored playlist yet.
    if (!m_blurayMenu->PlaybackRange(position, stop, endPlayItem)) {
        return S_FALSE;
    }
    CComQIPtr<IBlurayPlaybackControl> control = m_pSplitterSS;
    HRESULT hr = control ? control->SetPlayItemStop(endPlayItem) : E_NOINTERFACE;
    if (SUCCEEDED(hr)) {
        hr = m_pMS->SetPositions(&position, AM_SEEKING_AbsolutePositioning,
                                &stop, AM_SEEKING_AbsolutePositioning);
    }
    if (FAILED(hr)) {
        m_blurayMenu->PlaybackFailed(hr);
    }
    return hr;
}

bool CMainFrame::BlurayMouse(HWND window, CPoint point, UINT message)
{
    if (message == WM_LBUTTONUP && m_blurayMouseDown) {
        m_blurayMouseDown = false;
        return true;
    }
    if (!m_blurayMenu || !m_blurayMenu->MenuActive() || !m_pVideoWnd
            || GetLoadState() != MLS::LOADED || m_blurayMenu->RendererBusy()) {
        return false;
    }
    ::MapWindowPoints(window, m_pVideoWnd->m_hWnd, &point, 1);
    CRect rendererRect;
    if (HasDedicatedFSVideoWindow()) {
        m_pVideoWnd->GetClientRect(&rendererRect);
    } else {
        rendererRect = m_wndView.GetVideoRect();
    }
    const bool handled = m_blurayMenu->Mouse(point, rendererRect, message == WM_LBUTTONDOWN);
    if (handled && message == WM_LBUTTONDOWN) {
        ::SetFocus(window);
        m_blurayMouseDown = true;
    }
    return handled;
}

void CMainFrame::TickBlurayMenu()
{
    if (!m_blurayMenu || m_bluraySwitching || m_blurayTicking || m_blurayMenu->RendererBusy()
            || !IsStateClosedOrLoaded() || m_bSettingUpMenus) {
        return;
    }
    m_blurayTicking = true;
    struct ResetFlag { bool& flag; ~ResetFlag() { flag = false; } } reset{m_blurayTicking};
    REFERENCE_TIME position = 0;
    if (m_pMS) {
        m_pMS->GetCurrentPosition(&position);
    }
    position = m_blurayMenu->Tick(position, m_blurayMenu->PlaybackState(GetMediaState()) == State_Running,
                                 m_dSpeedRate, m_wndToolBar.Volume);
    CString error = m_blurayMenu->DiscLossNotice();
    if (error.IsEmpty()) {
        error = m_blurayMenu->Error();
    }
    if (!error.IsEmpty()) {
        CloseMedia();
        AfxMessageBox(error, MB_ICONERROR);
        return;
    }
    UpdateSeekbarChapterBag(false);
    if (m_blurayMenu->NeedsPlaybackPause(position) && m_pMC) {
        m_pMC->Pause();
        m_CachedFilterState = State_Paused;
        m_blurayMenu->Complete();
    }
    CString path;
    if (m_blurayMenu->TakePlaylist(path)) {
        REFERENCE_TIME start = 0;
        m_blurayMenu->TakeSeek(start);
        CComHeapPtr<OLECHAR> current;
        if (m_pFSF && m_pMS && m_pMC && GetLoadState() == MLS::LOADED
                && SUCCEEDED(m_pFSF->GetCurFile(&current, nullptr)) && current
                && !path.CompareNoCase(current)) {
            if (SUCCEEDED(SetBlurayPlaybackPosition(start))) {
                m_fEndOfStream = false;
                m_blurayMenu->AttachRenderer(m_pCAP);
                m_blurayMenu->SeekApplied(start);
                m_blurayMenu->PlaylistReused();
                MediaControlRun();
                return;
            }
        }
        CAutoPtr<OpenFileData> data(DEBUG_NEW OpenFileData());
        data->fns.AddTail(path);
        data->rtStart = start;
        data->bAddToRecent = false;
        m_bluraySwitching = true;
        OpenMedia(data);
        m_bluraySwitching = false;
        return;
    }
    REFERENCE_TIME seek = 0;
    if (m_pMS && m_blurayMenu->TakeSeek(seek)) {
        if (SUCCEEDED(SetBlurayPlaybackPosition(seek))) {
            m_blurayMenu->SeekApplied(seek);
            m_fEndOfStream = false;
            MediaControlRun();
        }
    }
    bool paused;
    if (m_pMC && m_blurayMenu->TakePlaybackRequest(paused)) {
        if (paused) MediaControlPause(); else MediaControlRun();
    }
    int audioPid, subtitlePid;
    if (GetLoadState() == MLS::LOADED && m_blurayMenu->TakeStreams(audioPid, subtitlePid)) {
        CComQIPtr<IBlurayStreamSelect> mapping = m_pSplitterSS;
        auto select = [&](int pid, bool audio) {
            if (pid == -2) return;
            HRESULT hr = E_NOINTERFACE;
            if (!audio && pid == -1) {
                SetSubtitleTrackIdx(-1);
                hr = S_OK;
            } else if (mapping && m_pSplitterSS) {
                DWORD index = 0, group = 0, ordinal = 0, flags = 0;
                hr = mapping->FindStream(WORD(pid), &index, &group, &ordinal);
                if (hr == S_OK && group != (audio ? 1 : 2)) hr = E_UNEXPECTED;
                if (hr == S_OK) {
                    if (audio) hr = m_pSplitterSS->Enable(index, AMSTREAMSELECTENABLE_ENABLE);
                    else SetSubtitleTrackIdx(ordinal);
                    if (hr == S_OK) {
                        hr = m_pSplitterSS->Info(index, nullptr, &flags, nullptr, nullptr, nullptr, nullptr, nullptr);
                        if (hr == S_OK && !(flags & AMSTREAMSELECTINFO_ENABLED)) hr = E_FAIL;
                    }
                }
            }
            m_blurayMenu->StreamResult(audio, pid, hr);
        };
        select(audioPid, true);
        select(subtitlePid, false);
    }
    const CString notice = m_blurayMenu->TakeNotice();
    if (!notice.IsEmpty()) {
        m_OSD.DisplayMessage(OSD_TOPLEFT, notice, 4000);
    }
}
