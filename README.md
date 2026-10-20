# My English Journey

Личный сайт для отслеживания прогресса в английском: активный словарь, переведённые тексты, статистика.
Опубликован: https://omnislvsh.github.io/myenglishjourney/

Сайт собран на [MkDocs Material](https://squidfunnel.github.io/mkdocs-material/); заметки пишутся в Obsidian (папка `docs/` — это vault).

## Структура

- `docs/` — Markdown-заметки (словарь, тексты, `assets/`)
- `overrides/` — переопределения шаблонов темы
- `scripts/generate_progress.py` — генерирует страницу `docs/Progress.md` по истории git
- `.github/workflows/deploy.yml` — сборка и публикация на GitHub Pages

## Локальный запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_progress.py   # необязательно: обновить Progress.md
mkdocs serve                          # http://127.0.0.1:8000
```

## Публикация

Push в `main` запускает workflow: генерация прогресса → `mkdocs build --strict` → деплой на GitHub Pages.
В настройках репозитория (Settings → Pages) источник должен быть «GitHub Actions».

## Добавление слова

Создайте файл `docs/Active Vocabulary/<Verbs|Nouns|Adjectives>/<слово>.md` с front matter
(`type`, `level`, `status`, `tags`), переводом, конструкциями и примером, затем добавьте ссылку `[[слово]]` в `index.md` раздела.
