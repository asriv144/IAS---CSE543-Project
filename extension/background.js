// // extension/background.js (replace existing file with this)

// /*
//   Background service worker (debug + auto-open popup)
//   - Logs useful info
//   - Calls the /predict API
//   - Saves prediction to chrome.storage.local
//   - Attempts to open the popup automatically via chrome.action.openPopup()
//   - Falls back to a chrome notification if openPopup() is blocked
// */

// console.log("BG: service worker loaded (debug)");

// const PREDICT_URL = "http://127.0.0.1:8000/predict"; // change port if your API uses another one

// // helper to show a desktop notification (fallback)
// function showNotification(title, message) {
//   // ask for permission - not required for extensions, but safe
//   if (chrome.notifications) {
//     chrome.notifications.create({
//       type: "basic",
//       iconUrl: "icon.png", // optional - if you don't have an icon, keep this or remove
//       title: title,
//       message: message,
//     });
//   } else {
//     console.log("BG: notifications not available");
//   }
// }

// chrome.runtime.onInstalled.addListener(() => {
//   console.log("BG: onInstalled - setting initial lastPrediction");
//   chrome.storage.local.set({ lastPrediction: { label: 0, confidence: 0.0, url: "init" } });
// });

// chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
//   console.log("BG: message received", msg);

//   if (msg.type === "CHECK_URL") {
//     fetch(PREDICT_URL, {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ url: msg.url })
//     })
//     .then(resp => {
//       if (!resp.ok) throw new Error("Network response not ok: " + resp.status);
//       return resp.json();
//     })
//     .then(data => {
//       console.log("BG: prediction received", data);
//       // store the prediction
//       chrome.storage.local.set({ lastPrediction: { ...data, url: msg.url } }, () => {
//         // set badge accordingly
//         if (data.label === 1) {
//           chrome.action.setBadgeText({ text: "PH" });
//           chrome.action.setBadgeBackgroundColor({ color: [200, 0, 0, 255] });
//         } else {
//           chrome.action.setBadgeText({ text: "" });
//         }

//         // Try to open popup programmatically (MV3)
//         // Note: chrome.action.openPopup may fail in some circumstances; we catch failures below.
//         try {
//           chrome.action.openPopup(() => {
//             // callback fires after attempting to open popup
//             const err = chrome.runtime.lastError;
//             if (err) {
//               console.warn("BG: openPopup failed:", err);
//               // fallback to a notification so user sees result
//               const title = data.label === 1 ? "PhishDetect — PHISH" : "PhishDetect — SAFE";
//               const msgText = `URL: ${msg.url}\nConfidence: ${data.confidence}`;
//               showNotification(title, msgText);
//             } else {
//               console.log("BG: openPopup succeeded or was attempted");
//             }
//           });
//         } catch (ex) {
//           console.error("BG: openPopup exception", ex);
//           const title = data.label === 1 ? "PhishDetect — PHISH" : "PhishDetect — SAFE";
//           showNotification(title, `URL: ${msg.url}\nConfidence: ${data.confidence}`);
//         }
//       });
//     })
//     .catch(err => {
//       console.error("BG: Predict API error:", err);
//       // show notification for API failure
//       showNotification("PhishDetect — error", String(err));
//     });

//     // Return true to indicate we will call sendResponse asynchronously (not strictly required here)
//     return true;
//   }
// });

// extension/background.js
// Service worker background script for PhishDetect
// Replace PREDICT_URL if your API runs on a different host/port.

const PREDICT_URL = "http://127.0.0.1:8000/predict"; // ensure this matches your uvicorn host:port

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

/* --- Optional: monitor active tab changes too --- */
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

/* --- graceful shutdown / cleanup (not required but good practice) --- */
self.addEventListener('install', (e) => {
  // activate as soon as installed
  self.skipWaiting();
});
self.addEventListener('activate', (e) => {
  self.clients.claim();
});

console.log("BG: listeners installed (debug)");
