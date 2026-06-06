// @vitest-environment jsdom
import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock @threlte/core with simple passthrough components
vi.mock("@threlte/core", () => {
	function MockCanvas() {}
	MockCanvas.prototype.$$render = (
		_result: any,
		_props: any,
		_bindings: any,
		slots: any,
	) => {
		const slotContent = slots?.default?.() ?? "";
		return slotContent;
	};

	return {
		Canvas: MockCanvas,
		T: new Proxy(
			{},
			{
				get(_, _tag: string) {
					return () => {};
				},
			},
		),
	};
});

import Page from "../+page.svelte";

describe("slots +page.svelte", () => {
	beforeEach(async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { coins: 50 };
	});

	it("renders slots heading", () => {
		render(Page);
		expect(screen.getByText("Slots")).toBeInTheDocument();
	});

	it("shows coins display", () => {
		render(Page);
		expect(screen.getByText(/Coins: 50/)).toBeInTheDocument();
	});

	it("renders SPIN button when coins available", () => {
		render(Page);
		expect(
			screen.getByRole("button", { name: "SPIN (1 coin)" }),
		).toBeInTheDocument();
	});

	it("disables SPIN button when no coins", async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { coins: 0 };
		render(Page);
		expect(screen.getByRole("button", { name: "No coins" })).toBeDisabled();
	});

	it("spins and shows win result", async () => {
		vi.useFakeTimers();
		vi.stubGlobal(
			"fetch",
			vi.fn().mockResolvedValue({
				ok: true,
				json: () =>
					Promise.resolve({
						fruits: ["🍒", "🍒", "🍒"],
						payout: 50,
						total_coins: 99,
					}),
			}),
		);

		render(Page);
		await fireEvent.click(
			screen.getByRole("button", { name: "SPIN (1 coin)" }),
		);

		await waitFor(() => {
			expect(screen.getByText(/You won 50 coins!/)).toBeInTheDocument();
		});

		// Advance timer to reset spinning state
		vi.advanceTimersByTime(2100);
		vi.useRealTimers();
	});

	it("spins and shows no-win result", async () => {
		vi.useFakeTimers();
		vi.stubGlobal(
			"fetch",
			vi.fn().mockResolvedValue({
				ok: true,
				json: () =>
					Promise.resolve({
						fruits: ["🍒", "🍋", "🔔"],
						payout: 0,
						total_coins: 49,
					}),
			}),
		);

		render(Page);
		await fireEvent.click(
			screen.getByRole("button", { name: "SPIN (1 coin)" }),
		);

		await waitFor(() => {
			expect(screen.getByText("No win. Try again!")).toBeInTheDocument();
		});

		vi.advanceTimersByTime(2100);
		vi.useRealTimers();
	});

	it("shows error on failed spin", async () => {
		vi.useFakeTimers();
		vi.stubGlobal(
			"fetch",
			vi.fn().mockResolvedValue({
				ok: false,
				json: () => Promise.resolve({ error: "Not enough coins" }),
			}),
		);

		render(Page);
		await fireEvent.click(
			screen.getByRole("button", { name: "SPIN (1 coin)" }),
		);

		await waitFor(() => {
			expect(screen.getByText("Not enough coins")).toBeInTheDocument();
		});

		vi.advanceTimersByTime(2100);
		vi.useRealTimers();
	});

	it("shows error on fetch failure", async () => {
		vi.useFakeTimers();
		vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network")));

		render(Page);
		await fireEvent.click(
			screen.getByRole("button", { name: "SPIN (1 coin)" }),
		);

		await waitFor(() => {
			expect(screen.getByText("Spin failed. Try again.")).toBeInTheDocument();
		});

		vi.advanceTimersByTime(2100);
		vi.useRealTimers();
	});
});
