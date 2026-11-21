"""Bundle the dashboard and public CSV/JSON data into an offline HTML file."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--data", type=Path, help="An alternative pipeline output directory")
    args = parser.parse_args()

    docs = Path(__file__).resolve().parent
    data_dir = args.data if args.data is not None else docs.parent / "data"
    data = {
        f"data/{path.name}": path.read_text(encoding="utf-8")
        for path in sorted(data_dir.iterdir())
        if path.is_file() and path.suffix in {".csv", ".json"}
    }
    if not {"data/run.json", "data/panel.csv"}.issubset(data):
        parser.error("the data directory must contain a monitoring run")

    html = (docs / "index.html").read_text(encoding="utf-8")
    css = (docs / "dashboard.css").read_text(encoding="utf-8")
    script = (docs / "dashboard.js").read_text(encoding="utf-8")
    # Escape opening tags so CSV text cannot close the HTML script element.
    payload = json.dumps(data, ensure_ascii=False).replace("<", r"\u003c")
    html = html.replace('<link rel="stylesheet" href="dashboard.css">', f"<style>\n{css}</style>")
    html = html.replace('<script src="dashboard.js" defer></script>', "")
    html = html.replace("</body>", f'<script type="application/json" id="embedded-run">{payload}</script>\n<script>\n{script}</script>\n</body>')
    args.output.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
