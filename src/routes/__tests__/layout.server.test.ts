// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import { load } from "../+layout.server";

function mockEvent(pathname: string, user: any = null) {
	return {
		locals: { user },
		url: new URL(`http://localhost:5173${pathname}`),
	} as Parameters<typeof load>[0];
}

describe("+layout.server load", () => {
	it("redirects to /login when no user on protected path", async () => {
		const event = mockEvent("/blackjack");

		await expect(load(event)).rejects.toMatchObject({
			status: 303,
			location: "/login",
		});
	});

	it("redirects to /login when no user on /roulette", async () => {
		const event = mockEvent("/roulette");

		await expect(load(event)).rejects.toMatchObject({
			status: 303,
			location: "/login",
		});
	});

	it("redirects to /login when no user on /slots", async () => {
		const event = mockEvent("/slots");

		await expect(load(event)).rejects.toMatchObject({
			status: 303,
			location: "/login",
		});
	});

	it("does not redirect on /login path without user", async () => {
		const event = mockEvent("/login");

		const result = await load(event);

		expect(result).toEqual({ user: null });
	});

	it("does not redirect on /signup path without user", async () => {
		const event = mockEvent("/signup");

		const result = await load(event);

		expect(result).toEqual({ user: null });
	});

	it("returns user when authenticated on protected path", async () => {
		const user = { id: "u1", username: "alice", coins: 100 };
		const event = mockEvent("/blackjack", user);

		const result = await load(event);

		expect(result).toEqual({ user });
	});

	it("returns user when authenticated on root path", async () => {
		const user = { id: "u1", username: "bob", coins: 200 };
		const event = mockEvent("/", user);

		const result = await load(event);

		expect(result).toEqual({ user });
	});
});
