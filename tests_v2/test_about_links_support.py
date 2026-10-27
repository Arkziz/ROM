from __future__ import annotations

import unittest
from rom_v2.domain.about_links_support import (
    AboutCatalog, AboutLinksSupportService, AboutSection, LinkKind, LinksConfiguration,
)


class AboutLinksSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sections = (
            AboutSection("world", "Світ", "Canonical body one"),
            AboutSection("classes", "Класи", "Canonical body two"),
        )
        self.catalog = AboutCatalog(self.sections)

    def test_catalog_preserves_authoritative_order_and_exact_content(self) -> None:
        service = AboutLinksSupportService(self.catalog, LinksConfiguration())
        self.assertEqual(service.list_about_sections(), self.sections)
        self.assertEqual(service.get_about_section("world").body, "Canonical body one")

    def test_unknown_and_duplicate_sections_fail_closed(self) -> None:
        with self.assertRaisesRegex(KeyError, "unknown_about_section"):
            self.catalog.get("missing")
        with self.assertRaisesRegex(ValueError, "duplicate_about_section_key"):
            AboutCatalog((self.sections[0], self.sections[0]))

    def test_https_links_are_visible_in_canonical_order(self) -> None:
        config = LinksConfiguration(
            game_chat_url="https://example.test/chat",
            news_channel_url="https://example.test/news",
            support_url="https://example.test/support",
        )
        kinds = [link.kind for link in config.configured_links()]
        self.assertEqual(kinds, [LinkKind.GAME_CHAT, LinkKind.NEWS_CHANNEL, LinkKind.SUPPORT])

    def test_unconfigured_links_are_hidden(self) -> None:
        view = AboutLinksSupportService(self.catalog, LinksConfiguration()).links_view()
        self.assertTrue(view.is_empty)
        self.assertEqual(view.links, ())

    def test_non_https_malformed_and_credential_urls_are_hidden(self) -> None:
        config = LinksConfiguration(
            game_chat_url="http://example.test/chat",
            news_channel_url="not-a-url",
            support_url="https://user:secret@example.test/support",
        )
        self.assertEqual(config.configured_links(), ())

    def test_partial_configuration_shows_only_valid_entries(self) -> None:
        config = LinksConfiguration(
            game_chat_url=" https://example.test/chat ",
            news_channel_url="",
            support_url=None,
        )
        links = config.configured_links()
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].kind, LinkKind.GAME_CHAT)
        self.assertEqual(links[0].url, "https://example.test/chat")

    def test_domain_has_no_provider_or_payment_destination_policy(self) -> None:
        config = LinksConfiguration(support_url="https://example.test/support")
        link = config.configured_links()[0]
        self.assertEqual(link.kind, LinkKind.SUPPORT)
        self.assertFalse(hasattr(link, "provider"))
        self.assertFalse(hasattr(link, "account"))


if __name__ == "__main__":
    unittest.main()
