import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import devLog from "../utils/functions/devLog";
import { Fruit } from "../utils/enums";

// Helper function to fetch initial coins
async function fetchInitialCoins(userId: string): Promise<number> {
  try {
    console.log(`Fetching initial coins for userId: ${userId}`);
    const response = await fetch(`http://localhost:3001/getCoins?userId=${userId}`);
    console.log(`Response status: ${response.status}`);

    if (!response.ok) {
      console.error(`Failed to fetch coins for userId: ${userId}, Status: ${response.status}`);
      return 0;
    }

    const data = await response.json();
    console.log(`Fetched coins: ${data.coins} for userId: ${userId}`);
    return data.coins;
  } catch (error) {
    console.error("Error fetching initial coins:", error);
    return 0;
  }
}

// Helper function to update coins in the database
async function updateCoinsInDatabase(userId: string, coins: number): Promise<void> {
  try {
    console.log(`Updating coins for userId: ${userId} with coins: ${coins}`);
    const response = await fetch('http://localhost:3001/updateCoins', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId, coins }),
    });
    console.log(`Update coins response status: ${response.status}`);

    if (!response.ok) {
      console.error(`Failed to update coins for userId: ${userId}, Status: ${response.status}`);
    }
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
  fetchCoins: (userId: string) => void;
  updateCoins: (userId: string, amount: number) => void;

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
  subscribeWithSelector((set) => ({
    modal: false,
    setModal: (isOpen: boolean) => {
      set({ modal: isOpen });
    },
    coins: 0, // Default to 0 until fetched
    fetchCoins: (userId: string) => {
      console.log(`Triggering fetchCoins for userId: ${userId}`);
      fetchInitialCoins(userId).then((initialCoins) => {
        console.log(`Setting coins in state for userId: ${userId} with coins: ${initialCoins}`);
        set({ coins: initialCoins });
      });
    },
    updateCoins: (userId: string, amount: number) => {
      console.log(`Triggering updateCoins for userId: ${userId} with amount: ${amount}`);
      set((state) => {
        const newCoins = state.coins + amount;
        updateCoinsInDatabase(userId, newCoins);
        console.log(`Updated coins in state for userId: ${userId} to newCoins: ${newCoins}`);
        return { coins: newCoins };
      });
    },
    fruit0: "",
    setFruit0: (fr: Fruit | "") => {
      set({ fruit0: fr });
    },
    fruit1: "",
    setFruit1: (fr: Fruit | "") => {
      set({ fruit1: fr });
    },
    fruit2: "",
    setFruit2: (fr: Fruit | "") => {
      set({ fruit2: fr });
    },
    spins: 0,
    addSpin: () => {
      set((state) => ({ spins: state.spins + 1 }));
    },
    startTime: 0,
    endTime: 0,
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
          const elapsedTime = endTime - state.startTime;
          devLog(`Time spinning: ${elapsedTime / 1000} seconds`);
          return { phase: "idle", endTime };
        }
        return {};
      });
    },
    firstTime: true,
    setFirstTime: (isFirstTime: boolean) => {
      set({ firstTime: isFirstTime });
    },
    username: "defaultUser", // This can be updated dynamically based on the user
  }))
);

export default useGame;
