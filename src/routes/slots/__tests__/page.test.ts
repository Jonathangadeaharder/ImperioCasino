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
		url: new URL('http://localhost:5173/slots')
	} as Parameters<typeof load>[0];
}

describe('slots +page.server', () => {
	it('returns coins from DB', async () => {
		const event = mockEvent();
		event.locals.db.getCoins.mockResolvedValue(300);

		const result = await load(event);

		expect(result).toEqual({ coins: 300 });
		expect(event.locals.db.getCoins).toHaveBeenCalledWith('user1');
	});

	it('throws when user is not authenticated', async () => {
		const event = mockEvent();
		event.locals.user = null;

		await expect(load(event as Parameters<typeof load>[0])).rejects.toThrow();
	});
});
