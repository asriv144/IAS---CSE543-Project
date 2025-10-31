async function loadBadUrls() {
  const res = await fetch(chrome.runtime.getURL("phishing_site_urls.csv"));
  const text = await res.text();

  // Split into lines, skip header, and parse each row
  const lines = text.split(/\r?\n/).filter(Boolean);
  const badUrls = [];

  for (let i = 1; i < lines.length; i++) {
    const [url, label] = lines[i].split(",").map(s => s.trim().replace(/^"|"$/g, ""));
    if (label && label.toLowerCase().includes("bad")) {
      badUrls.push(url);
    }
  }

  return badUrls;
}

(async () => {
  const badUrls = await loadBadUrls();
  const current = window.location.href;

  // You can adjust this comparison to be stricter (e.g., exact match)
  if (badUrls.some(u => current.includes(u))) {
    alert("⚠️ WARNING: This site matches a known phishing URL!");
  }
})();
