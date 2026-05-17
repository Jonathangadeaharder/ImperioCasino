// @vitest-environment node
import { describe, it, expect, vi } from 'vitest';
import { POST } from '../spin/+server';

function mockEvent(bets: Array<{ numbers: string; odds: number; amt: number }>) {
	const mockDb = {
		getCoins: vi.fn(),
		deductCoins: vi.fn(),
		addCoins: vi.fn(),
		setCoins: vi.fn(),
		createBlackjackGame: vi.fn(),
		updateBlackjackGame: vi.fn(),
		getBlackjackGame: vi.fn(),
		getUser: vi.fn(),
		getUserByUsername: vi.fn()
	};
	const request = new Request('http://localhost:5173/roulette/spin', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ bets })
	});
	return {
		request,
		locals: {
			db: mockDb,
			user: { id: 'user1', username: 'test', coins: 100 }
		},
		params: {},
		url: new URL('http://localhost:5173/roulette/spin')
	} as Parameters<typeof POST>[0];
}

describe('roulette spin POST', () => {
	it('processes spin with valid bets', async () => {
		const event = mockEvent([{ numbers: '7', odds: 35, amt: 10 }]);
		event.locals.db.getCoins.mockResolvedValue(100);
		event.locals.db.deductCoins.mockResolvedValue(90);
		event.locals.db.addCoins.mockResolvedValue(90);
		event.locals.db.getCoins.mockResolvedValue(90);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(200);
		expect(body).toHaveProperty('winning_number');
		expect(body).toHaveProperty('total_bet');
		expect(body).toHaveProperty('total_win');
		expect(body).toHaveProperty('new_coins');
		expect(body.total_bet).toBe(10);
		expect(event.locals.db.deductCoins).toHaveBeenCalledWith('user1', 10);
	});

	it('returns 400 for empty bets', async () => {
		const event = mockEvent([]);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe('Place at least one bet');
	});

	it('returns 400 when coins are insufficient', async () => {
		const event = mockEvent([{ numbers: '7', odds: 35, amt: 200 }]);
		event.locals.db.getCoins.mockResolvedValue(100);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe('Not enough coins');
	});

	it('adds coins on winning bet', async () => {
		const event = mockEvent([{ numbers: '7', odds: 35, amt: 10 }]);
		event.locals.db.getCoins.mockResolvedValue(100);
		event.locals.db.deductCoins.mockResolvedValue(90);
		event.locals.db.addCoins.mockResolvedValue(450);

		const response = await POST(event);
		const body = await response.json();

		expect(body.total_win).toBeGreaterThanOrEqual(0);
		if (body.total_win > 0) {
			expect(event.locals.db.addCoins).toHaveBeenCalled();
		}
	});

	it('handles multiple bets', async () => {
		const event = mockEvent([
			{ numbers: '7', odds: 35, amt: 5 },
			{ numbers: '1,2,3', odds: 11, amt: 5 }
		]);
		event.locals.db.getCoins.mockResolvedValue(100);
		event.locals.db.deductCoins.mockResolvedValue(90);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(200);
		expect(body.total_bet).toBe(10);
	});
});
