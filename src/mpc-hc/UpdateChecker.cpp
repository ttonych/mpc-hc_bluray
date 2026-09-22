/*
 * (C) 2012-2014, 2017 see Authors.txt
 *
 * This file is part of MPC-HC.
 *
 * MPC-HC is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * MPC-HC is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */


#include "stdafx.h"
#include "mpc-hc_config.h"
#include "VersionInfo.h"
#include "UpdateChecker.h"
#include "UpdateCheckerDlg.h"
#include "SettingsDefines.h"
#include "mplayerc.h"
#include "AppSettings.h"

#include <afxinet.h>
#include "BlurayVersion.h"
#include "BlurayUpdateFeed.h"
#include <memory>

const Version UpdateChecker::MPC_HC_VERSION = {
    VersionInfo::GetMajorNumber(),
    VersionInfo::GetMinorNumber(),
    VersionInfo::GetPatchNumber(),
    MPCHC_BLURAY_RELEASE
};
const LPCTSTR UpdateChecker::MPC_HC_UPDATE_URL = UPDATE_URL;

bool UpdateChecker::bIsCheckingForUpdate = false;
CCritSec UpdateChecker::csIsCheckingForUpdate;

UpdateChecker::UpdateChecker(CString versionFileURL)
    : versionFileURL(versionFileURL)
    , latestVersion()
{
}

UpdateChecker::~UpdateChecker()
{
}

Update_Status UpdateChecker::IsUpdateAvailable(const Version& currentVersion)
{
    latestVersion = {};
    latestURL.Empty();
    try {
        CInternetSession internet(MPCHC_BLURAY_NAME);
        internet.SetOption(INTERNET_OPTION_CONNECT_TIMEOUT, 5000);
        internet.SetOption(INTERNET_OPTION_RECEIVE_TIMEOUT, 5000);
        internet.SetOption(INTERNET_OPTION_SEND_TIMEOUT, 5000);
        const CString headers = _T("Accept: application/vnd.github+json\r\nX-GitHub-Api-Version: 2026-03-10\r\n");
        const auto close = [](CStdioFile* file) {
            if (file) {
                try { file->Close(); } catch (CException* error) { error->Delete(); }
                delete file;
            }
        };
        const ULONGLONG started = GetTickCount64();
        std::unique_ptr<CStdioFile, decltype(close)> file(internet.OpenURL(versionFileURL, 1,
            INTERNET_FLAG_TRANSFER_BINARY | INTERNET_FLAG_DONT_CACHE | INTERNET_FLAG_RELOAD,
            headers, DWORD(-1)), close);
        if (!file || !file->IsKindOf(RUNTIME_CLASS(CHttpFile))) {
            return UPDATER_ERROR;
        }
        DWORD status = 0;
        if (!static_cast<CHttpFile*>(file.get())->QueryInfoStatusCode(status) || status != HTTP_STATUS_OK) {
            return UPDATER_ERROR;
        }
        std::string body;
        char buffer[16384];
        UINT count;
        while ((count = file->Read(buffer, sizeof(buffer))) != 0) {
            if (body.size() + count > 4 * 1024 * 1024 || GetTickCount64() - started > 15000) {
                return UPDATER_ERROR;
            }
            body.append(buffer, count);
        }
        BlurayRelease::Release latest;
        if (!BlurayRelease::ReadFeed(body, latest)) {
            return UPDATER_ERROR;
        }
        time_t lastCheck = time(nullptr);
        AfxGetApp()->WriteProfileBinary(IDS_R_SETTINGS, IDS_RS_BLURAY_UPDATER_LAST_CHECK,
                                       (LPBYTE)&lastCheck, sizeof(lastCheck));
        if (latest.url.empty()) {
            return UPDATER_NO_RELEASES;
        }
        latestVersion = { latest.version[0], latest.version[1], latest.version[2], latest.version[3] };
        latestURL = CString(latest.url.c_str()); // Validated ASCII repository/tag URL.
        const int comparison = CompareVersion(currentVersion, latestVersion);
        if (comparison < 0) {
            const CString ignoredText = AfxGetApp()->GetProfileString(IDS_R_SETTINGS, IDS_RS_BLURAY_UPDATER_IGNORE_VERSION);
            Version ignored;
            const bool ignore = ParseVersion(ignoredText, ignored) && CompareVersion(ignored, latestVersion) >= 0;
            return ignore ? UPDATER_UPDATE_AVAILABLE_IGNORED : UPDATER_UPDATE_AVAILABLE;
        }
        return comparison > 0 ? UPDATER_NEWER_VERSION : UPDATER_LATEST_STABLE;
    } catch (CInternetException* error) {
        error->Delete();
        return UPDATER_ERROR;
    }
}

