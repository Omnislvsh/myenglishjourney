from __future__ import annotations

import subprocess
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PROGRESS_FILE = DOCS / "Progress.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def count_md(directory: Path) -> int:
    """Count markdown files recursively, excluding index.md files."""
    if not directory.exists():
        return 0

    return sum(
        1
        for path in directory.rglob("*.md")
        if path.is_file()
        and path.name.lower() != "index.md"
    )
    
def git_added_files() -> list[tuple[date, str]]:
    """
    Return all markdown files that were added to the repository,
    grouped by the date of the commit that added them.
    """

    result = subprocess.run(
        [
            "git",
            "log",
            "--diff-filter=A",
            "--format=%ad",
            "--date=short",
            "--name-only",
            "--",
            "docs",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    lines = [line.strip() for line in result.stdout.splitlines()]

    current_date: date | None = None
    additions: list[tuple[date, str]] = []

    for line in lines:
        if not line:
            continue

        try:
            current_date = datetime.strptime(
                line,
                "%Y-%m-%d",
            ).date()
            continue
        except ValueError:
            pass
        if (
            current_date
            and line.endswith(".md")
            and not line.endswith("/index.md")
            and line != "docs/Progress.md"
        ):
            additions.append((current_date, line))
    return additions
def calculate_streak(active_days: set[date]) -> int:
    """Calculate the current consecutive-day streak."""

    if not active_days:
        return 0

    today = date.today()

    # If there was no activity today, continue from yesterday.
    if today not in active_days:
        today -= timedelta(days=1)

    streak = 0
    current = today

    while current in active_days:
        streak += 1
        current -= timedelta(days=1)

    return streak


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

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

    today = date.today()

    daily_activity = []

    for days_ago in range(29, -1, -1):
        current = today - timedelta(days=days_ago)

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


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def generate_progress(stats: dict) -> str:
    vocabulary = stats["vocabulary"]
    activity = stats["activity"]

    lines = [
        "# Progress",
        "",
        "## Vocabulary",
        "",
        "| Category | Words |",
        "| --- | ---: |",
        f"| Verbs | {vocabulary['Verbs']} |",
        f"| Nouns | {vocabulary['Nouns']} |",
        f"| Adjectives | {vocabulary['Adjectives']} |",
        f"| **Total** | **{vocabulary['Total']}** |",
        "",
        "## Activity",
        "",
        "New Markdown files added per day during the last 30 days.",
        "",
        "```text",
    ]

    max_count = max(
        (item["count"] for item in activity),
        default=0,
    )

    if max_count == 0:
        lines.append("No activity yet.")
    else:
        for item in activity:
            bar_length = round(
                item["count"] / max_count * 20
            )

            bar = "█" * bar_length

            lines.append(
                f"{item['date'].strftime('%d %b')} "
                f"{bar:<20} "
                f"{item['count']}"
            )

    lines.extend(
        [
            "```",
            "",
            "## Streak",
            "",
            f"Current streak: **{stats['streak']} days**",
            "",
            "## Overall",
            "",
            f"Markdown files added: **{stats['total_added']}**",
            "",
        ]
    )

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
