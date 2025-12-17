import threading, time, argparse, json
import requests, urllib3
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, render_template
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_URL = "https://www.osmania.ac.in/res07/20250265.jsp"

app = Flask(__name__)
session = requests.Session()
lock = Lock()

logs = []
results = []
processed = set()
RUNNING = False


def log(msg):
    logs.append(msg)
    if len(logs) > 200:
        logs.pop(0)


def fetch_result(htno, url):
    with lock:
        if htno in processed:
            return None
        processed.add(htno)

    r = session.post(
        url,
        data={"mbstatus": "SEARCH", "htno": htno},
        headers={"User-Agent": "Mozilla/5.0", "Referer": url},
        verify=False,
        timeout=15
    )

    soup = BeautifulSoup(r.text, "html.parser")
    if not soup.find(id="AutoNumber3"):
        return None

    rows = soup.find(id="AutoNumber3").find_all("tr")

    student = {
        "hallticket": rows[1].find_all("td")[1].text.strip(),
        "name": rows[2].find_all("td")[1].text.strip(),
        "father": rows[2].find_all("td")[3].text.strip(),
    }

    subjects = []
    for r in soup.find(id="AutoNumber4").find_all("tr")[2:]:
        c = r.find_all("td")
        subjects.append({
            "code": c[0].text.strip(),
            "name": c[1].text.strip(),
            "grade": c[3].text.strip()
        })

    final = soup.find(id="AutoNumber5").find_all("tr")[2].find_all("td")[2].text.strip()
    status = "PASSED" if final.upper().startswith("P") else "PROMOTED"

    return {
        **student,
        "subjects": subjects,
        "status": status
    }


def scrape_engine(url, start, end, workers):
    processed.clear()
    results.clear()

    hts = list(map(str, range(start, end + 1)))
    log(f"Scraping {len(hts)} halltickets")

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(fetch_result, ht, url) for ht in hts]
        for f in as_completed(futures):
            d = f.result()
            if d:
                results.append(d)
                log(f"[OK] {d['hallticket']}")

    results.sort(key=lambda x: x["hallticket"])
    log("DONE")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    global RUNNING
    if RUNNING:
        return jsonify({"error": "Already running"}), 409

    RUNNING = True
    logs.clear()
    results.clear()

    d = request.json

    def run():
        global RUNNING
        scrape_engine(
            d["url"],
            int(d["start"]),
            int(d["end"]),
            int(d["workers"])
        )
        RUNNING = False

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/results")
def get_results():
    if not results:
        return jsonify({"headers": [], "rows": []})

    headers = [
        f"{s['code']}<br><small>{s['name']}</small>"
        for s in results[0]["subjects"]
    ]

    rows = [{
        "hallticket": r["hallticket"],
        "name": r["name"],
        "father": r["father"],
        "grades": [s["grade"] for s in r["subjects"]],
        "status": r["status"]
    } for r in results]

    return jsonify({"headers": headers, "rows": rows})


if __name__ == "__main__":
    app.run(debug=True)
