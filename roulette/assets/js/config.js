// Configuration for Roulette Frontend
// Update this file with your server address

const CONFIG = {
    // Backend API server URL
    serverAddress: 'http://13.61.3.232:5000',

    // Game settings
    minBet: 1,
    maxBet: 1000,

    // UI settings
    toastDuration: 2000, // milliseconds
};

// Make config available globally
window.ROULETTE_CONFIG = CONFIG;
