// Copyright (c) 2023 Michael Kolesidis <michael.kolesidis@gmail.com>
// Licensed under the GNU Affero General Public License v3.0.
// https://www.gnu.org/licenses/gpl-3.0.html

import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import devLog from "../utils/functions/devLog";
import { Fruit } from "../utils/enums";

// Helper function to fetch initial coins
async function fetchInitialCoins(userId: string): Promise<number> {
    try {
        const response = await fetch(`http://localhost:3001/getCoins?userId=${userId}`);
        const data = await response.json();
        return data.coins;
    } catch (error) {
        console.error("Error fetching initial coins:", error);
        return 0;
    }
}

// Helper function to update coins in the database
async function updateCoinsInDatabase(userId: string, coins: number): Promise<void> {
    try {
        await fetch('http://localhost:3001/updateCoins', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ userId, coins }),
        });
    } catch (error) {
        console.error("Error updating coins in database:", error);
    }
}

type State = {
    // Modal
    modal: boolean;
    setModal: (isOpen: boolean) => void;

    // Coins
    coins: number;
    updateCoins: (amount: number) => void;

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

const userId = "jonandrop";

const useGame = create<State>()(
    subscribeWithSelector((set) => {
        // Fetch initial coins when the store is created
        fetchInitialCoins(userId).then((initialCoins) => {
            set({ coins: initialCoins });
        });

        return {
            /**
             *  Modal
             *  (is the help modal open)
             */
            modal: false,
            setModal: (isOpen: boolean) => {
                set(() => {
                    return {
                        modal: isOpen,
                    };
                });
            },

            /**
             * Coins
             *
             */
            coins: 0, // Default to 0 until fetched
            updateCoins: (amount: number) => {
                set((state) => {
                    const newCoins = state.coins + amount;
                    updateCoinsInDatabase(userId, newCoins);
                    return {
                        coins: newCoins,
                    };
                });
            },

            /**
             * Fruits
             *
             */
            fruit0: "",
            setFruit0: (fr: Fruit | "") => {
                set(() => {
                    return {
                        fruit0: fr,
                    };
                });
            },
            fruit1: "",
            setFruit1: (fr: Fruit | "") => {
                set(() => {
                    return {
                        fruit1: fr,
                    };
                });
            },
            fruit2: "",
            setFruit2: (fr: Fruit | "") => {
                set(() => {
                    return {
                        fruit2: fr,
                    };
                });
            },

            /**
             * Games
             *
             */
            spins: 0,
            addSpin: () => {
                set((state) => {
                    return {
                        spins: state.spins + 1,
                    };
                });
            },

            /**
             * Time
             */
            startTime: 0,
            endTime: 0,

            /**
             * Phases
             * The phase of the game
             */
            phase: "idle",
            start: () => {
                set((state) => {
                    if (state.phase === "idle") {
                        return { phase: "spinning", startTime: Date.now() };
                    }
                    return {};
                });
            },
            end: () => {
                set((state) => {
                    if (state.phase === "spinning") {
                        const endTime = Date.now();
                        const startTime = state.startTime;
                        const elapsedTime = endTime - startTime;
                        devLog(`Time spinning: ${elapsedTime / 1000} seconds`);
                        return { phase: "idle", endTime: endTime };
                    }
                    return {};
                });
            },

            /**
             * Other
             *
             */
            firstTime: true,
            setFirstTime: (isFirstTime: boolean) => {
                set(() => {
                    return {
                        firstTime: isFirstTime,
                    };
                });
            },

            /**
             * Username
             */
            username: userId,
        };
    })
);

export default useGame;
