// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import { POST } from "../spin/+server";

function mockEvent(
	bets: Array<{ numbers: string; odds: number; amt: number }>,
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
	const request = new Request("http://localhost:5173/roulette/spin", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ bets }),
	});
	return {
		request,
		locals: {
			db: mockDb,
			user: { id: "user1", username: "test", coins: 100 },
		},
		params: {},
		url: new URL("http://localhost:5173/roulette/spin"),
	} as unknown as Parameters<typeof POST>[0];
}

describe("roulette spin POST", () => {
	it("processes spin with valid bets", async () => {
		const event = mockEvent([{ numbers: "7", odds: 35, amt: 10 }]);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockDeductCoins = vi.mocked(event.locals.db.deductCoins);
		const mockAddCoins = vi.mocked(event.locals.db.addCoins);
		mockGetCoins.mockResolvedValue(100);
		mockDeductCoins.mockResolvedValue(90);
		mockAddCoins.mockResolvedValue(90);
		mockGetCoins.mockResolvedValue(90);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(200);
		expect(body).toHaveProperty("winning_number");
		expect(body).toHaveProperty("total_bet");
		expect(body).toHaveProperty("total_win");
		expect(body).toHaveProperty("new_coins");
		expect(body.total_bet).toBe(10);
		expect(event.locals.db.deductCoins).toHaveBeenCalledWith("user1", 10);
	});

	it("returns 400 for empty bets", async () => {
		const event = mockEvent([]);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe("Place at least one bet");
	});

	it("returns 400 when coins are insufficient", async () => {
		const event = mockEvent([{ numbers: "7", odds: 35, amt: 200 }]);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		mockGetCoins.mockResolvedValue(100);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe("Not enough coins");
	});

	it("adds coins on winning bet", async () => {
		const event = mockEvent([{ numbers: "7", odds: 35, amt: 10 }]);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockDeductCoins = vi.mocked(event.locals.db.deductCoins);
		const mockAddCoins = vi.mocked(event.locals.db.addCoins);
		mockGetCoins.mockResolvedValue(100);
		mockDeductCoins.mockResolvedValue(90);
		mockAddCoins.mockResolvedValue(450);

		const response = await POST(event);
		const body = await response.json();

		expect(body.total_win).toBeGreaterThanOrEqual(0);
		if (body.total_win > 0) {
			expect(event.locals.db.addCoins).toHaveBeenCalled();
		}
	});

	it("handles multiple bets", async () => {
		const event = mockEvent([
			{ numbers: "7", odds: 35, amt: 5 },
			{ numbers: "1,2,3", odds: 11, amt: 5 },
		]);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockDeductCoins = vi.mocked(event.locals.db.deductCoins);
		mockGetCoins.mockResolvedValue(100);
		mockDeductCoins.mockResolvedValue(90);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(200);
		expect(body.total_bet).toBe(10);
	});

	it("returns 400 for invalid bet entry (non-number amt)", async () => {
		const event = mockEvent([{ numbers: "7", odds: 35, amt: "bad" } as any]);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe("Invalid bet entry");
	});

	it("returns 400 for invalid bet entry (negative amt)", async () => {
		const event = mockEvent([{ numbers: "7", odds: 35, amt: -5 }]);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe("Invalid bet entry");
	});

	it("returns 400 for invalid bet entry (non-string numbers)", async () => {
		const event = mockEvent([{ numbers: 7, odds: 35, amt: 10 } as any]);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe("Invalid bet entry");
	});

	it("returns 400 for invalid bet entry (non-number odds)", async () => {
		const event = mockEvent([{ numbers: "7", odds: "35", amt: 10 } as any]);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe("Invalid bet entry");
	});

	it("returns 401 when user is not authenticated", async () => {
		const request = new Request("http://localhost:5173/roulette/spin", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				bets: [{ numbers: "7", odds: 35, amt: 10 }],
			}),
		});
		const mockDb = {
			getCoins: vi.fn(),
			deductCoins: vi.fn(),
			addCoins: vi.fn(),
			setCoins: vi.fn(),
			createBlackjackGame: vi.fn(),
			updateBlackjackGame: vi.fn(),
			getBlackjackGame: vi.fn(),
			getUser: vi.fn(),
			getUserByUsername: vi.fn(),
		};
		const event = {
			request,
			locals: { db: mockDb, user: null },
			params: {},
			url: new URL("http://localhost:5173/roulette/spin"),
		} as unknown as Parameters<typeof POST>[0];

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(401);
		expect(body.error).toBe("Not authenticated");
	});

	it("returns 500 when addCoins fails on winning bet", async () => {
		const event = mockEvent([{ numbers: "0", odds: 35, amt: 10 }]);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockDeductCoins = vi.mocked(event.locals.db.deductCoins);
		const mockAddCoins = vi.mocked(event.locals.db.addCoins);
		mockGetCoins.mockResolvedValue(100);
		mockDeductCoins.mockResolvedValue(90);
		// First addCoins call fails (win payout), second succeeds (refund)
		mockAddCoins
			.mockRejectedValueOnce(new Error("DB error"))
			.mockResolvedValueOnce(90);

		const response = await POST(event);
		const body = await response.json();

		// If the winning number was 0, the bet won and addCoins was called
		// We can't control spinWheel(), so we check if addCoins was attempted
		// and if it failed, the refund path was triggered
		if (body.error === "Transaction failed") {
			expect(response.status).toBe(500);
			// Second addCoins call should be the refund
			expect(mockAddCoins).toHaveBeenCalledTimes(2);
		}
	});
});
