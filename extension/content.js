(function(){
  const url = window.location.href;
  // send page URL to background service worker
  chrome.runtime.sendMessage({type: "CHECK_URL", url: url});
})();
