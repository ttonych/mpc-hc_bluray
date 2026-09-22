// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <afxwin.h>
#include <filesystem>
#include "BlurayAdvancedSettings.h"
#include "BlurayJava.h"

struct BluraySettings {
    bool menus = false;
    int region = 2;
    CStringW country;
    CStringW menuLanguage = L"eng", audioLanguage = L"eng", subtitleLanguage = L"eng";
    bool persistent = true;
    BlurayAdvanced::Values advanced{};
    CStringW javaHome, persistentRoot, cacheRoot;

    static bool IsCode(const CStringW& value, int length) {
        if (value.IsEmpty()) return true;
        if (value.GetLength() != length) return false;
        for (int i = 0; i < length; ++i)
            if (!((value[i] >= L'a' && value[i] <= L'z') || (value[i] >= L'A' && value[i] <= L'Z'))) return false;
        return true;
    }
    static bool IsPath(const CStringW& value) {
        if (value.IsEmpty()) return true;
        return value.Find(L'"') < 0 && value.Find(L'\n') < 0 && value.Find(L'\r') < 0
            && std::filesystem::path(value.GetString()).is_absolute();
    }
    static bool HasJavaRuntime(const CStringW& value) {
        if (value.IsEmpty() || !IsPath(value)) return false;
        return BlurayJava::Inspect(value.GetString()).status == BlurayJava::Status::Ready;
    }

    void Load() {
        auto* app = AfxGetApp();
        menus = app->GetProfileInt(L"Settings", L"BluRayMenus", menus) != 0;
        region = app->GetProfileInt(L"Settings", L"BluRayRegion", region);
        if (region != 1 && region != 2 && region != 4) region = 2;
        country = app->GetProfileString(L"Settings", L"BluRayCountry", country);
        country.Trim(); country.MakeUpper();
        if (!IsCode(country, 2)) country.Empty();
        menuLanguage = app->GetProfileString(L"Settings", L"BluRayMenuLanguage", menuLanguage);
        audioLanguage = app->GetProfileString(L"Settings", L"BluRayAudioLanguage", audioLanguage);
        subtitleLanguage = app->GetProfileString(L"Settings", L"BluRaySubtitleLanguage", subtitleLanguage);
        for (auto* language : {&menuLanguage, &audioLanguage, &subtitleLanguage}) {
            language->Trim(); language->MakeLower();
            if (!IsCode(*language, 3)) *language = L"eng";
        }
        persistent = app->GetProfileInt(L"Settings", L"BluRayPersistentStorage", persistent) != 0;
        for (size_t i = 0; i < advanced.size(); ++i) {
            const unsigned n = app->GetProfileInt(L"Settings", BlurayAdvanced::Specs[i].key, UINT_MAX);
            // Every uint32 bit pattern is a valid capability mask. Distinguish
            // an absent key from explicit UINT_MAX using a second default.
            const bool present = n != UINT_MAX
                || app->GetProfileInt(L"Settings", BlurayAdvanced::Specs[i].key, 0) == UINT_MAX;
            advanced[i].enabled = present && BlurayAdvanced::Valid(i, n);
            advanced[i].number = n;
        }
        javaHome = app->GetProfileString(L"Settings", L"BluRayJavaHome", javaHome);
        persistentRoot = app->GetProfileString(L"Settings", L"BluRayPersistentRoot", persistentRoot);
        cacheRoot = app->GetProfileString(L"Settings", L"BluRayCacheRoot", cacheRoot);
    }
    void Save() const {
        auto* app = AfxGetApp();
        app->WriteProfileInt(L"Settings", L"BluRayMenus", menus);
        app->WriteProfileInt(L"Settings", L"BluRayRegion", region);
        app->WriteProfileString(L"Settings", L"BluRayCountry", country);
        app->WriteProfileString(L"Settings", L"BluRayMenuLanguage", menuLanguage);
        app->WriteProfileString(L"Settings", L"BluRayAudioLanguage", audioLanguage);
        app->WriteProfileString(L"Settings", L"BluRaySubtitleLanguage", subtitleLanguage);
        app->WriteProfileInt(L"Settings", L"BluRayPersistentStorage", persistent);
        for (size_t i = 0; i < advanced.size(); ++i) {
            if (advanced[i].enabled) app->WriteProfileInt(L"Settings", BlurayAdvanced::Specs[i].key, advanced[i].number);
            else app->WriteProfileString(L"Settings", BlurayAdvanced::Specs[i].key, nullptr);
        }
        app->WriteProfileString(L"Settings", L"BluRayJavaHome", javaHome);
        app->WriteProfileString(L"Settings", L"BluRayPersistentRoot", persistentRoot);
        app->WriteProfileString(L"Settings", L"BluRayCacheRoot", cacheRoot);
    }
};
