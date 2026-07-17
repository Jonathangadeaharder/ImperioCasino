// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from "vitest";

const envState = vi.hoisted(() => ({
	building: false,
}));

const authState = vi.hoisted(() => ({
	session: null as {
		user: { id: string; username: string; coins: number };
	} | null,
}));

vi.mock("$app/environment", () => ({
	get building() {
		return envState.building;
	},
	dev: true,
	prerender: false,
}));

vi.mock("$lib/server/db/database", () => ({
	ensureDb: vi.fn(async () => {}),
}));

vi.mock("$lib/server/auth-service", () => ({
	authService: {
		getSession: vi.fn(async () => authState.session),
	},
}));

import { handle } from "../hooks.server";

function makeEvent(pathname: string, cookie = ""): any {
	return {
		url: new URL(`http://localhost:5173${pathname}`),
		request: { headers: { get: vi.fn(() => cookie) } },
		cookies: { set: vi.fn(), delete: vi.fn() },
		locals: {} as Record<string, unknown>,
	};
}

function mockResolve(): any {
	return { headers: { set: vi.fn(), append: vi.fn() } };
}

describe("hooks.server handle", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		authState.session = null;
		envState.building = false;
	});

	it("skips ensureDb and auth when building", async () => {
		envState.building = true;
		const event = makeEvent("/blackjack");
		const resolve = vi.fn().mockResolvedValue(mockResolve());
		await handle({ event, resolve } as any);
		expect(resolve).toHaveBeenCalledWith(event);
	});

	it("sets up db and auth on locals", async () => {
		const event = makeEvent("/");
		const resolve = vi.fn().mockResolvedValue(mockResolve());
		await handle({ event, resolve } as any);
		expect(event.locals.db).toBeDefined();
		expect(typeof event.locals.auth).toBe("function");
	});

	it("sets user to null when no session", async () => {
		authState.session = null;
		const event = makeEvent("/");
		const resolve = vi.fn().mockResolvedValue(mockResolve());
		await handle({ event, resolve } as any);
		expect(event.locals.user).toBeNull();
	});

	it("sets user from session when authenticated", async () => {
		authState.session = {
			user: { id: "user1", username: "test", coins: 500 },
		};
		const event = makeEvent("/blackjack");
		const resolve = vi.fn().mockResolvedValue(mockResolve());
		await handle({ event, resolve } as any);
		expect(event.locals.user).toEqual({
			id: "user1",
			username: "test",
			coins: 500,
		});
	});

	it("redirects unauthenticated users on protected paths", async () => {
		authState.session = null;
		const event = makeEvent("/blackjack");
		const resolve = vi.fn().mockResolvedValue(mockResolve());
		await expect(handle({ event, resolve } as any)).rejects.toMatchObject({
			status: 303,
			location: "/login",
		});
		expect(resolve).not.toHaveBeenCalled();
	});

	it("allows public paths without session", async () => {
		authState.session = null;
		const event = makeEvent("/login");
		const resolve = vi.fn().mockResolvedValue(mockResolve());
		await handle({ event, resolve } as any);
		expect(resolve).toHaveBeenCalled();
	});

	it("allows root path without session", async () => {
		authState.session = null;
		const event = makeEvent("/");
		const resolve = vi.fn().mockResolvedValue(mockResolve());
		await handle({ event, resolve } as any);
		expect(resolve).toHaveBeenCalled();
	});

	it("applies security headers to response", async () => {
		authState.session = null;
		const event = makeEvent("/login");
		const response = mockResolve();
		const resolve = vi.fn().mockResolvedValue(response);
		await handle({ event, resolve } as any);
		expect(response.headers.set).toHaveBeenCalledWith(
			"X-Frame-Options",
			"DENY",
		);
		expect(response.headers.set).toHaveBeenCalledWith(
			"X-Content-Type-Options",
			"nosniff",
		);
	});
});
