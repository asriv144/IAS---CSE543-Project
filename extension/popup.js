// popup.js
const statusEl = document.getElementById('status');
const detailsEl = document.getElementById('details');
const rawEl = document.getElementById('raw');

function render(p) {
  if (!p) {
    statusEl.innerText = "No prediction yet. Reload the page to trigger detection.";
    detailsEl.innerText = "";
    rawEl.style.display = "none";
    rawEl.innerText = "";
    return;
  }
  const labelText = p.label === 1 ? "PHISH" : "SAFE";
  statusEl.innerHTML = `<span class="${p.label===1 ? 'phish' : 'safe'}">${labelText}</span> — Confidence: ${p.confidence.toFixed(3)}`;
  detailsEl.innerText = `URL: ${p.url || "(unknown)"}`;
  rawEl.style.display = "block";
  rawEl.innerText = JSON.stringify(p, null, 2);
}

// initial load: read storage
chrome.storage.local.get('lastPrediction', (data) => {
  try {
    console.log("Popup: loaded storage", data);
    render(data.lastPrediction);
  } catch (e) {
    console.error("Popup: error reading storage", e);
    statusEl.innerText = "Error reading storage. See console.";
  }
});

// listen for updates while popup is open
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes.lastPrediction) {
    console.log("Popup: storage changed", changes.lastPrediction.newValue);
    render(changes.lastPrediction.newValue);
  }
});
