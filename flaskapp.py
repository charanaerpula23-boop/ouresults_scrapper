from flask import Flask, render_template, request, jsonify
import json
import logging
from typing import List, Dict
import urllib3

# Reuse existing scraper logic from app.py
from app import OUResultsScraper, Config
import requests

app = Flask(__name__, static_url_path='/static', static_folder='static')
logging.getLogger('werkzeug').setLevel(logging.WARNING)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Store last results in-memory for /json view
last_results: List[Dict] = []
last_summary: Dict = {}


class WebScraper(OUResultsScraper):
    """Subclass that avoids file I/O and uses thread-safe HTTP calls."""
    def load_existing_results(self):
        return []

    def save_results(self, results: List[Dict]):
        # Disable file writes in web mode
        pass

    def fetch_result(self, htno: str):
        """Override to avoid sharing a Session across threads."""
        payload = {
            "mbstatus": "SEARCH",
            "htno": htno,
            "Submit.x": "25",
            "Submit.y": "8"
        }
        for attempt in range(self.config.MAX_RETRIES):
            try:
                response = requests.post(
                    self.config.URL,
                    data=payload,
                    headers=self.config.HEADERS,
                    timeout=self.config.TIMEOUT,
                    verify=False  # keep consistent with original config
                )
                if response.status_code != 200:
                    app.logger.warning(f"{htno} - HTTP {response.status_code} (attempt {attempt + 1})")
                    continue
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                result = self.parse_result_page(soup)
                if result:
                    from dataclasses import asdict
                    return {
                        "student": asdict(result.student),
                        "subjects": [asdict(s) for s in result.subjects],
                        "final_result": result.final_result,
                        "fetch_timestamp": result.fetch_timestamp
                    }
                else:
                    return None
            except requests.exceptions.Timeout:
                app.logger.warning(f"{htno} - Timeout (attempt {attempt + 1})")
            except Exception as e:
                app.logger.error(f"{htno} - Error: {e} (attempt {attempt + 1})")
        return None


def run_scrape(url: str, start: int, end: int, workers: int) -> Dict:
    cfg = Config()
    # clone headers to avoid mutating class defaults
    cfg.HEADERS = dict(cfg.HEADERS)
    cfg.URL = url or cfg.URL
    cfg.HEADERS["Referer"] = cfg.URL
    cfg.START_HT = start
    cfg.END_HT = end
    cfg.PARALLEL_WORKERS = max(1, min(int(workers or 1), 20))
    # Disable disk output for web mode
    cfg.OUTPUT_FILE = ""

    scraper = WebScraper(cfg)

    if cfg.PARALLEL_WORKERS > 1:
        scraper.scrape_parallel()
    else:
        scraper.scrape_sequential()

    summary = {
        "success": scraper.stats.get("success", 0),
        "failed": scraper.stats.get("failed", 0),
        "skipped": scraper.stats.get("skipped", 0),
        "errors": scraper.stats.get("errors", []),
        "count": len(scraper.results),
        "range": [cfg.START_HT, cfg.END_HT],
        "url": cfg.URL,
        "workers": cfg.PARALLEL_WORKERS,
    }
    return {"results": scraper.results, "summary": summary}


@app.route("/", methods=["GET"])
def index():
    default_url = Config.URL
    return render_template("index.html", default_url=default_url)


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    global last_results, last_summary
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or Config.URL).strip()
    try:
        start = int(data.get("start") or 0)
        end = int(data.get("end") or 0)
        workers = int(data.get("workers") or 1)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid input."}), 400

    if start <= 0 or end <= 0 or end < start:
        return jsonify({"error": "Invalid range provided."}), 400

    workers = max(1, min(workers, 20))

    result = run_scrape(url, start, end, workers)
    last_results = result["results"]
    last_summary = result["summary"]
    return jsonify(result)


@app.route("/json")
def json_view():
    return jsonify(last_results)


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    # Run local dev server
    app.run(host="127.0.0.1", port=5000, debug=True)
