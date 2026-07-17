// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from "vitest";

// Shared mutable store the hoisted db mock reads from. Tests set
// `.rows` before calling an adapter method that drives a query.
const store = vi.hoisted(() => ({ rows: [] as unknown[] }));

function chainable() {
	const self: Record<string, ReturnType<typeof vi.fn>> = {};
	for (const m of [
		"from",
		"where",
		"set",
		"values",
		"onConflictDoNothing",
		"onConflictDoUpdate",
	]) {
		self[m] = vi.fn(() => self);
	}
	// limit/returning are terminal: return a Promise resolving to store.rows.
	self.limit = vi.fn(() => Promise.resolve(store.rows)) as any;
	self.returning = vi.fn(() => Promise.resolve(store.rows)) as any;
	return self;
}

vi.mock("../database", () => {
	const select = chainable();
	const update = chainable();
	const insert = chainable();
	const del = chainable();
	return {
		db: {
			select: vi.fn(() => select),
			update: vi.fn(() => update),
			insert: vi.fn(() => insert),
			delete: vi.fn(() => del),
		},
	};
});

import { DrizzleAdapter } from "../adapter";

function setRows(rows: unknown[]): void {
	store.rows = rows;
}

describe("DrizzleAdapter", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		store.rows = [];
	});

	describe("getUser", () => {
		it("returns mapped User when found", async () => {
			setRows([{ id: "u1", username: "alice", coins: 100 }]);
			const adapter = new DrizzleAdapter();
			expect(await adapter.getUser("u1")).toEqual({
				id: "u1",
				username: "alice",
				coins: 100,
			});
		});

		it("throws when not found", async () => {
			setRows([]);
			const adapter = new DrizzleAdapter();
			await expect(adapter.getUser("missing")).rejects.toThrow(
				"User not found",
			);
		});
	});

	describe("getUserByUsername", () => {
		it("returns null when no match", async () => {
			setRows([]);
			const adapter = new DrizzleAdapter();
			expect(await adapter.getUserByUsername("nobody")).toBeNull();
		});

		it("returns User when found", async () => {
			setRows([{ id: "u2", username: "bob", coins: 200 }]);
			const adapter = new DrizzleAdapter();
			expect(await adapter.getUserByUsername("bob")).toEqual({
				id: "u2",
				username: "bob",
				coins: 200,
			});
		});
	});

	describe("getCoins", () => {
		it("returns the user's coins", async () => {
			setRows([{ coins: 42 }]);
			const adapter = new DrizzleAdapter();
			expect(await adapter.getCoins("u1")).toBe(42);
		});

		it("throws when user missing", async () => {
			setRows([]);
			const adapter = new DrizzleAdapter();
			await expect(adapter.getCoins("missing")).rejects.toThrow(
				"User not found",
			);
		});
	});

	describe("addCoins", () => {
		it("returns new total after increment", async () => {
			setRows([{ coins: 150 }]);
			const adapter = new DrizzleAdapter();
			expect(await adapter.addCoins("u1", 50)).toBe(150);
		});

		it("throws when user missing", async () => {
			setRows([]);
			const adapter = new DrizzleAdapter();
			await expect(adapter.addCoins("missing", 50)).rejects.toThrow(
				"User not found",
			);
		});
	});

	describe("deductCoins", () => {
		it("returns new total after decrement", async () => {
			setRows([{ coins: 50 }]);
			const adapter = new DrizzleAdapter();
			expect(await adapter.deductCoins("u1", 50)).toBe(50);
		});

		it("throws when user missing", async () => {
			setRows([]);
			const adapter = new DrizzleAdapter();
			await expect(adapter.deductCoins("missing", 50)).rejects.toThrow(
				"User not found",
			);
		});
	});

	describe("setCoins", () => {
		it("returns new total after set", async () => {
			setRows([{ coins: 999 }]);
			const adapter = new DrizzleAdapter();
			expect(await adapter.setCoins("u1", 999)).toBe(999);
		});

		it("throws when user missing", async () => {
			setRows([]);
			const adapter = new DrizzleAdapter();
			await expect(adapter.setCoins("missing", 999)).rejects.toThrow(
				"User not found",
			);
		});
	});

	describe("createBlackjackGame", () => {
		it("returns the new game id", async () => {
			setRows([{ id: "game1" }]);
			const adapter = new DrizzleAdapter();
			const state = {
				user_id: "u1",
				deck: [],
				dealer_hand: [],
				player_hand: [],
				player_second_hand: null,
				player_coins: 90,
				current_wager: 10,
				game_over: false,
				message: null,
				player_stood: false,
				double_down: false,
				split: false,
				current_hand: "first" as const,
				dealer_value: 0,
			};
			expect(await adapter.createBlackjackGame("u1", state)).toBe("game1");
		});
	});

	describe("updateBlackjackGame", () => {
		it("resolves without throwing", async () => {
			setRows([]);
			const adapter = new DrizzleAdapter();
			await expect(
				adapter.updateBlackjackGame("game1", { game_over: true, deck: [] }),
			).resolves.toBeUndefined();
		});
	});

	describe("getBlackjackGame", () => {
		it("maps row to BlackjackState when found", async () => {
			setRows([
				{
					id: "game1",
					userId: "u1",
					deck: [{ suit: "Hearts", name: "A", value: 11 }],
					dealerHand: [{ suit: "Spades", name: "K", value: 10 }],
					playerHand: [{ suit: "Diamonds", name: "7", value: 7 }],
					playerSecondHand: null,
					playerCoins: 90,
					currentWager: 10,
					gameOver: false,
					message: null,
					playerStood: false,
					doubleDown: false,
					split: false,
					currentHand: "first",
					dealerValue: 10,
				},
			]);
			const adapter = new DrizzleAdapter();
			const state = await adapter.getBlackjackGame("game1");
			expect(state).not.toBeNull();
			expect(state?.id).toBe("game1");
			expect(state?.user_id).toBe("u1");
			expect(state?.current_hand).toBe("first");
			expect(state?.deck).toEqual([{ suit: "Hearts", name: "A", value: 11 }]);
		});

		it("returns null when not found", async () => {
			setRows([]);
			const adapter = new DrizzleAdapter();
			expect(await adapter.getBlackjackGame("missing")).toBeNull();
		});
	});

	it("exports a singleton drizzleAdapter instance", async () => {
		const mod = await import("../adapter");
		expect(mod.drizzleAdapter).toBeInstanceOf(DrizzleAdapter);
	});
});
