// @vitest-environment node
import { describe, expect, it, vi } from "vitest";

const authMock = vi.hoisted(() => ({
	signIn: vi.fn(),
}));

vi.mock("$lib/server/auth-service", () => ({
	authService: { signIn: authMock.signIn },
}));

import { actions, load } from "../+page.server";

function mockEvent(overrides?: Record<string, unknown>) {
	return {
		request: new Request("http://localhost:5173/login"),
		cookies: { set: vi.fn(), delete: vi.fn() },
		locals: { db: {}, user: null },
		params: {},
		url: new URL("http://localhost:5173/login"),
		...(overrides ?? {}),
	} as any;
}

function formRequest(data: Record<string, string>): Request {
	const formData = new FormData();
	for (const [k, v] of Object.entries(data)) formData.append(k, v);
	return new Request("http://localhost:5173/login", {
		method: "POST",
		body: formData,
	});
}

describe("login +page.server", () => {
	describe("load", () => {
		it("returns empty object when not logged in", async () => {
			expect(await load(mockEvent())).toEqual({});
		});

		it("redirects to / when user is already logged in", async () => {
			const event = mockEvent();
			event.locals.user = { id: "u1", username: "t", coins: 1 };
			await expect(load(event)).rejects.toMatchObject({
				status: 303,
				location: "/",
			});
		});
	});

	describe("actions.default", () => {
		it("authenticates with valid credentials and redirects", async () => {
			authMock.signIn.mockResolvedValueOnce({
				user: { id: "u1", username: "alice", email: "a@x.com", coins: 100 },
				error: null,
			});
			const event = mockEvent({
				request: formRequest({ email: "a@x.com", password: "secret123" }),
			});
			await expect(actions.default(event)).rejects.toMatchObject({
				status: 303,
				location: "/",
			});
			expect(authMock.signIn).toHaveBeenCalledWith(
				event,
				"a@x.com",
				"secret123",
			);
		});

		it("returns 400 when email is missing", async () => {
			const event = mockEvent({
				request: formRequest({ password: "secret123" }),
			});
			const result = (await actions.default(event)) as {
				status: number;
				data: Record<string, unknown>;
			};
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe("Email and password required");
		});

		it("returns 400 when password is missing", async () => {
			const event = mockEvent({
				request: formRequest({ email: "a@x.com" }),
			});
			const result = (await actions.default(event)) as {
				status: number;
				data: Record<string, unknown>;
			};
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe("Email and password required");
		});

		it("returns 401 on invalid credentials", async () => {
			authMock.signIn.mockResolvedValueOnce({
				user: null,
				error: "Invalid email or password.",
			});
			const event = mockEvent({
				request: formRequest({ email: "a@x.com", password: "wrong" }),
			});
			const result = (await actions.default(event)) as {
				status: number;
				data: Record<string, unknown>;
			};
			expect(result.status).toBe(401);
			expect(result.data?.error).toBe("Invalid email or password.");
		});

		it("returns 401 when service returns no user and no error", async () => {
			authMock.signIn.mockResolvedValueOnce({ user: null, error: null });
			const event = mockEvent({
				request: formRequest({ email: "a@x.com", password: "secret123" }),
			});
			const result = (await actions.default(event)) as {
				status: number;
				data: Record<string, unknown>;
			};
			expect(result.status).toBe(401);
			expect(result.data?.error).toBe("Invalid credentials");
		});
	});
});
