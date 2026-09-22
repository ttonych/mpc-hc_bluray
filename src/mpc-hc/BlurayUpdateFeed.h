// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

#include "BlurayReleaseVersion.h"
#include "../thirdparty/rapidjson/include/rapidjson/document.h"
#include <string>

namespace BlurayRelease {

struct Release {
    Version version{};
    std::string url;
};

// Adapted from the pinned MPC-BE release selection. A valid empty list is not
// a connection error. Prereleases participate; drafts and foreign URLs do not.
inline bool ReadFeed(std::string_view text, Release& latest)
{
    if (text.size() > 4 * 1024 * 1024 || text.find('\0') != text.npos) {
        return false;
    }
    rapidjson::Document document;
    if (document.Parse<rapidjson::kParseValidateEncodingFlag>(text.data(), text.size()).HasParseError()
            || !document.IsArray()) {
        return false;
    }
    Release selected;
    for (const auto& item : document.GetArray()) {
        if (!item.IsObject()) {
            continue;
        }
        const auto draft = item.FindMember("draft");
        const auto tag = item.FindMember("tag_name");
        const auto url = item.FindMember("html_url");
        if (draft == item.MemberEnd() || !draft->value.IsBool() || draft->value.GetBool()
                || tag == item.MemberEnd() || !tag->value.IsString()
                || url == item.MemberEnd() || !url->value.IsString()) {
            continue;
        }
        const std::string tagText(tag->value.GetString(), tag->value.GetStringLength());
        const std::wstring wideTag(tagText.begin(), tagText.end());
        Version version;
        const std::string urlText(url->value.GetString(), url->value.GetStringLength());
        if (Parse(wideTag, version) && version > selected.version
                && urlText == "https://github.com/ttonych/mpc-hc_bluray/releases/tag/" + tagText) {
            selected = { version, urlText };
        }
    }
    latest = selected;
    return true;
}

} // namespace BlurayRelease
