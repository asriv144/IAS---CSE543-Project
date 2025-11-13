document.addEventListener('DOMContentLoaded', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs[0]) {
            showError('No active tab found');
            return;
        }

        const currentTab = tabs[0];
        const url = currentTab.url;

        // Display URL
        document.getElementById('urlDisplay').textContent = url.length > 50 
            ? url.substring(0, 47) + '...' 
            : url;

        // Listen for real-time updates from background script
        chrome.storage.onChanged.addListener((changes, area) => {
            if (area === 'local' && changes[url]) {
                updateDisplay(url);
            }
        });

        // Initial check
        updateDisplay(url);
    });
});

function updateDisplay(url) {
    chrome.storage.local.get([url], (result) => {
        if (result[url] && result[url].status) {
            const status = result[url].status;
            hideAllStates();

            if (status === 'safe') {
                showSafe();
            } else if (status === 'phishing') {
                showPhishing();
            } else {
                showError('Unknown status');
            }
        } else {
            // Still analyzing
            hideAllStates();
            document.getElementById('loading').style.display = 'flex';
        }
    });
}

function hideAllStates() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('safe').style.display = 'none';
    document.getElementById('phishing').style.display = 'none';
    document.getElementById('error').style.display = 'none';
}

function showSafe() {
    document.getElementById('safe').style.display = 'block';
    animateConfidenceBar('confidenceSafe', 'confidenceTextSafe', 85);
}

function showPhishing() {
    document.getElementById('phishing').style.display = 'block';
    animateConfidenceBar('confidenceDanger', 'confidenceTextDanger', 92);
}

function showError(message) {
    document.getElementById('error').style.display = 'block';
}

function animateConfidenceBar(barId, textId, targetPercentage) {
    let current = 0;
    const interval = setInterval(() => {
        current += Math.random() * 20;
        if (current >= targetPercentage) {
            current = targetPercentage;
            clearInterval(interval);
        }
        document.getElementById(barId).style.width = current + '%';
        document.getElementById(textId).textContent = Math.round(current) + '%';
    }, 50);
}
