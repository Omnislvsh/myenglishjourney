from __future__ import annotations

import re
from pathlib import Path

from generate_progress import build_statistics, stat_card


ROOT = Path(__file__).resolve().parent.parent
HOME = ROOT / "docs" / "index.md"
TEXTS = ROOT / "docs" / "Переведенные и известные тексты"

START = "<!-- home:start -->"
END = "<!-- home:end -->"


def plural_texts(n: int) -> str:
    if n % 100 in range(11, 15):
        return "переведённых текстов"
    forms = {1: "переведённый текст", 2: "переведённых текста", 3: "переведённых текста", 4: "переведённых текста"}
    return forms.get(n % 10, "переведённых текстов")


def build_block() -> str:
    total = build_statistics()["vocabulary"]["Total"]
    texts = sum(1 for p in TEXTS.iterdir() if p.is_dir()) if TEXTS.exists() else 0

    cards = "".join(
        [
            stat_card(str(total), "слов в словаре"),
            stat_card(str(texts), plural_texts(texts)),
        ]
    )

    return "\n".join([START, f'<div class="stats">{cards}</div>', END])


def main() -> None:
    text = HOME.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)

    if not pattern.search(text):
        raise SystemExit(f"Markers not found in {HOME}")

    HOME.write_text(pattern.sub(lambda _: build_block(), text), encoding="utf-8")
    print(f"Generated {HOME}")


if __name__ == "__main__":
    main()
