// @vitest-environment node
import { describe, it, expect, vi } from 'vitest';
import { load } from '../+page.server';

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
	return {
		locals: { db: mockDb, user: { id: 'user1', username: 'test', coins: 100 } },
		params: {},
		url: new URL('http://localhost:5173/roulette')
	} as Parameters<typeof load>[0];
}

describe('roulette +page.server', () => {
	it('returns coins from DB', async () => {
		const event = mockEvent();
		event.locals.db.getCoins.mockResolvedValue(200);

		const result = await load(event);

		expect(result).toEqual({ coins: 200 });
		expect(event.locals.db.getCoins).toHaveBeenCalledWith('user1');
	});

	it('throws when user is not authenticated', async () => {
		const event = mockEvent();
		event.locals.user = null;

		await expect(load(event as Parameters<typeof load>[0])).rejects.toThrow();
	});
});
