from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent.parent
VOCABULARY = ROOT / "docs" / "Active Vocabulary"
TARGET = ROOT / "docs" / "Мини-диктант.md"
CATEGORIES = ("Verbs", "Nouns", "Adjectives")

EXAMPLE = re.compile(
    r'!!! example vocab "Пример"\n {4}(.*?)\n {4}\{ \.sentence \}\n\n {4}(.*?)\n {4}\{ \.translation \}',
    re.S,
)


def clean_definition(text: str) -> str:
    text = re.sub(r"\*[^*]*\*", "", text)
    text = re.sub(r"\(\s*[,;:—-]+\s*", "(", text)
    text = re.sub(r"\s*[,;:—-]+\s*\)", ")", text)
    text = re.sub(r"\(\s*\)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def parse(path: Path, category: str) -> dict | None:
    text = path.read_text(encoding="utf-8")
    example = EXAMPLE.search(text)
    definitions = [
        clean_definition(d) for d in re.findall(r"^ {4}\d\. (.+)$", text, re.M)
    ]

    if not example or not definitions:
        return None

    return {
        "word": path.stem,
        "definitions": definitions,
        "sentence": example.group(1).strip(),
        "translation": example.group(2).strip(),
        "url": f"Active%20Vocabulary/{category}/{quote(path.stem)}/",
    }


def collect() -> list[dict]:
    words = []
    for category in CATEGORIES:
        for path in sorted((VOCABULARY / category).glob("*.md"), key=lambda p: p.stem.lower()):
            if path.name == "index.md":
                continue
            word = parse(path, category)
            if word:
                words.append(word)
    return words


def build_page(words: list[dict]) -> str:
    payload = json.dumps(words, ensure_ascii=False).replace("<", "\\u003c")

    return (
        "# Мини-диктант\n\n"
        "Дан перевод — введите слово по-английски. Принимается запись с «to» и без. "
        "В раунде по одному вопросу на каждое слово словаря, порядок случайный.\n\n"
        "**Клавиши:** Enter — проверить ответ, Пробел или → — следующий вопрос.\n\n"
        '<div class="quiz" data-quiz></div>\n\n'
        f'<script type="application/json" id="quiz-data">{payload}</script>\n'
    )


def main() -> None:
    words = collect()
    TARGET.write_text(build_page(words), encoding="utf-8")
    print(f"Generated {TARGET} ({len(words)} words)")


if __name__ == "__main__":
    main()
