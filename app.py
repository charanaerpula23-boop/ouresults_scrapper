import requests
from bs4 import BeautifulSoup
import time
import json
import urllib3
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
import argparse

# ================= SSL FIX =================
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= LOGGING SETUP =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Fix Windows console encoding
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ================= DATA CLASSES =================
@dataclass
class Subject:
    code: str
    name: str
    credits: str
    grade: str

@dataclass
class Student:
    hallticket: str
    gender: str
    name: str
    father: str
    course: str

@dataclass
class Result:
    student: Student
    subjects: List[Subject]
    final_result: str
    fetch_timestamp: str

# ================= CONFIG =================
class Config:
    URL = "https://www.osmania.ac.in/res07/20250686.jsp"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": URL,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    START_HT = 110624861010
    END_HT = 110624861020
    DELAY_SECONDS = 0.5
    OUTPUT_FILE = "ou_results.json"
    MAX_RETRIES = 3
    TIMEOUT = 20
    PARALLEL_WORKERS = 3  # Concurrent requests

# ================= SCRAPER CLASS =================
class OUResultsScraper:
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.results: List[Dict] = []
        self.stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    def load_existing_results(self) -> List[Dict]:
        """Load existing results with error handling"""
        if not os.path.exists(self.config.OUTPUT_FILE):
            logger.info(f"No existing file found. Starting fresh.")
            return []
        
        try:
            with open(self.config.OUTPUT_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                logger.info(f"Loaded {len(data)} existing results")
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading existing file: {e}. Starting fresh.")
            # Backup corrupted file
            backup_name = f"{self.config.OUTPUT_FILE}.backup_{int(time.time())}"
            os.rename(self.config.OUTPUT_FILE, backup_name)
            logger.info(f"Backed up corrupted file to {backup_name}")
            return []
    
    def save_results(self, results: List[Dict]):
        """Save results with atomic write"""
        temp_file = f"{self.config.OUTPUT_FILE}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, self.config.OUTPUT_FILE)
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def parse_result_page(self, soup: BeautifulSoup) -> Optional[Result]:
        """Parse the result page and extract data"""
        try:
            # Check if result exists
            personal_table = soup.find(id="AutoNumber3")
            if not personal_table:
                return None
            
            # Personal details
            rows = personal_table.find_all("tr")
            if len(rows) < 4:
                return None
            
            student = Student(
                hallticket=rows[1].find_all("td")[1].get_text(strip=True),
                gender=rows[1].find_all("td")[3].get_text(strip=True),
                name=rows[2].find_all("td")[1].get_text(strip=True),
                father=rows[2].find_all("td")[3].get_text(strip=True),
                course=rows[3].find_all("td")[1].get_text(strip=True)
            )
            
            # Marks table
            marks_table = soup.find(id="AutoNumber4")
            if not marks_table:
                return None
            
            subjects = []
            mark_rows = marks_table.find_all("tr")[2:]  # Skip headers
            
            for row in mark_rows:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    subjects.append(Subject(
                        code=cols[0].get_text(strip=True),
                        name=cols[1].get_text(strip=True),
                        credits=cols[2].get_text(strip=True),
                        grade=cols[3].get_text(strip=True)
                    ))
            
            # Final result
            result_table = soup.find(id="AutoNumber5")
            if not result_table:
                return None
            
            result_row = result_table.find_all("tr")[2]
            final_result = result_row.find_all("td")[2].get_text(strip=True)
            
            return Result(
                student=student,
                subjects=subjects,
                final_result=final_result,
                fetch_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Parsing error: {e}")
            return None
    
    def fetch_result(self, htno: str) -> Optional[Dict]:
        """Fetch a single result with retry logic"""
        payload = {
            "mbstatus": "SEARCH",
            "htno": htno,
            "Submit.x": "25",
            "Submit.y": "8"
        }
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                response = self.session.post(
                    self.config.URL,
                    data=payload,
                    headers=self.config.HEADERS,
                    timeout=self.config.TIMEOUT,
                    verify=False
                )
                
                if response.status_code != 200:
                    logger.warning(f"{htno} - HTTP {response.status_code} (attempt {attempt + 1})")
                    time.sleep(1)
                    continue
                
                soup = BeautifulSoup(response.text, "html.parser")
                result = self.parse_result_page(soup)
                
                if result:
                    return {
                        "student": asdict(result.student),
                        "subjects": [asdict(s) for s in result.subjects],
                        "final_result": result.final_result,
                        "fetch_timestamp": result.fetch_timestamp
                    }
                else:
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"{htno} - Timeout (attempt {attempt + 1})")
                time.sleep(2)
            except Exception as e:
                logger.error(f"{htno} - Error: {e} (attempt {attempt + 1})")
                time.sleep(1)
        
        return None
    
    def scrape_sequential(self):
        """Sequential scraping (original behavior)"""
        self.results = self.load_existing_results()
        fetched_hts = {
            r.get("student", {}).get("hallticket")
            for r in self.results
            if r.get("student")
        }
        
        total = self.config.END_HT - self.config.START_HT + 1
        progress = 0
        
        for ht in range(self.config.START_HT, self.config.END_HT + 1):
            htno = str(ht)
            progress += 1
            
            if htno in fetched_hts:
                logger.info(f"[{progress}/{total}] {htno} - SKIPPED (already saved)")
                self.stats['skipped'] += 1
                continue
            
            logger.info(f"[{progress}/{total}] Fetching {htno}...")
            
            data = self.fetch_result(htno)
            if data:
                self.results.append(data)
                self.save_results(self.results)
                self.stats['success'] += 1
                logger.info(f"[{progress}/{total}] {htno} - [OK] SAVED")
            else:
                self.stats['failed'] += 1
                self.stats['errors'].append(htno)
                logger.warning(f"[{progress}/{total}] {htno} - [FAIL] NO RESULT")
            
            time.sleep(self.config.DELAY_SECONDS)
    
    def scrape_parallel(self):
        """Parallel scraping for faster execution"""
        self.results = self.load_existing_results()
        fetched_hts = {
            r.get("student", {}).get("hallticket")
            for r in self.results
            if r.get("student")
        }
        
        htnos = [
            str(ht) for ht in range(self.config.START_HT, self.config.END_HT + 1)
            if str(ht) not in fetched_hts
        ]
        
        total = len(htnos)
        logger.info(f"Starting parallel scrape for {total} hall tickets...")
        
        with ThreadPoolExecutor(max_workers=self.config.PARALLEL_WORKERS) as executor:
            future_to_htno = {
                executor.submit(self.fetch_result, htno): htno
                for htno in htnos
            }
            
            completed = 0
            for future in as_completed(future_to_htno):
                htno = future_to_htno[future]
                completed += 1
                
                try:
                    data = future.result()
                    if data:
                        self.results.append(data)
                        self.save_results(self.results)
                        self.stats['success'] += 1
                        logger.info(f"[{completed}/{total}] {htno} - [OK] SAVED")
                    else:
                        self.stats['failed'] += 1
                        self.stats['errors'].append(htno)
                        logger.warning(f"[{completed}/{total}] {htno} - [FAIL] NO RESULT")
                except Exception as e:
                    self.stats['failed'] += 1
                    self.stats['errors'].append(htno)
                    logger.error(f"[{completed}/{total}] {htno} - ERROR: {e}")
                
                time.sleep(self.config.DELAY_SECONDS / self.config.PARALLEL_WORKERS)
    
    def print_summary(self):
        """Print scraping summary"""
        logger.info("\n" + "="*50)
        logger.info("SCRAPING SUMMARY")
        logger.info("="*50)
        logger.info(f"[OK] Success: {self.stats['success']}")
        logger.info(f"[FAIL] Failed: {self.stats['failed']}")
        logger.info(f"[SKIP] Skipped: {self.stats['skipped']}")
        logger.info(f"[FILE] Output: {self.config.OUTPUT_FILE}")
        
        if self.stats['errors']:
            logger.warning(f"\nFailed hall tickets: {', '.join(self.stats['errors'])}")
        
        logger.info("="*50)

# ================= MAIN =================
def main():
    parser = argparse.ArgumentParser(description='OU Results Scraper')
    parser.add_argument('--start', type=int, default=Config.START_HT, help='Starting hall ticket number')
    parser.add_argument('--end', type=int, default=Config.END_HT, help='Ending hall ticket number')
    parser.add_argument('--parallel', action='store_true', help='Use parallel scraping')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers')
    parser.add_argument('--output', type=str, default=Config.OUTPUT_FILE, help='Output JSON file')
    
    args = parser.parse_args()
    
    config = Config()
    config.START_HT = args.start
    config.END_HT = args.end
    config.OUTPUT_FILE = args.output
    config.PARALLEL_WORKERS = args.workers
    
    scraper = OUResultsScraper(config)
    
    logger.info(f"Starting scraper: {config.START_HT} to {config.END_HT}")
    logger.info(f"Mode: {'Parallel' if args.parallel else 'Sequential'}")
    
    start_time = time.time()
    
    if args.parallel:
        scraper.scrape_parallel()
    else:
        scraper.scrape_sequential()
    
    elapsed = time.time() - start_time
    logger.info(f"\n[TIME] Total time: {elapsed:.2f} seconds")
    
    scraper.print_summary()

if __name__ == "__main__":
    main()