// extension/scripts/content.js

const API_URL = "http://127.0.0.1:8000/check_url"; // FastAPI backend

async function checkUrl(url) {
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!res.ok) {
      console.warn("Content Script → backend returned non-200:", res.status);
      return { isPhishing: false, raw: null };
    }

    const data = await res.json();
    console.log("Content Script → backend result:", data);

    // Normalize to a single boolean
    const isPhishing = !!(
      data.is_phishing ??
      data.phishing ??
      (data.label === "bad")
    );

    return { isPhishing, raw: data };
  } catch (e) {
    console.warn("Content Script → backend unreachable, skipping check", e);
    return { isPhishing: false, raw: null };
  }
}

function showBanner(text) {
  if (document.getElementById("phishdetect-banner")) return;

  const banner = document.createElement("div");
  banner.id = "phishdetect-banner";
  banner.style.position = "fixed";
  banner.style.top = "0";
  banner.style.left = "0";
  banner.style.width = "100%";
  banner.style.background = "#d93025";
  banner.style.color = "white";
  banner.style.padding = "14px";
  banner.style.textAlign = "center";
  banner.style.fontSize = "18px";
  banner.style.zIndex = "999999";
  banner.style.boxShadow = "0 2px 8px rgba(0,0,0,0.2)";
  banner.innerText = text;

  document.body.prepend(banner);
}

(async () => {
  let url;
  try {
    url = window.location.href;
    const parsed = new URL(url);
    if (!/^https?:$/.test(parsed.protocol)) {
      // Not HTTP/HTTPS (e.g., chrome://) → skip
      return;
    }
  } catch (e) {
    console.warn("Content Script → invalid URL, skipping", e);
    return;
  }

  const result = await checkUrl(url);

  if (result.isPhishing) {
    showBanner("⚠️ WARNING: This site is classified as PHISHING by the ML model!");
  }
})();
