// @vitest-environment node

import PocketBase from "pocketbase";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { BlackjackState } from "$lib/types";
import { PocketBaseAdapter } from "../pocketbase";

vi.mock("pocketbase", () => ({ default: vi.fn() }));

function setup() {
	const mockGetOne = vi.fn();
	const mockGetList = vi.fn();
	const mockCreate = vi.fn();
	const mockUpdate = vi.fn();

	const mockFilter = vi.fn(
		(_template: string, _params: Record<string, unknown>) =>
			`username = "${_params.username}"`,
	);
	const mockPb = {
		collection: vi.fn().mockReturnValue({
			getOne: mockGetOne,
			getList: mockGetList,
			create: mockCreate,
			update: mockUpdate,
		}),
		filter: mockFilter,
	};

	vi.mocked(PocketBase).mockReturnValue(mockPb as any);
	const adapter = new PocketBaseAdapter(mockPb as any);

	return {
		adapter,
		mockGetOne,
		mockGetList,
		mockCreate,
		mockUpdate,
		mockFilter,
	};
}

const fakeUserRecord = { id: "u1", username: "alice", coins: 500 };

describe("PocketBaseAdapter", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe("getUser", () => {
		it("returns user from record", async () => {
			const { adapter, mockGetOne } = setup();
			mockGetOne.mockResolvedValue(fakeUserRecord);

			const user = await adapter.getUser("u1");

			expect(user).toEqual({ id: "u1", username: "alice", coins: 500 });
			expect(mockGetOne).toHaveBeenCalledWith("u1");
		});

		it("throws when pocketbase rejects", async () => {
			const { adapter, mockGetOne } = setup();
			mockGetOne.mockRejectedValue(new Error("not found"));

			await expect(adapter.getUser("bad")).rejects.toThrow("not found");
		});
	});

	describe("getUserByUsername", () => {
		it("returns user when found", async () => {
			const { adapter, mockGetList, mockFilter } = setup();
			mockGetList.mockResolvedValue({ items: [fakeUserRecord] });

			const user = await adapter.getUserByUsername("alice");

			expect(user).toEqual({ id: "u1", username: "alice", coins: 500 });
			expect(mockFilter).toHaveBeenCalledWith("username = {:username}", {
				username: "alice",
			});
			expect(mockGetList).toHaveBeenCalledWith(1, 1, {
				filter: 'username = "alice"',
			});
		});

		it("returns null when no match", async () => {
			const { adapter, mockGetList } = setup();
			mockGetList.mockResolvedValue({ items: [] });

			const user = await adapter.getUserByUsername("nobody");

			expect(user).toBeNull();
		});

		it("returns null on pocketbase error", async () => {
			const { adapter, mockGetList } = setup();
			mockGetList.mockRejectedValue(new Error("network"));

			const user = await adapter.getUserByUsername("error");

			expect(user).toBeNull();
		});
	});

	describe("getCoins", () => {
		it("returns coin count", async () => {
			const { adapter, mockGetOne } = setup();
			mockGetOne.mockResolvedValue(fakeUserRecord);

			const coins = await adapter.getCoins("u1");

			expect(coins).toBe(500);
			expect(mockGetOne).toHaveBeenCalledWith("u1");
		});

		it("throws on error", async () => {
			const { adapter, mockGetOne } = setup();
			mockGetOne.mockRejectedValue(new Error("fail"));

			await expect(adapter.getCoins("bad")).rejects.toThrow("fail");
		});
	});

	describe("addCoins", () => {
		it("fetches user, adds amount, updates, returns new total", async () => {
			const { adapter, mockGetOne, mockUpdate } = setup();
			mockGetOne.mockResolvedValue({ ...fakeUserRecord, coins: 500 });

			const result = await adapter.addCoins("u1", 100);

			expect(result).toBe(600);
			expect(mockGetOne).toHaveBeenCalledWith("u1");
			expect(mockUpdate).toHaveBeenCalledWith("u1", { coins: 600 });
		});

		it("throws on getOne failure", async () => {
			const { adapter, mockGetOne } = setup();
			mockGetOne.mockRejectedValue(new Error("db down"));

			await expect(adapter.addCoins("u1", 50)).rejects.toThrow("db down");
		});

		it("throws on update failure", async () => {
			const { adapter, mockGetOne, mockUpdate } = setup();
			mockGetOne.mockResolvedValue({ ...fakeUserRecord, coins: 500 });
			mockUpdate.mockRejectedValue(new Error("update fail"));

			await expect(adapter.addCoins("u1", 50)).rejects.toThrow("update fail");
		});
	});

	describe("deductCoins", () => {
		it("deducts amount and returns new total", async () => {
			const { adapter, mockGetOne, mockUpdate } = setup();
			mockGetOne.mockResolvedValue({ ...fakeUserRecord, coins: 200 });

			const result = await adapter.deductCoins("u1", 50);

			expect(result).toBe(150);
			expect(mockUpdate).toHaveBeenCalledWith("u1", { coins: 150 });
		});

		it("floors at 0 when deduction exceeds balance", async () => {
			const { adapter, mockGetOne, mockUpdate } = setup();
			mockGetOne.mockResolvedValue({ ...fakeUserRecord, coins: 10 });

			const result = await adapter.deductCoins("u1", 100);

			expect(result).toBe(0);
			expect(mockUpdate).toHaveBeenCalledWith("u1", { coins: 0 });
		});

		it("throws on failure", async () => {
			const { adapter, mockGetOne } = setup();
			mockGetOne.mockRejectedValue(new Error("fail"));

			await expect(adapter.deductCoins("u1", 50)).rejects.toThrow("fail");
		});
	});

	describe("setCoins", () => {
		it("updates and returns the amount", async () => {
			const { adapter, mockUpdate } = setup();
			mockUpdate.mockResolvedValue({});

			const result = await adapter.setCoins("u1", 999);

			expect(result).toBe(999);
			expect(mockUpdate).toHaveBeenCalledWith("u1", { coins: 999 });
		});

		it("throws on failure", async () => {
			const { adapter, mockUpdate } = setup();
			mockUpdate.mockRejectedValue(new Error("fail"));

			await expect(adapter.setCoins("u1", 0)).rejects.toThrow("fail");
		});
	});

	describe("createBlackjackGame", () => {
		const state: BlackjackState = {
			user_id: "u1",
			deck: [{ suit: "Hearts", name: "Ace", value: 11 }],
			dealer_hand: [{ suit: "Spades", name: "K", value: 10 }],
			player_hand: [{ suit: "Diamonds", name: "Q", value: 10 }],
			player_second_hand: null,
			player_coins: 500,
			current_wager: 50,
			game_over: false,
			message: null,
			player_stood: false,
			double_down: false,
			split: false,
			current_hand: "first",
			dealer_value: 10,
		};

		it("creates a record and returns its id", async () => {
			const { adapter, mockCreate } = setup();
			mockCreate.mockResolvedValue({ id: "bg1" });

			const id = await adapter.createBlackjackGame("u1", state);

			expect(id).toBe("bg1");
			expect(mockCreate).toHaveBeenCalledWith({
				user: "u1",
				deck: JSON.stringify(state.deck),
				dealer_hand: JSON.stringify(state.dealer_hand),
				player_hand: JSON.stringify(state.player_hand),
				player_second_hand: null,
				player_coins: 500,
				current_wager: 50,
				game_over: false,
				message: null,
				player_stood: false,
				double_down: false,
				split: false,
				current_hand: "first",
				dealer_value: 10,
			});
		});

		it("stringifies player_second_hand when present", async () => {
			const { adapter, mockCreate } = setup();
			mockCreate.mockResolvedValue({ id: "bg2" });
			const stateWithSplit: BlackjackState = {
				...state,
				player_second_hand: [{ suit: "Clubs", name: "5", value: 5 }],
				split: true,
			};

			const id = await adapter.createBlackjackGame("u1", stateWithSplit);

			expect(id).toBe("bg2");
			const callArg = mockCreate.mock.calls[0][0];
			expect(callArg.player_second_hand).toBe(
				JSON.stringify(stateWithSplit.player_second_hand),
			);
		});

		it("throws on failure", async () => {
			const { adapter, mockCreate } = setup();
			mockCreate.mockRejectedValue(new Error("fail"));

			await expect(adapter.createBlackjackGame("u1", state)).rejects.toThrow(
				"fail",
			);
		});
	});

	describe("updateBlackjackGame", () => {
		it("updates only provided fields", async () => {
			const { adapter, mockUpdate } = setup();
			mockUpdate.mockResolvedValue({});

			await adapter.updateBlackjackGame("bg1", {
				game_over: true,
				message: "Bust",
			});

			expect(mockUpdate).toHaveBeenCalledWith("bg1", {
				game_over: true,
				message: "Bust",
			});
		});

		it("stringifies hand fields", async () => {
			const { adapter, mockUpdate } = setup();
			mockUpdate.mockResolvedValue({});

			await adapter.updateBlackjackGame("bg1", {
				player_hand: [{ suit: "Hearts", name: "Ace", value: 11 }],
			});

			const callArg = mockUpdate.mock.calls[0][1];
			expect(callArg.player_hand).toBe(
				JSON.stringify([{ suit: "Hearts", name: "Ace", value: 11 }]),
			);
		});

		it("sets player_second_hand to null when provided as null", async () => {
			const { adapter, mockUpdate } = setup();
			mockUpdate.mockResolvedValue({});

			await adapter.updateBlackjackGame("bg1", { player_second_hand: null });

			const callArg = mockUpdate.mock.calls[0][1];
			expect(callArg.player_second_hand).toBeNull();
		});

		it("throws on failure", async () => {
			const { adapter, mockUpdate } = setup();
			mockUpdate.mockRejectedValue(new Error("fail"));

			await expect(
				adapter.updateBlackjackGame("bg1", { game_over: true }),
			).rejects.toThrow("fail");
		});
	});

	describe("getBlackjackGame", () => {
		const record = {
			id: "bg1",
			user: "u1",
			deck: JSON.stringify([{ suit: "Hearts", name: "Ace", value: 11 }]),
			dealer_hand: JSON.stringify([{ suit: "Spades", name: "K", value: 10 }]),
			player_hand: JSON.stringify([{ suit: "Diamonds", name: "Q", value: 10 }]),
			player_second_hand: null,
			player_coins: 500,
			current_wager: 50,
			game_over: false,
			message: null,
			player_stood: false,
			double_down: false,
			split: false,
			current_hand: "first",
			dealer_value: 10,
		};

		it("returns parsed BlackjackState", async () => {
			const { adapter, mockGetOne } = setup();
			mockGetOne.mockResolvedValue(record);

			const state = await adapter.getBlackjackGame("bg1");

			expect(state).toEqual({
				id: "bg1",
				user_id: "u1",
				deck: [{ suit: "Hearts", name: "Ace", value: 11 }],
				dealer_hand: [{ suit: "Spades", name: "K", value: 10 }],
				player_hand: [{ suit: "Diamonds", name: "Q", value: 10 }],
				player_second_hand: null,
				player_coins: 500,
				current_wager: 50,
				game_over: false,
				message: null,
				player_stood: false,
				double_down: false,
				split: false,
				current_hand: "first",
				dealer_value: 10,
			});
			expect(mockGetOne).toHaveBeenCalledWith("bg1", { expand: "user" });
		});

		it("parses player_second_hand when present", async () => {
			const { adapter, mockGetOne } = setup();
			const recordWithSplit = {
				...record,
				player_second_hand: JSON.stringify([
					{ suit: "Clubs", name: "5", value: 5 },
				]),
			};
			mockGetOne.mockResolvedValue(recordWithSplit);

			const state = await adapter.getBlackjackGame("bg1");

			expect(state.player_second_hand).toEqual([
				{ suit: "Clubs", name: "5", value: 5 },
			]);
		});

		it("throws on failure", async () => {
			const { adapter, mockGetOne } = setup();
			mockGetOne.mockRejectedValue(new Error("fail"));

			await expect(adapter.getBlackjackGame("bad")).rejects.toThrow("fail");
		});
	});
});
