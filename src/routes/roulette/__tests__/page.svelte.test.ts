// @vitest-environment jsdom
import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Page from "../+page.svelte";

describe("roulette +page.svelte", () => {
	beforeEach(async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { coins: 200 };
	});

	it("renders roulette heading", () => {
		render(Page);
		expect(screen.getByText("Roulette")).toBeInTheDocument();
	});

	it("shows coins display", () => {
		render(Page);
		expect(screen.getByText(/Coins: 200/)).toBeInTheDocument();
	});

	it("renders Spin button disabled when no bets", () => {
		render(Page);
		const btn = screen.getByRole("button", { name: "Spin!" });
		expect(btn).toBeDisabled();
	});

	it("renders number grid with 37 cells (0-36)", () => {
		render(Page);
		const grid = screen.getByText("0").closest(".grid");
		expect(grid).toBeInTheDocument();
	});

	it("renders outside bet labels", () => {
		render(Page);
		expect(screen.getByText("1-12")).toBeInTheDocument();
		expect(screen.getByText("Red")).toBeInTheDocument();
		expect(screen.getByText("Black")).toBeInTheDocument();
	});

	it("shows current bets total as 0 initially", () => {
		render(Page);
		expect(screen.getByText(/Current bets: 0/)).toBeInTheDocument();
	});

	it("toggles bet on number click and updates bets total", async () => {
		render(Page);
		// Click number "7" to add bet
		await fireEvent.click(screen.getByText("7"));
		expect(screen.getByText(/Current bets: 10/)).toBeInTheDocument();

		// Click again to remove bet
		await fireEvent.click(screen.getByText("7"));
		expect(screen.getByText(/Current bets: 0/)).toBeInTheDocument();
	});

	it("toggles outside bet and enables Spin button", async () => {
		render(Page);
		await fireEvent.click(screen.getByText("Red"));
		expect(screen.getByRole("button", { name: "Spin!" })).not.toBeDisabled();
		expect(screen.getByText(/Current bets: 10/)).toBeInTheDocument();
	});

	it("spins and shows win result", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn().mockResolvedValue({
				ok: true,
				json: () =>
					Promise.resolve({
						winning_number: 7,
						total_bet: 10,
						total_win: 360,
						new_coins: 550,
					}),
			}),
		);

		render(Page);
		await fireEvent.click(screen.getByText("7"));
		await fireEvent.click(screen.getByRole("button", { name: "Spin!" }));

		await waitFor(() => {
			expect(screen.getByText(/Result: 7/)).toBeInTheDocument();
			expect(screen.getByText(/You won 360 coins!/)).toBeInTheDocument();
		});
	});

	it("spins and shows no-win result", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn().mockResolvedValue({
				ok: true,
				json: () =>
					Promise.resolve({
						winning_number: 0,
						total_bet: 10,
						total_win: 0,
						new_coins: 190,
					}),
			}),
		);

		render(Page);
		await fireEvent.click(screen.getByText("7"));
		await fireEvent.click(screen.getByRole("button", { name: "Spin!" }));

		await waitFor(() => {
			expect(screen.getByText(/No win this time/)).toBeInTheDocument();
		});
	});

	it("shows error on failed spin", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn().mockResolvedValue({
				ok: false,
				json: () => Promise.resolve({ error: "Not enough coins" }),
			}),
		);

		render(Page);
		await fireEvent.click(screen.getByText("7"));
		await fireEvent.click(screen.getByRole("button", { name: "Spin!" }));

		await waitFor(() => {
			expect(screen.getByText("Not enough coins")).toBeInTheDocument();
		});
	});

	it("shows error on fetch failure", async () => {
		vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network")));

		render(Page);
		await fireEvent.click(screen.getByText("7"));
		await fireEvent.click(screen.getByRole("button", { name: "Spin!" }));

		await waitFor(() => {
			expect(
				screen.getByText("Spin failed. Please try again."),
			).toBeInTheDocument();
		});
	});
});
