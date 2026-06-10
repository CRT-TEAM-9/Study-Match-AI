// Nexus - Connection Offline Overlay Handler
document.addEventListener("DOMContentLoaded", () => {
    // Inject the offline overlay CSS
    const style = document.createElement("style");
    style.textContent = `
        #offline-overlay {
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease-in-out;
        }
        #offline-overlay.show {
            opacity: 1;
            pointer-events: auto;
        }
    `;
    document.head.appendChild(style);

    // Create overlay container
    const overlay = document.createElement("div");
    overlay.id = "offline-overlay";
    overlay.className = "fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm px-6 text-center";
    overlay.innerHTML = `
        <div class="bg-surface border border-outline-variant p-8 rounded-xl max-w-sm w-full flex flex-col items-center gap-4 text-primary shadow-2xl transition-colors duration-200">
            <div class="w-16 h-16 rounded-full bg-surface-variant flex items-center justify-center border border-outline-variant shadow-[0px_4px_16px_rgba(0,0,0,0.02)]">
                <span class="material-symbols-outlined text-red-500 text-[36px] animate-pulse">wifi_off</span>
            </div>
            <div class="flex flex-col gap-1">
                <h2 class="text-xl font-bold tracking-tight">Connection Offline</h2>
                <p class="text-xs text-on-surface-variant text-gray-500">We lost connection to the Nexus server. Reconnecting automatically when online...</p>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    let isOffline = false;

    function setOfflineState(offline) {
        if (offline) {
            overlay.classList.add("show");
            isOffline = true;
        } else {
            overlay.classList.remove("show");
            isOffline = false;
        }
    }

    // 1. Browser connectivity API listeners
    window.addEventListener("offline", () => setOfflineState(true));
    window.addEventListener("online", () => checkServerConnection());

    // 2. Active Server Ping check (handles local server process downtime)
    async function checkServerConnection() {
        if (!navigator.onLine) {
            setOfflineState(true);
            return;
        }
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000); // 3s timeout
            const apiUrl = window.getApiUrl ? window.getApiUrl("/api/stats") : "/api/stats";
            const res = await fetch(apiUrl, { signal: controller.signal });
            clearTimeout(timeoutId);
            if (res.ok) {
                setOfflineState(false);
            } else {
                setOfflineState(true);
            }
        } catch (err) {
            setOfflineState(true);
        }
    }

    // Run check on startup
    checkServerConnection();

    // Periodic check (every 5 seconds) to ensure server connection is alive
    setInterval(checkServerConnection, 5000);
});
