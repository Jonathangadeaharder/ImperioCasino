// @vitest-environment node
import { describe, expect, it, vi } from "vitest";

const authMock = vi.hoisted(() => ({
	signUp: vi.fn(),
}));

vi.mock("$lib/server/auth-service", () => ({
	authService: { signUp: authMock.signUp },
}));

import { actions, load } from "../+page.server";

function mockEvent(overrides?: Record<string, unknown>) {
	return {
		request: new Request("http://localhost:5173/signup"),
		cookies: { set: vi.fn(), delete: vi.fn() },
		locals: { db: {}, user: null },
		params: {},
		url: new URL("http://localhost:5173/signup"),
		...(overrides ?? {}),
	} as any;
}

function formRequest(data: Record<string, string>): Request {
	const formData = new FormData();
	for (const [k, v] of Object.entries(data)) formData.append(k, v);
	return new Request("http://localhost:5173/signup", {
		method: "POST",
		body: formData,
	});
}

describe("signup +page.server", () => {
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
		it("creates user and redirects with valid data", async () => {
			authMock.signUp.mockResolvedValueOnce({
				user: { id: "u1", username: "alice", email: "a@x.com", coins: 100 },
				error: null,
			});
			const event = mockEvent({
				request: formRequest({
					username: "alice",
					email: "a@x.com",
					password: "secret123",
				}),
			});
			await expect(actions.default(event)).rejects.toMatchObject({
				status: 303,
				location: "/",
			});
			expect(authMock.signUp).toHaveBeenCalledWith(
				event,
				"alice",
				"a@x.com",
				"secret123",
			);
		});

		it("returns 400 when username is missing", async () => {
			const event = mockEvent({
				request: formRequest({ email: "a@x.com", password: "secret123" }),
			});
			const result = (await actions.default(event)) as {
				status: number;
				data: Record<string, unknown>;
			};
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe("All fields required");
		});

		it("returns 400 when email is missing", async () => {
			const event = mockEvent({
				request: formRequest({ username: "alice", password: "secret123" }),
			});
			const result = (await actions.default(event)) as {
				status: number;
				data: Record<string, unknown>;
			};
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe("All fields required");
		});

		it("returns 400 when password is missing", async () => {
			const event = mockEvent({
				request: formRequest({ username: "alice", email: "a@x.com" }),
			});
			const result = (await actions.default(event)) as {
				status: number;
				data: Record<string, unknown>;
			};
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe("All fields required");
		});

		it("returns 400 on duplicate account error", async () => {
			authMock.signUp.mockResolvedValueOnce({
				user: null,
				error: "Could not create your account. Please try again.",
			});
			const event = mockEvent({
				request: formRequest({
					username: "alice",
					email: "a@x.com",
					password: "secret123",
				}),
			});
			const result = (await actions.default(event)) as {
				status: number;
				data: Record<string, unknown>;
			};
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe(
				"Could not create your account. Please try again.",
			);
		});

		it("returns generic error when service returns no user and no error", async () => {
			authMock.signUp.mockResolvedValueOnce({ user: null, error: null });
			const event = mockEvent({
				request: formRequest({
					username: "alice",
					email: "a@x.com",
					password: "secret123",
				}),
			});
			const result = (await actions.default(event)) as {
				status: number;
				data: Record<string, unknown>;
			};
			expect(result.status).toBe(400);
			expect(result.data?.error).toBe("Registration failed");
		});

		it("trims whitespace from username and email", async () => {
			authMock.signUp.mockResolvedValueOnce({
				user: { id: "u1", username: "alice", email: "a@x.com", coins: 100 },
				error: null,
			});
			const event = mockEvent({
				request: formRequest({
					username: "  alice  ",
					email: "  a@x.com  ",
					password: "secret123",
				}),
			});
			await expect(actions.default(event)).rejects.toMatchObject({
				status: 303,
				location: "/",
			});
			expect(authMock.signUp).toHaveBeenCalledWith(
				event,
				"alice",
				"a@x.com",
				"secret123",
			);
		});
	});
});
