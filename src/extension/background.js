// background.js
chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === "CHECK_URL") {
    fetch("http://localhost:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: msg.url })
    })
    .then(resp => resp.json())
    .then(data => {
      // set badge to show PH for phishing
      if (data.label === 1) {
        chrome.action.setBadgeText({ text: "PH" });
        chrome.action.setBadgeBackgroundColor({ color: [200, 0, 0, 255] });
      } else {
        chrome.action.setBadgeText({ text: "" });
      }
      // store last result for popup view
      chrome.storage.local.set({ lastPrediction: data });
    })
    .catch(err => {
      console.error("Predict API error:", err);
    });
  }
});
