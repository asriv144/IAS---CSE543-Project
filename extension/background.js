const PREDICT_URL = "http://127.0.0.1:8000/predict"; // ensure this matches uvicorn host:port

console.log("BG: service worker loaded (debug)");

/* --- Helpers --- */
function isHttpUrl(url) {
  return typeof url === "string" && (url.startsWith("http://") || url.startsWith("https://"));
}

function shouldIgnoreUrl(url) {
  if (!url) return true;
  // ignore chrome internal pages and extension pages
  return url.startsWith("chrome://") || url.startsWith("chrome-extension://") || url.startsWith("about:");
}

/* send fetch to API, handle and save result, show notifications */
async function sendPredictRequest(url) {
  if (!isHttpUrl(url) || shouldIgnoreUrl(url)) {
    // nothing to do
    return;
  }

  console.log("BG: sendPredictRequest ->", url);

  try {
    const resp = await fetch(PREDICT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    const text = await resp.text();
    if (!resp.ok) {
      console.error("BG: Predict API returned error", resp.status, text);
      return;
    }

    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      console.error("BG: Invalid JSON from predict API:", text);
      return;
    }

    console.log("BG: prediction received", data);

    // store result for popup
    chrome.storage.local.set({ lastPrediction: data }, () => {
      console.log("BG: stored lastPrediction");
    });

    // show desktop notification when phish detected
    if (data && data.label === 1) {
      try {
        chrome.notifications.create({
          type: "basic",
          iconUrl: "icon48.png",
          title: "PhishDetect — PHISHING ALERT",
          message: `Phishing detected (${(data.confidence * 100).toFixed(1)}%)\n${url}`
        }, (nid) => {
          // optional callback
        });
      } catch (e) {
        console.warn("BG: notifications failed or not permitted", e);
      }
    }

    // try to open popup (may be blocked on some pages / interstitials)
    try {
      chrome.action.openPopup(() => {
        // NOTE: callback runs when popup open attempt finishes
        console.log("BG: openPopup succeeded or was attempted");
      });
    } catch (e) {
      console.warn("BG: openPopup failed (likely blocked)", e);
    }

  } catch (err) {
    console.error("BG: Predict API error:", err);
  }
}

/* --- Message listener (backwards compatibility from content scripts) --- */
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  console.log("BG: message received", msg);
  if (msg && msg.type === "CHECK_URL" && msg.url) {
    // quick respond immediately
    sendResponse({ ok: true });
    // call predict pipeline
    sendPredictRequest(msg.url);
    return true; // keep message channel open if needed
  }
  // other messages...
});

/* --- On install: initialize storage --- */
chrome.runtime.onInstalled.addListener(() => {
  console.log("BG: onInstalled - setting initial lastPrediction");
  chrome.storage.local.set({ lastPrediction: { label: null, confidence: 0, url: null } });
});

/* --- Tabs update listener: detect navigation and URL changes --- */
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  try {
    if (changeInfo && changeInfo.url) {
      console.log("BG: tab URL changed ->", changeInfo.url);
      sendPredictRequest(changeInfo.url);
      return;
    }
    // when page finishes loading (sometimes URL not present in changeInfo)
    if (changeInfo && changeInfo.status === "complete" && tab && tab.url) {
      console.log("BG: tab load complete ->", tab.url);
      sendPredictRequest(tab.url);
    }
  } catch (e) {
    console.error("BG: tabs.onUpdated handler error:", e);
  }
});

/* --- monitor active tab changes too --- */
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const t = await chrome.tabs.get(activeInfo.tabId);
    if (t && t.url) {
      console.log("BG: tab activated ->", t.url);
      sendPredictRequest(t.url);
    }
  } catch (e) {
    // ignore
  }
});

/* --- graceful shutdown / cleanup --- */
self.addEventListener('install', (e) => {
  // activate as soon as installed
  self.skipWaiting();
});
self.addEventListener('activate', (e) => {
  self.clients.claim();
});

console.log("BG: listeners installed (debug)");
