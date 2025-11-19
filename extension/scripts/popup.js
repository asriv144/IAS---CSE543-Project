const API_URL = "http://127.0.0.1:8000/check_url";
document.addEventListener("DOMContentLoaded", () => {

  async function checkUrl(url) {
    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) {
        console.warn("Popup → backend non-200:", res.status);
        return { isPhishing: false, raw: null };
      }

      const data = await res.json();
      console.log("Popup → backend result:", data);

      const isPhishing = !!(
        data.is_phishing ??
        data.phishing ??
        (data.label === "bad")
      );

      return { isPhishing, raw: data };
    } catch (e) {
      console.warn("Popup → backend unreachable", e);
      return { isPhishing: false, raw: null };
    }
  }

  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const status = document.getElementById("status");
    const tab = tabs[0];
    if (!tab || !tab.url) {
      status.textContent = "Not a valid page.";
      return;
    }

    let url;
    try {
      url = tab.url;
      const parsed = new URL(url);
      if (!/^https?:$/.test(parsed.protocol)) {
        status.textContent = "Not an HTTP/HTTPS page.";
        return;
      }
    } catch (e) {
      status.textContent = "Invalid URL.";
      return;
    }

    status.textContent = "Checking with ML model...";

    const result = await checkUrl(url);

    document.getElementById("loading").style.display = "none";
    document.getElementById("urlDisplay").textContent = url;
    if (result.isPhishing) {
      document.getElementById("phishing").style.display = "block";
      document.getElementById("safe").style.display = "none";
      document.getElementById("confidenceTextDanger").textContent = `${(Number(result.raw.probability * 100).toFixed(2))}% (${result.raw.confidence} confidence)`;
      status.style.color = "#b00020";
      status.textContent = "⚠️ PHISHING SITE DETECTED!";
    } else {
      document.getElementById("safe").style.display = "block";
      document.getElementById("phishing").style.display = "none";
      document.getElementById("confidenceTextSafe").textContent = `${(Number(result.raw.probability * 100).toFixed(2))}% (${result.raw.confidence} confidence)`;
      status.style.color = "#0b8043";
      status.textContent = "✓ Not flagged by ML model";
    }
  });
});
