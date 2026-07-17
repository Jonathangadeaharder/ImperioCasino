// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const rows = vi.hoisted(() => ({ value: [] as unknown[] }));

function chainable() {
	const builder: Record<string, ReturnType<typeof vi.fn>> = {};
	for (const m of [
		"from",
		"where",
		"set",
		"values",
		"onConflictDoNothing",
		"onConflictDoUpdate",
	]) {
		builder[m] = vi.fn(() => builder);
	}
	builder.limit = vi.fn(() => Promise.resolve(rows.value)) as any;
	builder.returning = vi.fn(() => Promise.resolve(rows.value)) as any;
	// Return a real Promise that also exposes the builder methods, so both
	// `await db.insert().values({...})` (terminal) and `.values().returning()`
	// (chained) work without a literal thenable.
	const promise = Promise.resolve(rows.value);
	return Object.assign(promise, builder);
}

vi.mock("./db/database", () => {
	const select = chainable();
	const update = chainable();
	const insert = chainable();
	const del = chainable();
	return {
		db: {
			select: vi.fn(() => select),
			update: vi.fn(() => update),
			insert: vi.fn(() => insert),
			delete: vi.fn(() => del),
		},
	};
});

vi.mock("bcryptjs", () => ({
	hash: vi.fn(async () => "hashed"),
	compare: vi.fn(async () => true),
}));

import { compare, hash } from "bcryptjs";
import { type AuthUser, authService } from "./auth-service";

function setRows(value: unknown[]): void {
	rows.value = value;
}

function mockEvent(cookie = ""): any {
	return {
		request: { headers: { get: vi.fn(() => cookie) } },
		cookies: {
			set: vi.fn(),
			delete: vi.fn(),
		},
	};
}

const now = new Date("2026-01-01T00:00:00Z");

