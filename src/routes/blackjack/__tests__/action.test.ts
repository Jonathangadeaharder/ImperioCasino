// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import type { BlackjackState, Card } from "$lib/types";
import { POST } from "../action/+server";

function makeCard(
	name: string,
	value: number,
	suit: "Hearts" | "Spades" | "Diamonds" | "Clubs" = "Hearts",
): Card {
	return { suit, name, value };
}

function createMockState(overrides?: Partial<BlackjackState>): BlackjackState {
	return {
		id: "game1",
		user_id: "user1",
		deck: [
			makeCard("K", 10),
			makeCard("5", 5),
			makeCard("3", 3),
			makeCard("2", 2),
		],
		dealer_hand: [makeCard("10", 10), makeCard("7", 7)],
		player_hand: [makeCard("10", 10), makeCard("5", 5)],
		player_second_hand: null,
		player_coins: 90,
		current_wager: 10,
		game_over: false,
		message: null,
		player_stood: false,
		double_down: false,
		split: false,
		current_hand: "first",
		dealer_value: 17,
		...overrides,
	};
}

function mockEvent(
	action: string,
	game_id: string,
	overrides?: Record<string, unknown>,
) {
	const mockGetCoins = vi.fn();
	const mockDeductCoins = vi.fn();
	const mockAddCoins = vi.fn();
	const mockSetCoins = vi.fn();
	const mockCreateBlackjackGame = vi.fn();
	const mockUpdateBlackjackGame = vi.fn();
	const mockGetBlackjackGame = vi.fn();
	const mockGetUser = vi.fn();
	const mockGetUserByUsername = vi.fn();
	const mockDb = {
		getCoins: mockGetCoins,
		deductCoins: mockDeductCoins,
		addCoins: mockAddCoins,
		setCoins: mockSetCoins,
		createBlackjackGame: mockCreateBlackjackGame,
		updateBlackjackGame: mockUpdateBlackjackGame,
		getBlackjackGame: mockGetBlackjackGame,
		getUser: mockGetUser,
		getUserByUsername: mockGetUserByUsername,
	};
	const request = new Request("http://localhost:5173/blackjack/action", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ action, game_id }),
	});
	return {
		request,
		locals: {
			db: mockDb,
			user: { id: "user1", username: "test", coins: 100 },
			...(overrides ?? {}),
		},
		params: {},
		url: new URL("http://localhost:5173/blackjack/action"),
	} as unknown as Parameters<typeof POST>[0];
}

describe("blackjack action POST", () => {
	it("processes hit action", async () => {
		const state = createMockState({ deck: [makeCard("3", 3)] });
		const event = mockEvent("hit", "game1");
		const mockGetBlackjackGame = vi.mocked(event.locals.db.getBlackjackGame);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockUpdateBlackjackGame = vi.mocked(
			event.locals.db.updateBlackjackGame,
		);
		mockGetBlackjackGame.mockResolvedValue(state);
		mockGetCoins.mockResolvedValue(90);
		mockUpdateBlackjackGame.mockResolvedValue(undefined);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(200);
		expect(body.player_hand).toHaveLength(3);
		expect(body.game_over).toBe(false);
	});

	it("processes hit and detects bust", async () => {
		const state = createMockState({
			player_hand: [makeCard("K", 10), makeCard("Q", 10)],
			deck: [makeCard("J", 10)],
		});
		const event = mockEvent("hit", "game1");
		const mockGetBlackjackGame = vi.mocked(event.locals.db.getBlackjackGame);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockUpdateBlackjackGame = vi.mocked(
			event.locals.db.updateBlackjackGame,
		);
		mockGetBlackjackGame.mockResolvedValue(state);
		mockGetCoins.mockResolvedValue(90);
		mockUpdateBlackjackGame.mockResolvedValue(undefined);

		const response = await POST(event);
		const body = await response.json();

		expect(body.game_over).toBe(true);
		expect(body.message).toBe("Bust! You lose.");
	});

	it("processes stand action", async () => {
		const state = createMockState({
			deck: [makeCard("3", 3), makeCard("2", 2)],
		});
		const event = mockEvent("stand", "game1");
		const mockGetBlackjackGame = vi.mocked(event.locals.db.getBlackjackGame);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockUpdateBlackjackGame = vi.mocked(
			event.locals.db.updateBlackjackGame,
		);
		const mockAddCoins = vi.mocked(event.locals.db.addCoins);
		mockGetBlackjackGame.mockResolvedValue(state);
		mockGetCoins.mockResolvedValue(100);
		mockUpdateBlackjackGame.mockResolvedValue(undefined);
		mockAddCoins.mockResolvedValue(100);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(200);
		expect(body.player_stood).toBe(true);
		expect(body.game_over).toBe(true);
		expect(body.message).toBeTruthy();
	});

	it("processes double action", async () => {
		const state = createMockState({
			player_coins: 90,
			current_wager: 10,
			deck: [makeCard("4", 4), makeCard("2", 2)],
		});
		const event = mockEvent("double", "game1");
		const mockGetBlackjackGame = vi.mocked(event.locals.db.getBlackjackGame);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockDeductCoins = vi.mocked(event.locals.db.deductCoins);
		const mockUpdateBlackjackGame = vi.mocked(
			event.locals.db.updateBlackjackGame,
		);
		mockGetBlackjackGame.mockResolvedValue(state);
		mockGetCoins.mockResolvedValue(80);
		mockDeductCoins.mockResolvedValue(80);
		mockUpdateBlackjackGame.mockResolvedValue(undefined);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(200);
		expect(body.game_over).toBe(true);
		expect(body.current_wager).toBe(20);
	});

	it("returns 400 when game is already over", async () => {
		const state = createMockState({ game_over: true, message: "You win!" });
		const event = mockEvent("hit", "game1");
		const mockGetBlackjackGame = vi.mocked(event.locals.db.getBlackjackGame);
		mockGetBlackjackGame.mockResolvedValue(state);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe("Game already over");
	});

	it("returns coins updated after action", async () => {
		const state = createMockState({
			deck: [makeCard("2", 2), makeCard("3", 3)],
		});
		const event = mockEvent("stand", "game1");
		const mockGetBlackjackGame = vi.mocked(event.locals.db.getBlackjackGame);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockUpdateBlackjackGame = vi.mocked(
			event.locals.db.updateBlackjackGame,
		);
		mockGetBlackjackGame.mockResolvedValue(state);
		mockGetCoins.mockResolvedValue(110);
		mockUpdateBlackjackGame.mockResolvedValue(undefined);

		const response = await POST(event);
		const body = await response.json();

		expect(body.player_coins).toBe(110);
	});
});
