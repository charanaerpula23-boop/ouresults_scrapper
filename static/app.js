// Store all data globally for search
let allResultsData = { headers: [], rows: [] };

function startScrape() {
  document.getElementById("btnText").innerText = "Scraping...";
  document.getElementById("loader").classList.remove("hidden");
  document.getElementById("startBtn").disabled = true;

  fetch("/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url: url.value,
      start: start.value,
      end: end.value,
      workers: workers.value
    })
  });
}

function renderTable(data) {
  if (!data.rows.length) return;

  document.getElementById("btnText").innerText = "Start Scraping";
  document.getElementById("loader").classList.add("hidden");
  document.getElementById("startBtn").disabled = false;

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
    tbody.innerHTML += `
      <tr>
        <td>${r.hallticket}</td>
        <td>${r.name}</td>
        <td>${r.father}</td>
        ${r.grades.map(g =>
          `<td class="grade grade-${g}">${g}</td>`
        ).join("")}
        <td class="status">${r.status}</td>
      </tr>
    `;
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

  renderTable({ headers: allResultsData.headers, rows: filteredRows });
}

// Add search event listener
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener('input', searchTable);
  }
});

function downloadPDF() {
  const { jsPDF } = window.jspdf;
  const resultsTable = document.getElementById('resultsTable');
  
  if (!resultsTable || !tbody.children.length) {
    alert('No results to download!');
    return;
  }

  // Show loading state
  const downloadBtn = event.target.closest('.download-btn');
  const originalText = downloadBtn.innerHTML;
  downloadBtn.innerHTML = '<span class="loader"></span> Generating...';
  downloadBtn.disabled = true;

  // Use html2canvas to capture the table
  html2canvas(resultsTable, {
    scale: 2,
    backgroundColor: '#1a1a1a',
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
    pdf.save(`OU_Results_${new Date().toISOString().split('T')[0]}.pdf`);

    // Restore button
    downloadBtn.innerHTML = originalText;
    downloadBtn.disabled = false;
  }).catch(error => {
    console.error('PDF generation failed:', error);
    alert('Failed to generate PDF. Please try again.');
    downloadBtn.innerHTML = originalText;
    downloadBtn.disabled = false;
  });
}

setInterval(() => {
  fetch("/results")
    .then(r => r.json())
    .then(data => {
      allResultsData = data;
      
      // Only render if search is not active
      const searchTerm = document.getElementById("searchInput")?.value;
      if (!searchTerm) {
        renderTable(data);
      } else {
        searchTable(); // Re-apply search with updated data
      }
    });
}, 1500);
