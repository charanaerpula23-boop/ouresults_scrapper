// Store all data globally for search
let allResultsData = { headers: [], rows: [] };
let isScrapingActive = false;

// Terminal logging
function addTerminalLog(message) {
  const terminalLogs = document.getElementById('terminalLogs');
  const logLine = document.createElement('div');
  logLine.className = 'terminal-line';
  logLine.textContent = message;
  terminalLogs.appendChild(logLine);
  
  // Auto-scroll to bottom
  terminalLogs.scrollTop = terminalLogs.scrollHeight;
  
  // Keep only last 50 logs
  const logs = terminalLogs.querySelectorAll('.terminal-line');
  if (logs.length > 50) {
    logs[0].remove();
  }
}

function startScrape() {
  isScrapingActive = true;
  document.getElementById("btnText").innerText = "Scraping...";
  document.getElementById("loader").classList.remove("hidden");
  document.getElementById("startBtn").disabled = true;

  addTerminalLog(`Starting scraper with ${workers.value} workers...`);
  addTerminalLog(`Range: ${start.value} to ${end.value}`);
  addTerminalLog(`Target URL: ${url.value}`);

  fetch("/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url: url.value,
      start: start.value,
      end: end.value,
      workers: workers.value
    })
  }).then(() => {
    addTerminalLog('Scraping initiated successfully!');
  }).catch(err => {
    addTerminalLog(`Error: ${err.message}`);
  });
}

function renderTable(data) {
  if (!data.rows.length) return;

  if (isScrapingActive) {
    document.getElementById("btnText").innerText = "Start Scraping";
    document.getElementById("loader").classList.add("hidden");
    document.getElementById("startBtn").disabled = false;
    addTerminalLog(`Scraping completed! Total results: ${data.rows.length}`);
    isScrapingActive = false;
  }

  thead.innerHTML = `
    <tr>
      <th>Hallticket</th>
      <th>Name</th>
      <th>Father</th>
      ${data.headers.map(h => `<th>${h}</th>`).join("")}
      <th>Status</th>
    </tr>
  `;

  tbody.innerHTML = "";

  data.rows.forEach(r => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${r.hallticket}</td>
      <td>${r.name}</td>
      <td>${r.father}</td>
      ${r.grades.map(g =>
        `<td><span class="grade grade-${g}">${g}</span></td>`
      ).join("")}
      <td><span class="status">${r.status}</span></td>
    `;
    tbody.appendChild(row);
  });
}

function searchTable() {
  const searchTerm = document.getElementById("searchInput").value.toLowerCase();
  
  if (!searchTerm) {
    renderTable(allResultsData);
    return;
  }

  const filteredRows = allResultsData.rows.filter(row => {
    return (
      row.hallticket.toLowerCase().includes(searchTerm) ||
      row.name.toLowerCase().includes(searchTerm) ||
      row.father.toLowerCase().includes(searchTerm) ||
      row.status.toLowerCase().includes(searchTerm) ||
      row.grades.some(g => g.toLowerCase().includes(searchTerm))
    );
  });

  addTerminalLog(`Search: "${searchTerm}" - ${filteredRows.length} results found`);
  renderTable({ headers: allResultsData.headers, rows: filteredRows });
}

// Add search event listener
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener('input', searchTable);
  }
  addTerminalLog('System initialized. Ready to scrape!');
});

function downloadPDF() {
  const { jsPDF } = window.jspdf;
  const resultsTable = document.getElementById('resultsTable');
  
  if (!resultsTable || !tbody.children.length) {
    alert('No results to download!');
    addTerminalLog('PDF download failed: No results available');
    return;
  }

  addTerminalLog('Generating PDF...');

  // Show loading state
  const downloadBtn = event.target.closest('.download-btn');
  const originalText = downloadBtn.innerHTML;
  downloadBtn.innerHTML = '<span class="loader"></span> Generating...';
  downloadBtn.disabled = true;

  // Use html2canvas to capture the table
  html2canvas(resultsTable, {
    scale: 2,
    backgroundColor: '#171717',
    logging: false
  }).then(canvas => {
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'landscape',
      unit: 'mm',
      format: 'a4'
    });

    const imgWidth = 297; // A4 landscape width in mm
    const pageHeight = 210; // A4 landscape height in mm
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    let heightLeft = imgHeight;
    let position = 0;

    // Add first page
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;

    // Add additional pages if needed
    while (heightLeft > 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }

    // Save the PDF
    const filename = `OU_Results_${new Date().toISOString().split('T')[0]}.pdf`;
    pdf.save(filename);
    addTerminalLog(`PDF downloaded: ${filename}`);

    // Restore button
    downloadBtn.innerHTML = originalText;
    downloadBtn.disabled = false;
  }).catch(error => {
    console.error('PDF generation failed:', error);
    alert('Failed to generate PDF. Please try again.');
    addTerminalLog(`PDF generation error: ${error.message}`);
    downloadBtn.innerHTML = originalText;
    downloadBtn.disabled = false;
  });
}

let lastRowCount = 0;
let lastLogCount = 0;

setInterval(() => {
  // Fetch results
  fetch("/results")
    .then(r => r.json())
    .then(data => {
      allResultsData = data;
      
      // Log progress during scraping
      if (isScrapingActive && data.rows.length > lastRowCount) {
        addTerminalLog(`Fetched ${data.rows.length} results...`);
        lastRowCount = data.rows.length;
      }
      
      // Only render if search is not active
      const searchTerm = document.getElementById("searchInput")?.value;
      if (!searchTerm) {
        renderTable(data);
      } else {
        searchTable(); // Re-apply search with updated data
      }
    });

  // Fetch backend logs
  fetch("/logs")
    .then(r => r.json())
    .then(data => {
      if (data.logs && data.logs.length > lastLogCount) {
        // Add new logs
        for (let i = lastLogCount; i < data.logs.length; i++) {
          addTerminalLog(data.logs[i]);
        }
        lastLogCount = data.logs.length;
      }
    });
}, 1500);
