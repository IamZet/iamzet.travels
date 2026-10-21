# iamzet.travels

Путевой журнал Александра Захарова — https://iamzet.ru

Статический сайт на GitHub Pages. Страницы (`index.html`, `archive.html`, `trips/*.html`, `assets/*`)
**генерируются** из папки `src/` — руками их править не нужно, изменения перезапишутся.

## Как устроено

| Где | Что |
|---|---|
| `src/build.py` | генератор сайта |
| `src/style.css`, `src/site.js` | стили и скрипты (копируются в `assets/`) |
| `src/trips.json` | список поездок (из Google Doc «Все путешествия») |
| `src/notes.json` | тексты путевых заметок |
| `src/videos.json`, `dzen*.json`, `localvideos.json`, `cloudvideos.json` | видео: YouTube, Дзен, Yandex Object Storage |
| `src/dates.json`, `countries.json`, `merges.json`, `excludes.json` | даты, флаги стран, объединения и скрытые поездки |
| `src/covers_list.json` | размеры обложек; сами обложки лежат в `covers/` |
| `src/photo_index/*.json` | описания фотоальбомов; сами фото лежат в `photos/` |
| `src/countries.geojson`, `src/world.json` | контуры стран и суши для карты на главной |
| `maps/cities.kml` | города на карте: название, `Last visit`, `Trip link` |
| `src/flags/`, `src/me.webp` | флаги и аватар |

## Как обновить сайт

**Вариант 1 — через GitHub (ничего ставить не нужно).** Отредактируйте файл в `src/` или `maps/`
прямо на github.com и сохраните. Action «Build site» сам пересоберёт страницы и закоммитит их,
через 1–2 минуты сайт обновится.

**Вариант 2 — локально.**

```sh
pip3 install shapely
python3 src/build.py      # пересобирает страницы прямо в корне репозитория
open index.html           # посмотреть
git add -A && git commit -m "..." && git push
```

Новая обложка: положите `<slug>.webp` в `src/covers_new/` (скопируется в `covers/`) и добавьте её
размеры в `src/covers_list.json`. Новый фотоальбом: фото в `photos/<ключ>/`, описание в
`src/photo_index/<ключ>.json`.
