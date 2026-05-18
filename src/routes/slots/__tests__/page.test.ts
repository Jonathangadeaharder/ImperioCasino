// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import { load } from "../+page.server";

function mockEvent() {
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
	return {
		locals: { db: mockDb, user: { id: "user1", username: "test", coins: 100 } },
		params: {},
		url: new URL("http://localhost:5173/slots"),
	} as unknown as Parameters<typeof load>[0];
}

describe("slots +page.server", () => {
	it("returns coins from DB", async () => {
		const event = mockEvent();
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		mockGetCoins.mockResolvedValue(300);

		const result = await load(event);

		expect(result).toEqual({ coins: 300 });
		expect(event.locals.db.getCoins).toHaveBeenCalledWith("user1");
	});

	it("returns 0 coins when user is not authenticated", async () => {
		const event = mockEvent();
		event.locals.user = null;

		const result = await load(event);
		expect(result).toEqual({ coins: 0 });
	});
});
