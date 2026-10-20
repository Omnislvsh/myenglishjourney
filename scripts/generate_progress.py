from __future__ import annotations

import subprocess
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PROGRESS_FILE = DOCS / "Progress.md"

TIMEZONE = ZoneInfo("Europe/Moscow")
COMMIT_MARKER = "@@COMMIT@@"
VOCABULARY_PREFIX = "docs/Active Vocabulary/"


def today() -> date:
    return datetime.now(TIMEZONE).date()


def count_md(directory: Path) -> int:
    if not directory.exists():
        return 0

    return sum(
        1
        for path in directory.rglob("*.md")
        if path.is_file()
        and path.name.lower() != "index.md"
    )


def git_added_files() -> list[tuple[date, str]]:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotepath=false",
            "log",
            "--diff-filter=A",
            f"--format={COMMIT_MARKER}%ad",
            "--date=short",
            "--name-only",
            "--",
            "docs",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )

    current_date: date | None = None
    first_added: dict[str, date] = {}

    for raw in result.stdout.splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith(COMMIT_MARKER):
            current_date = datetime.strptime(
                line[len(COMMIT_MARKER):],
                "%Y-%m-%d",
            ).date()
            continue

        if (
            current_date
            and line.startswith(VOCABULARY_PREFIX)
            and line.endswith(".md")
            and not line.endswith("/index.md")
        ):
            first_added[line] = current_date

    return [(added, path) for path, added in first_added.items()]


def calculate_streak(active_days: set[date]) -> int:
    if not active_days:
        return 0

    current = today()

    if current not in active_days:
        current -= timedelta(days=1)

    streak = 0

    while current in active_days:
        streak += 1
        current -= timedelta(days=1)

    return streak


def build_statistics() -> dict:
    vocabulary = {
        "Verbs": count_md(DOCS / "Active Vocabulary" / "Verbs"),
        "Nouns": count_md(DOCS / "Active Vocabulary" / "Nouns"),
        "Adjectives": count_md(DOCS / "Active Vocabulary" / "Adjectives"),
    }

    vocabulary["Total"] = sum(vocabulary.values())

    additions = git_added_files()

    activity = Counter(
        added_date
        for added_date, _ in additions
    )

    active_days = set(activity.keys())

    streak = calculate_streak(active_days)

    now = today()

    daily_activity = []

    for days_ago in range(29, -1, -1):
        current = now - timedelta(days=days_ago)

        daily_activity.append(
            {
                "date": current,
                "count": activity.get(current, 0),
            }
        )

    return {
        "vocabulary": vocabulary,
        "activity": daily_activity,
        "streak": streak,
        "total_added": len(additions),
    }


def plural_days(n: int) -> str:
    if n % 100 in range(11, 15):
        return f"{n} дней"
    return f"{n} " + {1: "день", 2: "дня", 3: "дня", 4: "дня"}.get(n % 10, "дней")


def stat_card(value: str, label: str) -> str:
    return (
        '<div class="stat">'
        f'<span class="stat__value">{value}</span>'
        f'<span class="stat__label">{label}</span>'
        "</div>"
    )


def vocabulary_bar(name: str, count: int, total: int) -> str:
    width = round(count / total * 100) if total else 0
    return (
        '<div class="bar">'
        f'<div class="bar__head"><span>{name}</span><span>{count}</span></div>'
        '<div class="bar__track">'
        f'<div class="bar__fill" style="width:{width}%"></div>'
        "</div></div>"
    )


def activity_level(count: int, max_count: int) -> int:
    if count == 0 or max_count == 0:
        return 0
    return max(1, min(4, -(-count * 4 // max_count)))


def heatmap(activity: list[dict]) -> str:
    max_count = max((item["count"] for item in activity), default=0)
    lead = activity[0]["date"].weekday()

    cells = ['<i class="cell cell--empty"></i>'] * lead
    for item in activity:
        count = item["count"]
        level = activity_level(count, max_count)
        label = f"{item['date'].strftime('%d.%m.%Y')}: {count}"
        cells.append(f'<i class="cell cell--l{level}" title="{label}"></i>')

    weekdays = ["Пн", "", "Ср", "", "Пт", "", ""]
    day_labels = "".join(f"<span>{d}</span>" for d in weekdays)
    legend = "".join(f'<i class="cell cell--l{level}"></i>' for level in range(5))

    return (
        '<div class="heatmap-wrap">'
        f'<div class="heatmap-days">{day_labels}</div>'
        f'<div class="heatmap">{"".join(cells)}</div>'
        "</div>"
        f'<div class="heatmap-legend"><span>меньше</span>{legend}<span>больше</span></div>'
    )


def generate_progress(stats: dict) -> str:
    vocabulary = stats["vocabulary"]
    activity = stats["activity"]
    total = vocabulary["Total"]

    month_total = sum(item["count"] for item in activity)
    active_days = sum(1 for item in activity if item["count"])

    cards = "".join(
        [
            stat_card(str(total), "слов в словаре"),
            stat_card(plural_days(stats["streak"]), "подряд"),
            stat_card(str(month_total), "новых слов за 30 дней"),
            stat_card(str(active_days), "активных дней из 30"),
        ]
    )

    bars = "".join(
        vocabulary_bar(name, vocabulary[name], total)
        for name in ("Verbs", "Nouns", "Adjectives")
    )

    lines = [
        "# Progress",
        "",
        f'<div class="stats">{cards}</div>',
        "",
        "## Словарь",
        "",
        f'<div class="bars">{bars}</div>',
        "",
        "## Активность",
        "",
        "Новые заметки словаря по дням за последние 30 дней.",
        "",
        heatmap(activity),
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    stats = build_statistics()

    PROGRESS_FILE.write_text(
        generate_progress(stats),
        encoding="utf-8",
    )

    print(f"Generated {PROGRESS_FILE}")


if __name__ == "__main__":
    main()
