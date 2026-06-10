// Nexus Web Configuration
// Configure the URL of your deployed Railway Flask backend (include protocol, e.g. https://xxx.up.railway.app, no trailing slash).
// Set to "" to use relative paths for local development.
window.BACKEND_URL = "";

// Helper function to resolve API endpoints dynamically
window.getApiUrl = function (path) {
    if (window.BACKEND_URL) {
        return window.BACKEND_URL + path;
    }
    return path;
};
