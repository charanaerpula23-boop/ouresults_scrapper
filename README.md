# OU Results Scraper

A modern Flask web application to scrape and display Osmania University exam results with a sleek dark theme interface.

## Features

- 🚀 **Fast Concurrent Scraping** - Multi-threaded result fetching
- 🎨 **Modern Dark UI** - Beautiful black theme with cyan accents
- 🔍 **Real-time Search** - Instant table filtering
- 📥 **PDF Export** - Download results as PDF
- 📊 **Live Updates** - Auto-refresh every 1.5 seconds
- 🎯 **Grade Visualization** - Color-coded grade display

## Screenshots

![OU Results Scraper Interface](https://via.placeholder.com/800x400?text=OU+Results+Scraper)

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/ouresults_scrapper.git
cd ouresults_scrapper
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## PythonAnywhere Deployment

1. Create a PythonAnywhere account at [pythonanywhere.com](https://www.pythonanywhere.com)

2. Open a Bash console and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/ouresults_scrapper.git
cd ouresults_scrapper
```

3. Create a virtual environment:
```bash
mkvirtualenv --python=/usr/bin/python3.10 ouresults
pip install -r requirements.txt
```

4. Configure the web app:
   - Go to Web tab
   - Add a new web app
   - Select Manual configuration
   - Choose Python 3.10
   - Set source code directory: `/home/YOUR_USERNAME/ouresults_scrapper`
   - Set working directory: `/home/YOUR_USERNAME/ouresults_scrapper`
   - Edit WSGI file to point to your app

5. Reload the web app

## Usage

1. Enter the OU results URL
2. Specify the start and end hall ticket numbers
3. Set the number of concurrent workers (default: 5)
4. Click "Start Scraping"
5. Use the search box to filter results
6. Download results as PDF using the download button

## Configuration

- **Workers**: Adjust the number of concurrent threads (1-20)
- **URL**: Default OU results URL can be modified
- **Timeout**: Request timeout set to 15 seconds

## Technologies Used

- **Backend**: Flask, Python
- **Frontend**: HTML5, CSS3, JavaScript
- **Scraping**: BeautifulSoup4, Requests
- **PDF Generation**: jsPDF, html2canvas
- **Styling**: Custom CSS with dark theme

## API Endpoints

- `GET /` - Main interface
- `POST /start` - Start scraping process
- `GET /results` - Get current results (JSON)
- `GET /logs` - Get scraping logs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Author

**Charan**

## Disclaimer

This tool is for educational purposes only. Please respect the university's terms of service and use responsibly.