Update_Status UpdateChecker::IsUpdateAvailable()
{
    return IsUpdateAvailable(MPC_HC_VERSION);
}

void UpdateChecker::IgnoreLatestVersion()
{
    if (!latestURL.IsEmpty()) {
        AfxGetApp()->WriteProfileString(IDS_R_SETTINGS, IDS_RS_BLURAY_UPDATER_IGNORE_VERSION, latestVersion.ToString());
    }
}

bool UpdateChecker::ParseVersion(const CString& text, Version& version)
{
    BlurayRelease::Version parsed;
    if (!BlurayRelease::Parse(std::wstring_view(text.GetString(), text.GetLength()), parsed)) {
        return false;
    }
    version = { parsed[0], parsed[1], parsed[2], parsed[3] };
    return true;
}

int UpdateChecker::CompareVersion(const Version& v1, const Version& v2)
{
    if (v1.major > v2.major) {
        return 1;
    } else if (v1.major < v2.major) {
        return -1;
    } else if (v1.minor > v2.minor) {
        return 1;
    } else if (v1.minor < v2.minor) {
        return -1;
    } else if (v1.patch > v2.patch) {
        return 1;
    } else if (v1.patch < v2.patch) {
        return -1;
    } else if (v1.revision > v2.revision) {
        return 1;
    } else if (v1.revision < v2.revision) {
        return -1;
    } else {
        return 0;
    }
}

bool UpdateChecker::IsAutoUpdateEnabled()
{
    int& status = AfxGetAppSettings().nUpdaterAutoCheck;

    if (status == AUTOUPDATE_UNKNOWN) { // First run
        status = (AfxMessageBox(IDS_BD_UPDATE_AUTO_CHECK, MB_ICONQUESTION | MB_YESNO, 0) == IDYES) ? AUTOUPDATE_ENABLE : AUTOUPDATE_DISABLE;
    }

    return (status == AUTOUPDATE_ENABLE);
}

bool UpdateChecker::IsTimeToAutoUpdate()
{
    time_t* lastCheck = nullptr;
    UINT nRead;

    if (!AfxGetApp()->GetProfileBinary(IDS_R_SETTINGS, IDS_RS_BLURAY_UPDATER_LAST_CHECK, (LPBYTE*)&lastCheck, &nRead) || nRead != sizeof(time_t)) {
        if (lastCheck) {
            delete [] lastCheck;
        }

        return true;
    }

    bool isTimeToAutoUpdate = (time(nullptr) >= *lastCheck + AfxGetAppSettings().nUpdaterDelay * 24 * 3600);

    delete [] lastCheck;

    return isTimeToAutoUpdate;
}

static UINT RunCheckForUpdateThread(LPVOID pParam)
{
    bool autoCheck = !!pParam;

    if (!autoCheck || UpdateChecker::IsTimeToAutoUpdate()) {
        UpdateChecker updateChecker(UpdateChecker::MPC_HC_UPDATE_URL);

        Update_Status status = updateChecker.IsUpdateAvailable();

        if (!autoCheck || status == UPDATER_UPDATE_AVAILABLE) {
            UpdateCheckerDlg dlg(status, updateChecker.GetLatestVersion(), updateChecker.GetLatestURL());

            try {
                if (dlg.DoModal() == IDC_UPDATE_IGNORE_BUTTON) {
                    updateChecker.IgnoreLatestVersion();
                }
            } catch (...) {
                AfxGetAppSettings().nUpdaterAutoCheck = AUTOUPDATE_DISABLE;
            }
        }
    }

    CAutoLock lock(&UpdateChecker::csIsCheckingForUpdate);
    UpdateChecker::bIsCheckingForUpdate = false;

    return 0;
}

void UpdateChecker::CheckForUpdate(bool autoCheck /*= false*/)
{
    CAutoLock lock(&csIsCheckingForUpdate);

    if (!bIsCheckingForUpdate) {
        bIsCheckingForUpdate = true;
        if (!AfxBeginThread(RunCheckForUpdateThread, (LPVOID)autoCheck)) {
            bIsCheckingForUpdate = false;
        }
    }
}
