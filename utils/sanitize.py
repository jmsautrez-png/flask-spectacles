"""HTML sanitization for rich-text fields (TinyMCE descriptions)."""
import re
import html as html_module
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


# --- Comptage / troncature de mots pour la description (TinyMCE) ---------

# Balises "bloc" traitées comme un séparateur de phrase lors de la conversion
# HTML -> texte brut (aligné sur la logique JS de show_form_edit.html).
_BLOCK_END_RE = re.compile(r"</\s*(p|div|li|h[1-6]|blockquote)\s*>", re.IGNORECASE)
_BR_RE = re.compile(r"<\s*br\s*/?\s*>", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[\u00A0\u2000-\u200B\t\r\n]+")


def html_to_plain(html: str) -> str:
    """Convert sanitized HTML (TinyMCE) to plain text for word counting."""
    if not html:
        return ""
    s = _BR_RE.sub(". ", html)
    s = _BLOCK_END_RE.sub(". ", s)
    s = _TAG_RE.sub(" ", s)
    s = html_module.unescape(s)
    s = _WS_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def count_words_html(html: str) -> int:
    """Return the number of words in a sanitized HTML fragment."""
    plain = html_to_plain(html)
    if not plain:
        return 0
    # Un "mot" doit contenir au moins un caractère alphanumérique.
    return sum(1 for w in plain.split(" ") if w and re.search(r"[^\W_]", w, re.UNICODE))


def enforce_word_limit(html: str, max_words: int) -> tuple[str, int, int]:
    """Truncate HTML so that the visible text has at most ``max_words`` words.

    Returns a tuple ``(new_html, original_count, final_count)``.
    If the input is already within the limit, ``new_html`` is unchanged.
    The truncation preserves HTML tags: it walks the HTML linearly, counts
    words inside text nodes, closes any still-open tags at the cut point,
    and appends an ellipsis.
    """
    original = count_words_html(html)
    if original <= max_words or not html:
        return html, original, original

    out_parts: list[str] = []
    open_tags: list[str] = []
    words_left = max_words
    i = 0
    n = len(html)
    void_tags = {"br", "hr", "img", "input", "meta", "link"}

    while i < n and words_left > 0:
        if html[i] == "<":
            end = html.find(">", i)
            if end == -1:
                break
            tag_full = html[i:end + 1]
            m = re.match(r"<\s*(/?)\s*([a-zA-Z0-9]+)([^>]*)>", tag_full)
            if m:
                closing = m.group(1) == "/"
                name = m.group(2).lower()
                self_closing = tag_full.rstrip().endswith("/>") or name in void_tags
                out_parts.append(tag_full)
                if not closing and not self_closing:
                    open_tags.append(name)
                elif closing and open_tags and open_tags[-1] == name:
                    open_tags.pop()
            else:
                out_parts.append(tag_full)
            i = end + 1
            continue

        next_tag = html.find("<", i)
        chunk = html[i:] if next_tag == -1 else html[i:next_tag]
        decoded = html_module.unescape(chunk)
        # Comptage identique à html_to_plain : NBSP/tab/nl -> espace
        normalized = _WS_RE.sub(" ", decoded)
        tokens = [w for w in re.split(r"\s+", normalized) if w]
        # Un token compte comme "mot" seulement s'il contient un alphanumérique.
        real_words = [w for w in tokens if re.search(r"[^\W_]", w, re.UNICODE)]
        if len(real_words) <= words_left:
            out_parts.append(chunk)
            words_left -= len(real_words)
            i = next_tag if next_tag != -1 else n
            continue

        # On coupe au milieu de ce chunk texte
        kept: list[str] = []
        used = 0
        for tok in tokens:
            if used >= words_left:
                break
            kept.append(tok)
            if re.search(r"[^\W_]", tok, re.UNICODE):
                used += 1
        out_parts.append(" ".join(kept))
        words_left = 0
        break

    out_parts.append("…")
    for tag in reversed(open_tags):
        out_parts.append(f"</{tag}>")
    new_html = "".join(out_parts).strip()
    return new_html, original, count_words_html(new_html)