describe("AuthService", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		setRows([]);
		vi.useFakeTimers();
		vi.setSystemTime(now);
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	describe("getSession", () => {
		it("returns null when no cookie", async () => {
			expect(await authService.getSession(mockEvent())).toBeNull();
		});

		it("returns null when session not found", async () => {
			setRows([]);
			expect(
				await authService.getSession(mockEvent("imperio_session=token")),
			).toBeNull();
		});

		it("returns null when session expired", async () => {
			setRows([{ userId: "u1", expiresAt: new Date("2025-01-01") }]);
			expect(
				await authService.getSession(mockEvent("imperio_session=token")),
			).toBeNull();
		});

		it("returns session when valid", async () => {
			const sessionRows = [{ userId: "u1", expiresAt: new Date("2027-01-01") }];
			const userRows = [
				{
					id: "u1",
					username: "alice",
					email: "a@x.com",
					coins: 100,
				},
			];
			const dbMod = await import("./db/database");
			const sessionChain = chainable();
			vi.mocked(
				sessionChain.limit as unknown as ReturnType<typeof vi.fn>,
			).mockReturnValue(Promise.resolve(sessionRows) as any);
			const userChain = chainable();
			vi.mocked(
				userChain.limit as unknown as ReturnType<typeof vi.fn>,
			).mockReturnValue(Promise.resolve(userRows) as any);
			vi.mocked(dbMod.db.select as unknown as ReturnType<typeof vi.fn>)
				.mockReturnValueOnce(sessionChain)
				.mockReturnValueOnce(userChain);
			const session = await authService.getSession(
				mockEvent("imperio_session=token"),
			);
			expect(session).not.toBeNull();
			expect(session?.user.id).toBe("u1");
			expect(session?.user.username).toBe("alice");
			expect(session?.user.coins).toBe(100);
		});
	});

	describe("signUp", () => {
		it("rejects short password", async () => {
			const event = mockEvent();
			const result = await authService.signUp(
				event,
				"alice",
				"a@x.com",
				"short",
			);
			expect(result.user).toBeNull();
			expect(result.error).toContain("8 characters");
		});

		it("rejects over-long password", async () => {
			const event = mockEvent();
			const result = await authService.signUp(
				event,
				"alice",
				"a@x.com",
				"x".repeat(200),
			);
			expect(result.user).toBeNull();
			expect(result.error).toContain("128 characters");
		});

		it("rejects duplicate username or email", async () => {
			setRows([{ id: "existing" }]);
			const event = mockEvent();
			const result = await authService.signUp(
				event,
				"alice",
				"a@x.com",
				"password123",
			);
			expect(result.user).toBeNull();
			expect(result.error).toBe(
				"Could not create your account. Please try again.",
			);
			expect(hash).toHaveBeenCalled();
		});

		it("creates user and sets session cookie", async () => {
			const newUser: AuthUser = {
				id: "u1",
				username: "alice",
				email: "a@x.com",
				coins: 100,
			};
			const dbMod = await import("./db/database");
			const emptySelect = chainable();
			vi.mocked(
				emptySelect.limit as unknown as ReturnType<typeof vi.fn>,
			).mockReturnValue(Promise.resolve([]) as any);
			const insertChain = chainable();
			vi.mocked(
				insertChain.returning as unknown as ReturnType<typeof vi.fn>,
			).mockReturnValue(Promise.resolve([newUser]) as any);
			vi.mocked(dbMod.db.select as unknown as ReturnType<typeof vi.fn>)
				.mockReturnValueOnce(emptySelect) // existing username
				.mockReturnValueOnce(emptySelect); // existing email
			vi.mocked(
				dbMod.db.insert as unknown as ReturnType<typeof vi.fn>,
			).mockReturnValueOnce(insertChain);
			const event = mockEvent();
			const result = await authService.signUp(
				event,
				"alice",
				"a@x.com",
				"password123",
			);
			expect(result.user).not.toBeNull();
			expect(result.user?.id).toBe("u1");
			expect(result.error).toBeNull();
			expect(hash).toHaveBeenCalledWith("password123", 12);
			expect(event.cookies.set).toHaveBeenCalledWith(
				"imperio_session",
				expect.any(String),
				expect.objectContaining({ httpOnly: true, sameSite: "lax", path: "/" }),
			);
		});

		it("returns error when insert returns no row", async () => {
			const dbMod = await import("./db/database");
			const emptySelect = chainable();
			vi.mocked(
				emptySelect.limit as unknown as ReturnType<typeof vi.fn>,
			).mockReturnValue(Promise.resolve([]) as any);
			const insertChain = chainable();
			vi.mocked(
				insertChain.returning as unknown as ReturnType<typeof vi.fn>,
			).mockReturnValue(Promise.resolve([]) as any);
			vi.mocked(dbMod.db.select as unknown as ReturnType<typeof vi.fn>)
				.mockReturnValueOnce(emptySelect)
				.mockReturnValueOnce(emptySelect);
			vi.mocked(
				dbMod.db.insert as unknown as ReturnType<typeof vi.fn>,
			).mockReturnValueOnce(insertChain);
			const result = await authService.signUp(
				mockEvent(),
				"alice",
				"a@x.com",
				"password123",
			);
			expect(result.user).toBeNull();
			expect(result.error).toBe(
				"Could not create your account. Please try again.",
			);
		});
	});

	describe("signIn", () => {
		it("returns error when user not found", async () => {
			setRows([]);
			const result = await authService.signIn(
				mockEvent(),
				"a@x.com",
				"password123",
			);
			expect(result.user).toBeNull();
			expect(result.error).toBe("Invalid email or password.");
			expect(compare).toHaveBeenCalled();
		});

		it("returns error when password invalid", async () => {
			setRows([
				{
					id: "u1",
					username: "alice",
					email: "a@x.com",
					coins: 100,
					passwordHash: "hashed",
				},
			]);
			vi.mocked(
				compare as unknown as ReturnType<typeof vi.fn>,
			).mockResolvedValueOnce(false);
			const result = await authService.signIn(mockEvent(), "a@x.com", "wrong");
			expect(result.user).toBeNull();
			expect(result.error).toBe("Invalid email or password.");
		});

		it("creates session and sets cookie on valid credentials", async () => {
			setRows([
				{
					id: "u1",
					username: "alice",
					email: "a@x.com",
					coins: 100,
					passwordHash: "hashed",
				},
			]);
			vi.mocked(
				compare as unknown as ReturnType<typeof vi.fn>,
			).mockResolvedValueOnce(true);
			const event = mockEvent();
			const result = await authService.signIn(event, "a@x.com", "password123");
			expect(result.user).not.toBeNull();
			expect(result.user?.id).toBe("u1");
			expect(result.error).toBeNull();
			expect(event.cookies.set).toHaveBeenCalledWith(
				"imperio_session",
				expect.any(String),
				expect.objectContaining({ httpOnly: true, path: "/" }),
			);
		});
	});

	describe("signOut", () => {
		it("deletes session and clears cookie when token present", async () => {
			const del = chainable();
			const dbMod = await import("./db/database");
			vi.mocked(
				dbMod.db.delete as unknown as ReturnType<typeof vi.fn>,
			).mockReturnValueOnce(del as any);
			const event = mockEvent("imperio_session=token");
			await authService.signOut(event);
			expect(event.cookies.delete).toHaveBeenCalledWith("imperio_session", {
				path: "/",
			});
		});

		it("clears cookie only when no token", async () => {
			const event = mockEvent();
			await authService.signOut(event);
			expect(event.cookies.delete).toHaveBeenCalledWith("imperio_session", {
				path: "/",
			});
		});
	});

	describe("getUserByEmail", () => {
		it("returns user when found", async () => {
			setRows([{ id: "u1", username: "alice", email: "a@x.com", coins: 100 }]);
			expect(await authService.getUserByEmail("a@x.com")).not.toBeNull();
		});

		it("returns null when not found", async () => {
			setRows([]);
			expect(await authService.getUserByEmail("none@x.com")).toBeNull();
		});
	});
});
