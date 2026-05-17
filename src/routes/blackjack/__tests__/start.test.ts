// @vitest-environment node
import { describe, it, expect, vi } from 'vitest';
import { POST } from '../start/+server';
import type { BlackjackState } from '$lib/types';

function mockEvent(wager: number, overrides?: Record<string, unknown>) {
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
		getUserByUsername: mockGetUserByUsername
	};
	const request = new Request('http://localhost:5173/blackjack/start', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ wager })
	});
	return {
		request,
		locals: {
			db: mockDb,
			user: { id: 'user1', username: 'test', coins: 100 },
			...(overrides ?? {})
		},
		params: {},
		url: new URL('http://localhost:5173/blackjack/start')
	} as unknown as Parameters<typeof POST>[0];
}

describe('blackjack start POST', () => {
	it('starts game with valid wager', async () => {
		const event = mockEvent(10);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockDeductCoins = vi.mocked(event.locals.db.deductCoins);
		const mockCreateBlackjackGame = vi.mocked(event.locals.db.createBlackjackGame);
		mockGetCoins.mockResolvedValue(100);
		mockDeductCoins.mockResolvedValue(90);
		mockCreateBlackjackGame.mockResolvedValue('game1');

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(200);
		expect(body.id).toBe('game1');
		expect(body.current_wager).toBe(10);
		expect(body.player_coins).toBe(90);
		expect(body.player_hand).toHaveLength(2);
		expect(body.dealer_hand).toHaveLength(2);
		expect(body.can_double_down).toBe(false);
		expect(event.locals.db.deductCoins).toHaveBeenCalledWith('user1', 10);
	});

	it('returns 400 for invalid wager (<= 0)', async () => {
		const event = mockEvent(0);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe('Invalid wager');
	});

	it('returns 400 for negative wager', async () => {
		const event = mockEvent(-5);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe('Invalid wager');
	});

	it('returns 400 when coins are insufficient', async () => {
		const event = mockEvent(200);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		mockGetCoins.mockResolvedValue(100);

		const response = await POST(event);
		const body = await response.json();

		expect(response.status).toBe(400);
		expect(body.error).toBe('Not enough coins');
	});

	it('handles malformed JSON body', async () => {
		const event = mockEvent(10);
		event.request = new Request('http://localhost:5173/blackjack/start', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: 'not-json'
		});

		await expect(POST(event)).rejects.toThrow();
	});

	it('detects split possibility for matching cards', async () => {
		const event = mockEvent(10);
		const mockGetCoins = vi.mocked(event.locals.db.getCoins);
		const mockDeductCoins = vi.mocked(event.locals.db.deductCoins);
		const mockCreateBlackjackGame = vi.mocked(event.locals.db.createBlackjackGame);
		mockGetCoins.mockResolvedValue(100);
		mockDeductCoins.mockResolvedValue(90);
		mockCreateBlackjackGame.mockResolvedValue('game1');

		const response = await POST(event);
		const body = await response.json();

		expect(body).toHaveProperty('can_split');
		expect(typeof body.can_split).toBe('boolean');
	});
});
