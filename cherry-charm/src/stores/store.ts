import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { Fruit } from "../utils/enums";

// Helper function to fetch initial coins
const userManagementServer = "http://13.61.3.232:5000";

async function fetchInitialCoins(userId: string): Promise<number> {
    const token = localStorage.getItem('authToken'); // Retrieve the token from local storage

    if (!token) {
        console.error("No token found. Redirecting to login.");
        window.location.href = `${userManagementServer}/login`;
        return 0;
    }

    try {
        console.log(`Fetching initial coins for userId: ${userId} with token ${token}`);
        const response = await fetch(`${userManagementServer}/getCoins?userId=${userId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`, // Ensure 'Bearer' prefix is included
            },
        });
        console.log(`Response: ${response.status}`);
        if (!response.ok) {
            console.error(`Failed to fetch coins for userId: ${userId}, Status: ${response.status}`);
            return 0;
        }

        console.log("Retrieving response...");
        const data = await response.json();
        console.log("Logging data:");
        console.log(data);
        console.log(`Fetched coins: ${data.coins} for userId: ${userId}`);
        return data.coins;
    } catch (error) {
        console.error("Error fetching initial coins:", error);
        return 0;
    }
}

type State = {
    // Modal
    modal: boolean;
    setModal: (isOpen: boolean) => void;

    // Coins
    coins: number;
    fetchCoins: (userId: string) => void;
    setCoins: (userId: string, newCoinTotal: number) => void;

    // Fruits (results)
    fruit0: Fruit | "";
    setFruit0: (fr: Fruit | "") => void;
    fruit1: Fruit | "";
    setFruit1: (fr: Fruit | "") => void;
    fruit2: Fruit | "";
    setFruit2: (fr: Fruit | "") => void;

    // Games
    spins: number;
    addSpin: () => void;

    // Time
    startTime: number;
    endTime: number;

    // Phase
    phase: "idle" | "spinning";
    start: () => void;
    end: () => void;

    // First time
    firstTime: boolean;
    setFirstTime: (isFirstTime: boolean) => void;

    // Username
    username: string;
};

// Create the store with Zustand
const useGame = create<State>()(
    subscribeWithSelector(set => {
        return ({
            // Modal
            modal: false,
            setModal: (isOpen: boolean) => {
                set({modal: isOpen});
            },

            // Coins
            coins: 0, // Default to 0 until fetched
            fetchCoins: (userId: string) => {
                console.log(`Triggering fetchCoins for userId: ${userId}`);
                fetchInitialCoins(userId).then((initialCoins) => {
                    console.log(`Setting coins in state for userId: ${userId} with coins: ${initialCoins}`);
                    set({coins: initialCoins});
                });
            },
            setCoins: (newCoinTotal: number) => {
                console.log(`Setting coins to amount: ${newCoinTotal}`);
                set({coins: newCoinTotal});
            },

            // Fruits (results)
            fruit0: "",
            setFruit0: (fr: Fruit | "") => {
                set({fruit0: fr});
            },
            fruit1: "",
            setFruit1: (fr: Fruit | "") => {
                set({fruit1: fr});
            },
            fruit2: "",
            setFruit2: (fr: Fruit | "") => {
                set({fruit2: fr});
            },

            // Games
            spins: 0,
            addSpin: () => {
                set((state) => ({spins: state.spins + 1}));
            },

            // Time
            startTime: 0,
            endTime: 0,

            // Phase
            phase: "idle",
            start: () => {
                set((state) => {
                    if (state.phase === "idle") {
                        return {phase: "spinning", startTime: Date.now()};
                    }
                    return {};
                });
            },
            end: () => {
                set((state) => {
                    if (state.phase === "spinning") {
                        const endTime = Date.now();
                        const elapsedTime = endTime - state.startTime;
                        devLog(`Time spinning: ${elapsedTime / 1000} seconds`);
                        return {phase: "idle", endTime};
                    }
                    return {};
                });
            },

            // First time
            firstTime: true,
            setFirstTime: (isFirstTime: boolean) => {
                set({firstTime: isFirstTime});
            },

            // Username
            username: "defaultUser", // This can be updated dynamically based on the user
        });
    })
);

export default useGame;
