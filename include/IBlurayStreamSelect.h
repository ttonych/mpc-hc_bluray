// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// Translate a disc PID into IAMStreamSelect's index and per-group ordinal.
// Kept separate from the public IMpegSplitterFilter settings interface.
interface __declspec(uuid("75951DA2-2B84-47C0-8D8D-6476E25E6706"))
IBlurayStreamSelect : public IUnknown {
    STDMETHOD(FindStream)(WORD pid, DWORD* index, DWORD* group, DWORD* ordinal) PURE;
};

// Restrict the demuxer to complete play items while the disc navigator holds
// a still. Set before IMediaSeeking::SetPositions (which flushes queued data).
interface __declspec(uuid("89E5DF56-9B39-4C91-8847-6ACB52DEBD75"))
IBlurayPlaybackControl : public IUnknown {
    STDMETHOD(SetPlayItemStop)(UINT endExclusive) PURE;
    // PTS origin used to normalize a standalone M2TS file's media positions.
    STDMETHOD(GetPresentationStart)(REFERENCE_TIME* start) PURE;
};

// The host must stop the graph before replacing a Blu-ray playlist.
interface __declspec(uuid("9064A8E2-3786-4098-B72B-A3D5C0686CC8"))
IBlurayPlaylistSwitch : public IUnknown {
    STDMETHOD(SwitchPlaylist)(LPCWSTR playlist) PURE;
};

// Confirm delivery of a fresh native sample after the old segment was flushed.
interface __declspec(uuid("41F47EBF-15EA-4520-A266-8F3AF9FB13CB"))
IBlurayNativeDelivery : public IUnknown {
    STDMETHOD(WatchNextFrame)() PURE;
    // S_FALSE until delivered, S_OK on native delivery, or a failure HRESULT.
    STDMETHOD(GetFrameResult)() PURE;
};
