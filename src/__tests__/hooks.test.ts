// @vitest-environment node
import { describe, expect, it, vi } from "vitest";

const mockStore = {
	isValid: false,
	loadFromCookie: vi.fn(),
	clear: vi.fn(),
	model: null as { id: string; username: string; coins: number } | null,
	exportToCookie: vi.fn(() => "pb_auth=session"),
};

vi.mock("pocketbase", () => ({
	default: vi.fn(() => ({
		collection: vi.fn().mockReturnValue({
			authRefresh: vi.fn().mockResolvedValue({}),
			getOne: vi.fn(),
			getList: vi.fn(),
			create: vi.fn(),
			update: vi.fn(),
		}),
		authStore: mockStore,
	})),
}));

import { handle } from "../hooks.server";

function mockResolve() {
	return { headers: { set: vi.fn() } };
}

describe("hooks.server handle", () => {
	it("skips auth when building", async () => {
		const event = {
			request: { headers: { get: vi.fn(() => "") } },
			locals: {},
		} as any;
		const resolve = vi.fn().mockResolvedValue({ headers: { set: vi.fn() } });

		await handle({ event, resolve });

		expect(resolve).toHaveBeenCalledWith(event);
	});

	it("sets up pb and db on locals", async () => {
		const event = {
			request: { headers: { get: vi.fn(() => "") } },
			locals: {},
		} as any;
		const resolve = vi.fn().mockResolvedValue(mockResolve());

		await handle({ event, resolve });

		expect(event.locals.pb).toBeDefined();
		expect(event.locals.db).toBeDefined();
	});

	it("loads auth cookie from request", async () => {
		const event = {
			request: { headers: { get: vi.fn(() => "pb_auth=token123") } },
			locals: {},
		} as any;
		const resolve = vi.fn().mockResolvedValue(mockResolve());

		await handle({ event, resolve });

		expect(mockStore.loadFromCookie).toHaveBeenCalledWith("pb_auth=token123");
	});

	it("sets user to null when auth store is invalid", async () => {
		mockStore.isValid = false;
		const event = {
			request: { headers: { get: vi.fn(() => "") } },
			locals: {},
		} as any;
		const resolve = vi.fn().mockResolvedValue(mockResolve());

		await handle({ event, resolve });

		expect(event.locals.user).toBeNull();
	});

	it("sets user from auth store when valid", async () => {
		mockStore.isValid = true;
		mockStore.model = { id: "user1", username: "test", coins: 500 };
		const event = {
			request: { headers: { get: vi.fn(() => "pb_auth=token") } },
			locals: {},
		} as any;
		const resolve = vi.fn().mockResolvedValue(mockResolve());

		await handle({ event, resolve });

		expect(event.locals.user).toEqual({
			id: "user1",
			username: "test",
			coins: 500,
		});
	});

	it("sets set-cookie header on response", async () => {
		mockStore.isValid = false;
		const event = {
			request: { headers: { get: vi.fn(() => "") } },
			locals: {},
		} as any;
		const mockRes = mockResolve();
		const resolve = vi.fn().mockResolvedValue(mockRes);

		await handle({ event, resolve });

		expect(mockRes.headers.set).toHaveBeenCalledWith(
			"set-cookie",
			"pb_auth=session",
		);
	});
});
