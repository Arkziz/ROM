"""Pure API-ready About/links/support evaluation without Telegram wiring."""
from __future__ import annotations

from dataclasses import dataclass
from .models import AboutCatalog, AboutSection, ExternalLink, LinksConfiguration


@dataclass(frozen=True, slots=True)
class LinksView:
    links: tuple[ExternalLink, ...]
    is_empty: bool


class AboutLinksSupportService:
    """Expose canonical content supplied by an authoritative adapter and safe links."""

    def __init__(self, catalog: AboutCatalog, configuration: LinksConfiguration) -> None:
        self._catalog = catalog
        self._configuration = configuration

    def list_about_sections(self) -> tuple[AboutSection, ...]:
        return self._catalog.sections

    def get_about_section(self, section_key: str) -> AboutSection:
        return self._catalog.get(section_key)

    def links_view(self) -> LinksView:
        links = self._configuration.configured_links()
        return LinksView(links=links, is_empty=not links)
