// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import { PocketBaseAdapter } from "../pocketbase";

function makeMockPb() {
	const mockGetOne = vi.fn();
	const mockGetList = vi.fn();
	const mockCreate = vi.fn();
	const mockUpdate = vi.fn();

	const pb = {
		collection: vi.fn().mockReturnValue({
			getOne: mockGetOne,
			getList: mockGetList,
			create: mockCreate,
			update: mockUpdate,
		}),
	} as any;

	return { pb, mockGetOne, mockGetList, mockCreate, mockUpdate };
}

describe("PocketBaseAdapter", () => {
	describe("getUser", () => {
		it("fetches user by id and returns mapped User", async () => {
			const { pb, mockGetOne } = makeMockPb();
			mockGetOne.mockResolvedValue({ id: "u1", username: "alice", coins: 500 });
			const adapter = new PocketBaseAdapter(pb);

			const user = await adapter.getUser("u1");

			expect(pb.collection).toHaveBeenCalledWith("users");
			expect(mockGetOne).toHaveBeenCalledWith("u1");
			expect(user).toEqual({ id: "u1", username: "alice", coins: 500 });
		});

		it("propagates error when user not found", async () => {
			const { pb, mockGetOne } = makeMockPb();
			mockGetOne.mockRejectedValue(new Error("Not found"));
			const adapter = new PocketBaseAdapter(pb);

			await expect(adapter.getUser("bad-id")).rejects.toThrow("Not found");
		});
	});

	describe("getUserByUsername", () => {
		it("returns null when no matching user", async () => {
			const { pb, mockGetList } = makeMockPb();
			mockGetList.mockResolvedValue({ items: [] });
			const adapter = new PocketBaseAdapter(pb);

			const result = await adapter.getUserByUsername("nobody");

			expect(mockGetList).toHaveBeenCalledWith(1, 1, {
				filter: 'username="nobody"',
			});
			expect(result).toBeNull();
		});

		it("returns User when match found", async () => {
			const { pb, mockGetList } = makeMockPb();
			mockGetList.mockResolvedValue({
				items: [{ id: "u2", username: "bob", coins: 200 }],
			});
			const adapter = new PocketBaseAdapter(pb);

			const result = await adapter.getUserByUsername("bob");

			expect(result).toEqual({ id: "u2", username: "bob", coins: 200 });
		});
	});

	describe("getCoins", () => {
		it("returns coins for a user", async () => {
			const { pb, mockGetOne } = makeMockPb();
			mockGetOne.mockResolvedValue({ id: "u1", coins: 42 });
			const adapter = new PocketBaseAdapter(pb);

			const coins = await adapter.getCoins("u1");

			expect(coins).toBe(42);
		});
	});

	describe("addCoins", () => {
		it("increments coins and returns new total", async () => {
			const { pb, mockUpdate } = makeMockPb();
			mockUpdate.mockResolvedValue({ coins: 150 });
			const adapter = new PocketBaseAdapter(pb);

			const result = await adapter.addCoins("u1", 50);

			expect(mockUpdate).toHaveBeenCalledWith("u1", {
				coins: { increment: 50 },
			});
			expect(result).toBe(150);
		});
	});

	describe("deductCoins", () => {
		it("decrements coins and returns new total", async () => {
			const { pb, mockUpdate } = makeMockPb();
			mockUpdate.mockResolvedValue({ coins: 50 });
			const adapter = new PocketBaseAdapter(pb);

			const result = await adapter.deductCoins("u1", 50);

			expect(mockUpdate).toHaveBeenCalledWith("u1", {
				coins: { decrement: 50 },
			});
			expect(result).toBe(50);
		});
	});

	describe("setCoins", () => {
		it("sets coins to exact amount and returns new total", async () => {
			const { pb, mockUpdate } = makeMockPb();
			mockUpdate.mockResolvedValue({ coins: 999 });
			const adapter = new PocketBaseAdapter(pb);

			const result = await adapter.setCoins("u1", 999);

			expect(mockUpdate).toHaveBeenCalledWith("u1", { coins: 999 });
			expect(result).toBe(999);
		});
	});

	describe("createBlackjackGame", () => {
		it("creates game and returns id, excluding user_id from rest", async () => {
			const { pb, mockCreate } = makeMockPb();
			mockCreate.mockResolvedValue({ id: "game1" });
			const adapter = new PocketBaseAdapter(pb);

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

			const gameId = await adapter.createBlackjackGame("u1", state);

			expect(mockCreate).toHaveBeenCalledWith(
				expect.objectContaining({
					user_id: "u1",
					deck: [],
					dealer_hand: [],
				}),
			);
			expect(gameId).toBe("game1");
		});
	});

	describe("updateBlackjackGame", () => {
		it("updates game by id", async () => {
			const { pb, mockUpdate } = makeMockPb();
			mockUpdate.mockResolvedValue({});
			const adapter = new PocketBaseAdapter(pb);

			await adapter.updateBlackjackGame("game1", { game_over: true });

			expect(pb.collection).toHaveBeenCalledWith("blackjack_games");
			expect(mockUpdate).toHaveBeenCalledWith("game1", { game_over: true });
		});
	});

	describe("getBlackjackGame", () => {
		it("fetches game and maps all fields to BlackjackState", async () => {
			const { pb, mockGetOne } = makeMockPb();
			const record = {
				id: "game1",
				user_id: "u1",
				deck: [{ suit: "Hearts", name: "A", value: 11 }],
				dealer_hand: [{ suit: "Spades", name: "K", value: 10 }],
				player_hand: [{ suit: "Diamonds", name: "7", value: 7 }],
				player_second_hand: null,
				player_coins: 90,
				current_wager: 10,
				game_over: false,
				message: null,
				player_stood: false,
				double_down: false,
				split: false,
				current_hand: "first",
				dealer_value: 10,
			};
			mockGetOne.mockResolvedValue(record);
			const adapter = new PocketBaseAdapter(pb);

			const state = await adapter.getBlackjackGame("game1");

			expect(pb.collection).toHaveBeenCalledWith("blackjack_games");
			expect(mockGetOne).toHaveBeenCalledWith("game1");
			expect(state.id).toBe("game1");
			expect(state.user_id).toBe("u1");
			expect(state.deck).toEqual(record.deck);
			expect(state.dealer_hand).toEqual(record.dealer_hand);
			expect(state.player_hand).toEqual(record.player_hand);
			expect(state.player_second_hand).toBeNull();
			expect(state.player_coins).toBe(90);
			expect(state.current_wager).toBe(10);
			expect(state.game_over).toBe(false);
			expect(state.message).toBeNull();
			expect(state.player_stood).toBe(false);
			expect(state.double_down).toBe(false);
			expect(state.split).toBe(false);
			expect(state.current_hand).toBe("first");
			expect(state.dealer_value).toBe(10);
		});

		it("propagates error when game not found", async () => {
			const { pb, mockGetOne } = makeMockPb();
			mockGetOne.mockRejectedValue(new Error("Not found"));
			const adapter = new PocketBaseAdapter(pb);

			await expect(adapter.getBlackjackGame("bad-id")).rejects.toThrow(
				"Not found",
			);
		});
	});
});
