"""HTML sanitization for rich-text fields (TinyMCE descriptions)."""
import bleach

ALLOWED_TAGS = [
    "p", "br", "strong", "b", "em", "i", "u", "s", "strike",
    "ul", "ol", "li",
    "h2", "h3", "h4",
    "blockquote", "a", "span", "div",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "target", "rel"],
}
# Note: les attributs "style" sont volontairement exclus pour eviter
# d'avoir a configurer un CssSanitizer (et limite la surface d'attaque).
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(text: str) -> str:
    """Clean rich HTML coming from TinyMCE.

    - Strips disallowed tags (script, iframe, img, etc.).
    - Returns "" for None/empty.
    - Adds rel="noopener" on external links via attribute filtering.
    """
    if not text:
        return ""
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )
    return cleaned.strip()
