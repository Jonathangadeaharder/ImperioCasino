// @vitest-environment node
import { describe, expect, it, vi } from "vitest";

const authMock = vi.hoisted(() => ({
	signOut: vi.fn(async () => {}),
}));

vi.mock("$lib/server/auth-service", () => ({
	authService: { signOut: authMock.signOut },
}));

import { actions, load } from "../+page.server";

function mockEvent(): any {
	return {
		request: new Request("http://localhost:5173/logout"),
		cookies: { set: vi.fn(), delete: vi.fn() },
		locals: {
			db: {},
			user: { id: "u1", username: "t", coins: 100 },
		},
		params: {},
		url: new URL("http://localhost:5173/logout"),
	} as any;
}

describe("logout +page.server", () => {
	describe("load", () => {
		it("redirects to /login", async () => {
			await expect(load()).rejects.toMatchObject({
				status: 303,
				location: "/login",
			});
		});
	});

	describe("actions.default", () => {
		it("signs out and redirects to /login", async () => {
			const event = mockEvent();
			await expect(actions.default(event)).rejects.toMatchObject({
				status: 303,
				location: "/login",
			});
			expect(authMock.signOut).toHaveBeenCalledWith(event);
		});
	});
});
