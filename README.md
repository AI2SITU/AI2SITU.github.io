# AI²S Lab website

Website of the Artificial Intelligence and Intelligent Systems Laboratory (AI²S), Istanbul Technical University — live at https://ai2situ.github.io

- `index.html` – the page (self-contained; embeds a fallback copy of the data)
- `videos.json` – videos shown under "Studies". New YouTube uploads are added automatically; edit `cat` (topic), `v` (venue), `y` (year) and `paper` to tidy them up.
- `metrics.json` – Google Scholar numbers in the header
- `update_data.py` + `.github/workflows/update-data.yml` – run every morning: add new YouTube uploads, try to refresh the Scholar metrics (Scholar sometimes blocks this; the last good values are kept)
