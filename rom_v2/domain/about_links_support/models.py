"""Immutable models for About content and configured external links."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlsplit


class LinkKind(str, Enum):
    GAME_CHAT = "game_chat"
    NEWS_CHANNEL = "news_channel"
    SUPPORT = "support"


def validate_https_url(value: str | None) -> str | None:
    """Return a canonical configured HTTPS URL or hide invalid/unconfigured input."""
    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    parsed = urlsplit(candidate)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    return candidate


@dataclass(frozen=True, slots=True)
class AboutSection:
    section_key: str
    title: str
    body: str

    def __post_init__(self) -> None:
        if not self.section_key.strip() or not self.title.strip() or not self.body.strip():
            raise ValueError("about_section_key_title_and_body_required")


@dataclass(frozen=True, slots=True)
class AboutCatalog:
    sections: tuple[AboutSection, ...]

    def __post_init__(self) -> None:
        keys = [section.section_key for section in self.sections]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate_about_section_key")

    def get(self, section_key: str) -> AboutSection:
        for section in self.sections:
            if section.section_key == section_key:
                return section
        raise KeyError(f"unknown_about_section::{section_key}")


@dataclass(frozen=True, slots=True)
class ExternalLink:
    kind: LinkKind
    url: str


@dataclass(frozen=True, slots=True)
class LinksConfiguration:
    game_chat_url: str | None = None
    news_channel_url: str | None = None
    support_url: str | None = None

    def configured_links(self) -> tuple[ExternalLink, ...]:
        """Hide unconfigured or invalid values and preserve canonical display order."""
        pairs = (
            (LinkKind.GAME_CHAT, self.game_chat_url),
            (LinkKind.NEWS_CHANNEL, self.news_channel_url),
            (LinkKind.SUPPORT, self.support_url),
        )
        links = []
        for kind, raw in pairs:
            valid = validate_https_url(raw)
            if valid is not None:
                links.append(ExternalLink(kind, valid))
        return tuple(links)
