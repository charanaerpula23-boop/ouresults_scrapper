# OU Results Scraper

A Flask web application to scrape and display Osmania University examination results.

## Features

- 🔍 Bulk hall ticket number scraping
- 📊 Real-time result fetching
- 🎨 Modern, responsive UI
- 📈 Summary statistics
- 💾 JSON export functionality

## Installation

1. Clone the repository:
```bash
git clone https://github.com/charanaerpula23-boop/ouresults_scrapper.git
cd ouresults_scrapper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Web Application (Main)

Run the Flask web app:
```bash
python flaskapp.py
```

Then open your browser and navigate to `http://localhost:5000`

**Note:** `flaskapp.py` is the main application for web-based result scraping.

### Command Line Tool (Optional)

For command-line batch processing:
```bash
python app.py
```

## Features Overview

### Web Interface (`flaskapp.py`) - **Main Application**
- Enter hall ticket number ranges
- View results in real-time
- Export results as JSON
- See summary statistics
- No file I/O - results stored in memory

### CLI Tool (`app.py`) - **Optional**
- Batch processing with configurable ranges
- Automatic retry mechanism
- Progress tracking
- Saves results to `ou_results.json`

## Configuration

Edit the `Config` class in `app.py` to customize:
- Start and end hall ticket numbers
- Number of worker threads
- Retry attempts
- Request timeout

## Requirements

- Python 3.7+
- Flask
- requests
- BeautifulSoup4
- urllib3

## Deployment on PythonAnywhere

See deployment instructions below for hosting this application on PythonAnywhere.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Please use responsibly and respect the university's terms of service.
