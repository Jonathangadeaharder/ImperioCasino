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

	it("returns tie (Push) and refunds wager on stand", async () => {
		// Player 7+10=17, dealer 7+10=17 => dealer stands (>=17), tie
		const state = createMockState({
			player_hand: [makeCard("7", 7), makeCard("K", 10)],
			dealer_hand: [makeCard("7", 7), makeCard("K", 10)],
			deck: [makeCard("2", 2), makeCard("2", 2)],
			dealer_value: 17,
		});
		const event = mockEvent("stand", "game1");
		vi.mocked(event.locals.db.getBlackjackGame).mockResolvedValue(state);
		vi.mocked(event.locals.db.getCoins).mockResolvedValue(100);
		vi.mocked(event.locals.db.updateBlackjackGame).mockResolvedValue(undefined);
		const mockAddCoins = vi.mocked(event.locals.db.addCoins);
		mockAddCoins.mockResolvedValue(100);

		const response = await POST(event);
		const body = await response.json();

		expect(body.message).toBe("Push!");
		expect(mockAddCoins).toHaveBeenCalledWith("user1", 10);
	});

	it("returns 'Dealer wins' on stand when dealer has higher hand", async () => {
		const state = createMockState({
			player_hand: [makeCard("8", 8), makeCard("5", 5)],
			dealer_hand: [makeCard("K", 10), makeCard("7", 7)],
			deck: [makeCard("2", 2), makeCard("2", 2)],
		});
		const event = mockEvent("stand", "game1");
		vi.mocked(event.locals.db.getBlackjackGame).mockResolvedValue(state);
		vi.mocked(event.locals.db.getCoins).mockResolvedValue(90);
		vi.mocked(event.locals.db.updateBlackjackGame).mockResolvedValue(undefined);

		const response = await POST(event);
		const body = await response.json();

		expect(body.message).toBe("Dealer wins.");
	});

	it("handles tie (Push) on double down and refunds wager", async () => {
		// Player 7+10=17, hits 2 => 19; Dealer 9+10=19 => stands, tie at 19
		const state = createMockState({
			player_hand: [makeCard("7", 7), makeCard("K", 10)],
			dealer_hand: [makeCard("9", 9), makeCard("K", 10)],
			deck: [makeCard("2", 2), makeCard("2", 2), makeCard("2", 2)],
			current_wager: 10,
			player_coins: 80,
		});
		const event = mockEvent("double", "game1");
		vi.mocked(event.locals.db.getBlackjackGame).mockResolvedValue(state);
		vi.mocked(event.locals.db.getCoins).mockResolvedValue(80);
		vi.mocked(event.locals.db.deductCoins).mockResolvedValue(70);
		vi.mocked(event.locals.db.updateBlackjackGame).mockResolvedValue(undefined);
		const mockAddCoins = vi.mocked(event.locals.db.addCoins);
		mockAddCoins.mockResolvedValue(90);

		const response = await POST(event);
		const body = await response.json();

		expect(body.message).toBe("Push!");
		expect(body.current_wager).toBe(20);
		expect(mockAddCoins).toHaveBeenCalledWith("user1", 20);
	});

	it("returns 400 for invalid action", async () => {
		const event = mockEvent("fold", "game1");

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe("Invalid action");
	});

	it("returns 400 when game_id is missing", async () => {
		const request = new Request("http://localhost:5173/blackjack/action", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ action: "hit" }),
		});
		const event = {
			request,
			locals: {
				db: {
					getCoins: vi.fn(),
					deductCoins: vi.fn(),
					addCoins: vi.fn(),
					setCoins: vi.fn(),
					createBlackjackGame: vi.fn(),
					updateBlackjackGame: vi.fn(),
					getBlackjackGame: vi.fn(),
					getUser: vi.fn(),
					getUserByUsername: vi.fn(),
				},
				user: { id: "user1", username: "test", coins: 100 },
			},
			params: {},
			url: new URL("http://localhost:5173/blackjack/action"),
		} as unknown as Parameters<typeof POST>[0];

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe("Missing game_id");
	});

	it("returns 401 when user is not authenticated", async () => {
		const event = mockEvent("hit", "game1", { user: null });

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(401);
		expect(body.error).toBe("Not authenticated");
	});

	it("returns 404 when game not found", async () => {
		const event = mockEvent("hit", "game1");
		vi.mocked(event.locals.db.getBlackjackGame).mockResolvedValue(null as any);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(404);
		expect(body.error).toBe("Game not found");
	});

	it("returns 403 when game belongs to another user", async () => {
		const state = createMockState({ user_id: "other_user" });
		const event = mockEvent("hit", "game1");
		vi.mocked(event.locals.db.getBlackjackGame).mockResolvedValue(state);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(403);
		expect(body.error).toBe("Forbidden");
	});
});
