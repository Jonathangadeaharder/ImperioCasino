// @vitest-environment node
import { describe, it, expect, vi } from 'vitest';
import { load, actions } from '../+page.server';

function mockEvent() {
	return {
		locals: {
			pb: {
				collection: vi.fn(),
				authStore: { isValid: true, clear: vi.fn(), loadFromCookie: vi.fn(), model: { id: 'user1' } }
			},
			db: {},
			user: { id: 'user1', username: 'test', coins: 100 }
		},
		params: {},
		url: new URL('http://localhost:5173/logout')
	} as unknown as Parameters<NonNullable<typeof actions.default>>[0];
}

describe('logout +page.server', () => {
	describe('load', () => {
		it('redirects to /login', async () => {
			await expect(load()).rejects.toMatchObject({
				status: 303,
				location: '/login'
			});
		});
	});

	describe('actions.default', () => {
		it('clears auth store and redirects to /login', async () => {
			const event = mockEvent();

			await expect(actions.default(event)).rejects.toMatchObject({
				status: 303,
				location: '/login'
			});
			expect(event.locals.pb.authStore.clear).toHaveBeenCalled();
		});
	});
});
