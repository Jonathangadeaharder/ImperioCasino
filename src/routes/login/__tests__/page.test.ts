// @vitest-environment node
import { describe, it, expect, vi } from 'vitest';
import { load, actions } from '../+page.server';

function mockEvent(overrides?: Record<string, unknown>) {
	return {
		locals: {
			pb: {
				collection: vi.fn().mockReturnValue({
					authWithPassword: vi.fn().mockResolvedValue({})
				}),
				authStore: { isValid: false, clear: vi.fn(), loadFromCookie: vi.fn(), model: null }
			},
			db: {},
			user: null
		},
		params: {},
		url: new URL('http://localhost:5173/login'),
		...(overrides ?? {})
	} as any;
}

describe('login +page.server', () => {
	describe('load', () => {
		it('returns empty object when not logged in', async () => {
			const event = mockEvent();
			const result = await load(event);
			expect(result).toEqual({});
		});

		it('redirects to / when user is already logged in', async () => {
			const event = mockEvent();
			event.locals.user = { id: 'user1', username: 'test', coins: 100 };
			await expect(load(event)).rejects.toMatchObject({
				status: 303,
				location: '/'
			});
		});
	});

	describe('actions.default', () => {
		it('authenticates with valid credentials and redirects', async () => {
			const formData = new FormData();
			formData.append('email', 'test@example.com');
			formData.append('password', 'secret123');
			const request = new Request('http://localhost:5173/login', {
				method: 'POST',
				body: formData
			});
			const event = mockEvent({ request });

			await expect(actions.default(event)).rejects.toMatchObject({
				status: 303,
				location: '/'
			});
			expect(event.locals.pb.collection).toHaveBeenCalledWith('users');
		});

		it('returns 400 when email is missing', async () => {
			const formData = new FormData();
			formData.append('password', 'secret123');
			const request = new Request('http://localhost:5173/login', {
				method: 'POST',
				body: formData
			});
			const event = mockEvent({ request });

			const result = await actions.default(event) as { status: number; data: Record<string, unknown> };
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe('Email and password required');
		});

		it('returns 400 when password is missing', async () => {
			const formData = new FormData();
			formData.append('email', 'test@example.com');
			const request = new Request('http://localhost:5173/login', {
				method: 'POST',
				body: formData
			});
			const event = mockEvent({ request });

			const result = await actions.default(event) as { status: number; data: Record<string, unknown> };
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe('Email and password required');
		});

		it('returns 401 on invalid credentials', async () => {
			const formData = new FormData();
			formData.append('email', 'test@example.com');
			formData.append('password', 'wrong');
			const request = new Request('http://localhost:5173/login', {
				method: 'POST',
				body: formData
			});
			const event = mockEvent({ request });
			event.locals.pb.collection.mockReturnValue({
				authWithPassword: vi.fn().mockRejectedValue(new Error('Invalid credentials'))
			});

			const result = await actions.default(event) as { status: number; data: Record<string, unknown> };
			expect(result.status).toBe(401);
			expect(result.data?.error).toBe('Invalid credentials');
		});
	});
});
