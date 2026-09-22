// SPDX-License-Identifier: GPL-3.0-or-later
// Adapted from the pinned MPC-BE release-version probe; also check HC's feed.
#include "../../src/mpc-hc/BlurayUpdateFeed.h"
#include <cassert>
#include <iostream>

int main()
{
    using namespace BlurayRelease;
    Version value{};
    assert(Parse(L"2.8.2-bluray.1", value));
    assert((value == Version{2, 8, 2, 1}));
    for (auto bad : {L"2.8.2", L"2.8.2.2", L"2.8.2-bluray.0", L"v2.8.2-bluray.1",
        L"2.8.2-bluray.2-extra", L"2.8.2-bluray.-1", L"2.8.2-bluray.100000",
        L" 2.8.2-bluray.2", L"2.8.2-bluray.2 ", L"2.8.2-bluray.", L""}) {
        const auto before = value;
        assert(!Parse(bad, value));
        assert(value == before);
    }
    assert(Parse(L"2.8.2-bluray.2", value));
    assert((value > Version{2, 8, 2, 1}));
    assert((Version{2, 8, 3, 1} > value));
    assert((Version{2, 10, 0, 1} > Version{2, 9, 99, 99}));
    Release latest;
    assert(ReadFeed("[]", latest) && latest.url.empty());
    for (auto bad : {"", "<html>error</html>", "{\"message\":\"rate limit\"}", "[] trailing", "["}) {
        assert(!ReadFeed(bad, latest));
    }
    assert(!ReadFeed(std::string("[]\0ignored", 10), latest));
    assert(!ReadFeed(std::string(4 * 1024 * 1024 + 1, ' '), latest));
    assert(ReadFeed(R"([
      {"draft":false,"prerelease":true,"tag_name":"2.8.2-bluray.2","html_url":"https://github.com/ttonych/mpc-hc_bluray/releases/tag/2.8.2-bluray.2"},
      {"draft":true,"tag_name":"99.0.0-bluray.1","html_url":"https://github.com/ttonych/mpc-hc_bluray/releases/tag/99.0.0-bluray.1"},
      {"draft":false,"tag_name":"98.0.0-bluray.1","html_url":"https://github.com/clsid2/mpc-hc/releases/tag/98.0.0-bluray.1"},
      {"draft":false,"tag_name":"97.0.0","html_url":"https://github.com/ttonych/mpc-hc_bluray/releases/tag/97.0.0"},
      {"draft":false,"tag_name":"2.8.2-bluray.1","html_url":"https://github.com/ttonych/mpc-hc_bluray/releases/tag/2.8.2-bluray.1"},
      {"tag_name":"96.0.0-bluray.1"}, null, 12,
      {"draft":"false","tag_name":4,"html_url":[]},
      {"draft":false,"tag_name":"95.0.0-bluray.1\u0000","html_url":"https://github.com/ttonych/mpc-hc_bluray/releases/tag/95.0.0-bluray.1"}
    ])", latest));
    assert((latest.version == Version{2, 8, 2, 2}));
    assert(latest.url == "https://github.com/ttonych/mpc-hc_bluray/releases/tag/2.8.2-bluray.2");
    assert(ReadFeed(R"([
      {"draft":false,"tag_name":"2.8.3-bluray.1","html_url":"https://github.com/ttonych/mpc-hc_bluray/releases/tag/2.8.3-bluray.1"},
      {"draft":false,"tag_name":"2.8.2-bluray.99","html_url":"https://github.com/ttonych/mpc-hc_bluray/releases/tag/2.8.2-bluray.99"}
    ])", latest));
    assert((latest.version == Version{2, 8, 3, 1}));
    assert(ReadFeed("[]", latest) && latest.url.empty() && latest.version == Version{});
    std::cout << "Fork tag parsing, ordering, release filtering and invalid/empty feeds: passed\n";
}
