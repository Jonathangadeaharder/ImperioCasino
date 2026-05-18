// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import { POST } from "../spin/+server";

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
	const request = new Request("http://localhost:5173/slots/spin", {
		method: "POST",
	});
	return {
		request,
		locals: {
			db: mockDb,
			user: { id: "user1", username: "test", coins: 100 },
		},
		params: {},
		url: new URL("http://localhost:5173/slots/spin"),
	} as unknown as Parameters<typeof POST>[0];
}

describe("slots spin POST", () => {
	it("processes spin with sufficient coins", async () => {
		const event = mockEvent();
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockDeductCoins = vi.mocked(event.locals.db.deductCoins);
		mockGetCoins.mockResolvedValue(100);
		mockDeductCoins.mockResolvedValue(99);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(200);
		expect(body.stop_segments).toHaveLength(3);
		expect(body.fruits).toHaveLength(3);
		expect(body).toHaveProperty("payout");
		expect(body).toHaveProperty("total_coins");
		expect(event.locals.db.deductCoins).toHaveBeenCalledWith("user1", 1);
	});

	it("returns 400 when coins are insufficient", async () => {
		const event = mockEvent();
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		mockGetCoins.mockResolvedValue(0);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe("Not enough coins");
	});

	it("adds coins on winning payout", async () => {
		const event = mockEvent();
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockDeductCoins = vi.mocked(event.locals.db.deductCoins);
		mockGetCoins.mockResolvedValue(100);
		mockDeductCoins.mockResolvedValue(99);

		const response = await POST(event);
		const body = await response.json();

		if (body.payout > 0) {
			expect(event.locals.db.addCoins).toHaveBeenCalled();
		}
	});

	it("returns correct payout structure", async () => {
		const event = mockEvent();
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockDeductCoins = vi.mocked(event.locals.db.deductCoins);
		mockGetCoins.mockResolvedValue(100);
		mockDeductCoins.mockResolvedValue(99);

		const response = await POST(event);
		const body = await response.json();

		expect(body.payout).toBeGreaterThanOrEqual(0);
		expect(body.total_coins).toBeGreaterThanOrEqual(0);
	});
});
