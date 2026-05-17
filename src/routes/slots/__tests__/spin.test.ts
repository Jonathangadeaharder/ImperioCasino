// @vitest-environment node
import { describe, it, expect, vi } from 'vitest';
import { POST } from '../spin/+server';

function mockEvent() {
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
	const request = new Request('http://localhost:5173/slots/spin', { method: 'POST' });
	return {
		request,
		locals: {
			db: mockDb,
			user: { id: 'user1', username: 'test', coins: 100 }
		},
		params: {},
		url: new URL('http://localhost:5173/slots/spin')
	} as Parameters<typeof POST>[0];
}

describe('slots spin POST', () => {
	it('processes spin with sufficient coins', async () => {
		const event = mockEvent();
		event.locals.db.getCoins.mockResolvedValue(100);
		event.locals.db.deductCoins.mockResolvedValue(99);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(200);
		expect(body.stop_segments).toHaveLength(3);
		expect(body.fruits).toHaveLength(3);
		expect(body).toHaveProperty('payout');
		expect(body).toHaveProperty('total_coins');
		expect(event.locals.db.deductCoins).toHaveBeenCalledWith('user1', 1);
	});

	it('returns 400 when coins are insufficient', async () => {
		const event = mockEvent();
		event.locals.db.getCoins.mockResolvedValue(0);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe('Not enough coins');
	});

	it('adds coins on winning payout', async () => {
		const event = mockEvent();
		event.locals.db.getCoins.mockResolvedValue(100);
		event.locals.db.deductCoins.mockResolvedValue(99);

		const response = await POST(event);
		const body = await response.json();

		if (body.payout > 0) {
			expect(event.locals.db.addCoins).toHaveBeenCalled();
		}
	});

	it('returns correct payout structure', async () => {
		const event = mockEvent();
		event.locals.db.getCoins.mockResolvedValue(100);
		event.locals.db.deductCoins.mockResolvedValue(99);

		const response = await POST(event);
		const body = await response.json();

		expect(body.payout).toBeGreaterThanOrEqual(0);
		expect(body.total_coins).toBeGreaterThanOrEqual(0);
	});
});
