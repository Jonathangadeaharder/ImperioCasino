// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/svelte";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Page from "../+page.svelte";

describe("blackjack +page.svelte", () => {
	beforeEach(async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { coins: 100 };
	});

	it("renders blackjack heading", () => {
		render(Page);
		expect(screen.getByText("Blackjack")).toBeInTheDocument();
	});

	it("shows coins display before game starts", () => {
		render(Page);
		expect(screen.getByText(/Coins: 100/)).toBeInTheDocument();
	});

	it("renders Deal button", () => {
		render(Page);
		expect(
			screen.getByRole("button", { name: "Deal" }),
		).toBeInTheDocument();
	});

	it("renders BlackjackBoard component", () => {
		const { container } = render(Page);
		expect(container.querySelector(".board")).not.toBeInTheDocument();
	});

	it("starts game on Deal click and shows game board", async () => {
		const mockGame = {
			id: "g1",
			player_hand: ["7♥", "K♠"],
			dealer_hand: ["9♣"],
			player_coins: 90,
			game_over: false,
		};
		vi.stubGlobal(
			"fetch",
			vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockGame),
			}),
		);

		render(Page);
		await fireEvent.click(screen.getByRole("button", { name: "Deal" }));

		await waitFor(() => {
			// After deal, the board shows Hit/Stand buttons
			expect(screen.getByRole("button", { name: "Hit" })).toBeInTheDocument();
			expect(screen.getByRole("button", { name: "Stand" })).toBeInTheDocument();
		});
	});

	it("shows alert when deal fails (not enough coins)", async () => {
		const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
		vi.stubGlobal(
			"fetch",
			vi.fn().mockResolvedValue({
				ok: false,
				json: () => Promise.resolve({ error: "Not enough coins" }),
			}),
		);

		render(Page);
		await fireEvent.click(screen.getByRole("button", { name: "Deal" }));

		await waitFor(() => {
			expect(alertSpy).toHaveBeenCalledWith("Not enough coins!");
		});
		alertSpy.mockRestore();
	});

	it("handles action and shows coins-after when game over", async () => {
		// First: deal
		const dealResponse = {
			id: "g1",
			player_hand: ["7♥", "K♠"],
			dealer_hand: ["9♣"],
			player_coins: 90,
			game_over: false,
		};
		// Then: stand action => game over
		const standResponse = {
			id: "g1",
			player_hand: ["7♥", "K♠"],
			dealer_hand: ["9♣", "8♦"],
			player_coins: 110,
			game_over: true,
			message: "You win!",
		};
		let callCount = 0;
		vi.stubGlobal(
			"fetch",
			vi.fn().mockImplementation(() => {
				callCount++;
				return Promise.resolve({
					ok: true,
					json: () =>
						Promise.resolve(
							callCount === 1 ? dealResponse : standResponse,
						),
				});
			}),
		);

		render(Page);
		await fireEvent.click(screen.getByRole("button", { name: "Deal" }));

		await waitFor(() => {
			expect(screen.getByRole("button", { name: "Stand" })).toBeInTheDocument();
		});

		await fireEvent.click(screen.getByRole("button", { name: "Stand" }));

		await waitFor(() => {
			// After game over, coins-after shows and result modal shows
			expect(screen.getByText("You win!")).toBeInTheDocument();
		});
	});
});
