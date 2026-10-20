from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent.parent
VOCABULARY = ROOT / "docs" / "Active Vocabulary"

CATEGORIES = {
    "Verbs": "Глаголов пока нет.",
    "Nouns": "Раздел пока пуст — существительные появятся здесь.",
    "Adjectives": "Раздел пока пуст — прилагательные появятся здесь.",
}


def plain(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("*", "")).strip()


def definitions(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [
        plain(m.group(1))
        for m in re.finditer(r"^ {4}\d\. (.+)$", text, re.M)
    ]


def hint(definition: str) -> str:
    return re.split(r"\s*\(", definition, maxsplit=1)[0].strip()


def card(path: Path) -> str:
    defs = definitions(path)
    title = path.stem
    search = plain(" ".join([title, *defs])).lower().replace('"', "&quot;")
    short = hint(defs[0]) if defs else ""
    return (
        f'<a class="word" href="{quote(title)}/" data-search="{search}">'
        f'<span class="word__title">{title}</span>'
        f'<span class="word__hint">{short}</span>'
        "</a>"
    )


def build_index(category: str, empty: str) -> str:
    notes = sorted(
        (p for p in (VOCABULARY / category).glob("*.md") if p.name != "index.md"),
        key=lambda p: p.stem.lower(),
    )

    if not notes:
        return f"# {category}\n\n{empty}\n"

    cards = "".join(card(p) for p in notes)

    return (
        f"# {category}\n\n"
        f'<input class="word-filter" type="search" '
        f'placeholder="Найти по слову или переводу" aria-label="Поиск по словарю">\n\n'
        f'<div class="word-grid">{cards}</div>\n'
    )


def main() -> None:
    for category, empty in CATEGORIES.items():
        target = VOCABULARY / category / "index.md"
        target.write_text(build_index(category, empty), encoding="utf-8")
        print(f"Generated {target}")


if __name__ == "__main__":
    main()
