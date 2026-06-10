// Nexus Web Configuration
// Configure the URL of your deployed Railway Flask backend (include protocol, e.g. https://xxx.up.railway.app, no trailing slash).
window.BACKEND_URL = "https://nexus-ai-b8zi.onrender.com";
window.getApiUrl = function (path) {
    if (window.BACKEND_URL) {
        return window.BACKEND_URL + path;
    }
    return path;
};
