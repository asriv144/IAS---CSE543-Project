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
  const current = window.location.href.split(/[?#]/)[0].replace(/^https?:\/\//, ""); // Strip query, remove http/https for comparison
  if (badUrls.some(u => current === u)) {
    // Give user a "Get me out of here!" prompt
    if (confirm("⚠️ WARNING: This site matches a known phishing URL! Click OK to be redirected to a safe page.")) {
      window.location.href = "https://www.google.com";
    }
  }
})();
