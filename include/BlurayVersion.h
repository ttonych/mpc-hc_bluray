// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "version.h"

// Single fork-release number. Keep upstream numeric resource versions intact.
#define MPCHC_BLURAY_RELEASE 1
#define MPCHC_BLURAY_VERSION_STR MAKE_STR(MPC_VERSION_MAJOR) _T(".") MAKE_STR(MPC_VERSION_MINOR) _T(".") MAKE_STR(MPC_VERSION_PATCH) _T("-bluray.") MAKE_STR(MPCHC_BLURAY_RELEASE)
#define MPCHC_BLURAY_NAME _T("MPC-HC Blu-ray")
