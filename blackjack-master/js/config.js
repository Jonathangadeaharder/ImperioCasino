// Configuration for Blackjack Frontend
// Update this file with your server address

const CONFIG = {
    // Backend API server URL
    serverAddress: 'http://13.61.3.232:5000',

    // Game settings
    defaultChipValues: [10, 25, 50, 100],

    // UI settings
    toastDuration: 2000, // milliseconds
};

// Make config available globally
window.BLACKJACK_CONFIG = CONFIG;
