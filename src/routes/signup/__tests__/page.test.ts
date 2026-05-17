// @vitest-environment node
import { describe, it, expect, vi } from 'vitest';
import { load, actions } from '../+page.server';

function mockEvent(overrides?: Record<string, unknown>) {
	return {
		locals: {
			pb: {
				collection: vi.fn().mockReturnValue({
					create: vi.fn().mockResolvedValue({ id: 'user1', username: 'test', coins: 100 }),
					authWithPassword: vi.fn().mockResolvedValue({})
				}),
				authStore: { isValid: false, clear: vi.fn(), loadFromCookie: vi.fn(), model: null }
			},
			db: {},
			user: null
		},
		params: {},
		url: new URL('http://localhost:5173/signup'),
		...(overrides ?? {})
	} as any;
}

describe('signup +page.server', () => {
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
		it('creates user and redirects with valid data', async () => {
			const formData = new FormData();
			formData.append('username', 'testuser');
			formData.append('email', 'test@example.com');
			formData.append('password', 'secret123');
			const request = new Request('http://localhost:5173/signup', {
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

		it('returns 400 when username is missing', async () => {
			const formData = new FormData();
			formData.append('email', 'test@example.com');
			formData.append('password', 'secret123');
			const request = new Request('http://localhost:5173/signup', {
				method: 'POST',
				body: formData
			});
			const event = mockEvent({ request });

			const result = await actions.default(event) as { status: number; data: Record<string, unknown> };
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe('All fields required');
		});

		it('returns 400 when email is missing', async () => {
			const formData = new FormData();
			formData.append('username', 'testuser');
			formData.append('password', 'secret123');
			const request = new Request('http://localhost:5173/signup', {
				method: 'POST',
				body: formData
			});
			const event = mockEvent({ request });

			const result = await actions.default(event) as { status: number; data: Record<string, unknown> };
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe('All fields required');
		});

		it('returns 400 when password is missing', async () => {
			const formData = new FormData();
			formData.append('username', 'testuser');
			formData.append('email', 'test@example.com');
			const request = new Request('http://localhost:5173/signup', {
				method: 'POST',
				body: formData
			});
			const event = mockEvent({ request });

			const result = await actions.default(event) as { status: number; data: Record<string, unknown> };
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe('All fields required');
		});

		it('returns 400 on registration error', async () => {
			const formData = new FormData();
			formData.append('username', 'testuser');
			formData.append('email', 'test@example.com');
			formData.append('password', 'secret123');
			const request = new Request('http://localhost:5173/signup', {
				method: 'POST',
				body: formData
			});
			const event = mockEvent({ request });
			event.locals.pb.collection.mockReturnValue({
				create: vi.fn().mockRejectedValue(new Error('Username already taken')),
				authWithPassword: vi.fn()
			});

			const result = await actions.default(event) as { status: number; data: Record<string, unknown> };
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe('Username already taken');
		});

		it('returns generic error for non-Error exceptions', async () => {
			const formData = new FormData();
			formData.append('username', 'testuser');
			formData.append('email', 'test@example.com');
			formData.append('password', 'secret123');
			const request = new Request('http://localhost:5173/signup', {
				method: 'POST',
				body: formData
			});
			const event = mockEvent({ request });
			event.locals.pb.collection.mockReturnValue({
				create: vi.fn().mockRejectedValue('string error'),
				authWithPassword: vi.fn()
			});

			const result = await actions.default(event) as { status: number; data: Record<string, unknown> };
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe('Registration failed');
		});
	});
});
