import { describe, it, expect, vi, beforeEach } from 'vitest';
import { signup, login } from '../auth';
import PocketBase from 'pocketbase';

vi.mock('pocketbase', () => ({ default: vi.fn() }));

function setup() {
	const mockCreate = vi.fn();
	const mockAuthWithPassword = vi.fn();

	const mockPb = {
		collection: vi.fn().mockReturnValue({ create: mockCreate, authWithPassword: mockAuthWithPassword })
	};

	vi.mocked(PocketBase).mockReturnValue(mockPb as any);

	return { mockPb, mockCreate, mockAuthWithPassword };
}

const fakeRecord = { id: 'u1', username: 'alice', coins: 100 };

describe('auth', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('signup', () => {
		it('creates user, authenticates, returns User', async () => {
			const { mockPb, mockCreate, mockAuthWithPassword } = setup();
			mockCreate.mockResolvedValue(fakeRecord);
			mockAuthWithPassword.mockResolvedValue(undefined);

			const user = await signup(mockPb as any, 'alice', 'alice@test.com', 'pass123');

			expect(user).toEqual({ id: 'u1', username: 'alice', coins: 100 });
			expect(mockCreate).toHaveBeenCalledWith({
				username: 'alice',
				email: 'alice@test.com',
				password: 'pass123',
				passwordConfirm: 'pass123',
				coins: 100
			});
			expect(mockAuthWithPassword).toHaveBeenCalledWith('alice@test.com', 'pass123');
		});

		it('throws on create failure', async () => {
			const { mockPb, mockCreate } = setup();
			mockCreate.mockRejectedValue(new Error('email taken'));

			await expect(signup(mockPb as any, 'bob', 'bob@test.com', 'pw')).rejects.toThrow('email taken');
		});

		it('throws on auth failure after create', async () => {
			const { mockPb, mockCreate, mockAuthWithPassword } = setup();
			mockCreate.mockResolvedValue(fakeRecord);
			mockAuthWithPassword.mockRejectedValue(new Error('auth fail'));

			await expect(signup(mockPb as any, 'alice', 'alice@test.com', 'pass')).rejects.toThrow('auth fail');
		});
	});

	describe('login', () => {
		it('authenticates and returns User', async () => {
			const { mockPb, mockAuthWithPassword } = setup();
			mockAuthWithPassword.mockResolvedValue({ record: fakeRecord });

			const user = await login(mockPb as any, 'alice@test.com', 'pass123');

			expect(user).toEqual({ id: 'u1', username: 'alice', coins: 100 });
			expect(mockAuthWithPassword).toHaveBeenCalledWith('alice@test.com', 'pass123');
		});

		it('throws on invalid credentials', async () => {
			const { mockPb, mockAuthWithPassword } = setup();
			mockAuthWithPassword.mockRejectedValue(new Error('Invalid credentials'));

			await expect(login(mockPb as any, 'bad@test.com', 'wrong')).rejects.toThrow('Invalid credentials');
		});
	});
});
