// @vitest-environment jsdom
import { render, screen } from "@testing-library/svelte";
import { beforeEach, describe, expect, it } from "vitest";
import Page from "../+page.svelte";

describe("+page.svelte (home)", () => {
	beforeEach(async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { user: { id: "u1", username: "alice", coins: 100 } };
	});

	it("renders welcome heading with username", () => {
		render(Page);
		expect(screen.getByText(/Welcome, alice/)).toBeInTheDocument();
	});

	it("renders game links", () => {
		render(Page);
		expect(screen.getByRole("link", { name: /Blackjack/ })).toBeInTheDocument();
		expect(screen.getByRole("link", { name: /Roulette/ })).toBeInTheDocument();
		expect(screen.getByRole("link", { name: /Slots/ })).toBeInTheDocument();
	});

	it("renders welcome without username when no user", async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { user: null };

		render(Page);
		expect(screen.getByText("Welcome")).toBeInTheDocument();
	});

	it("links point to correct paths", () => {
		render(Page);
		expect(screen.getByRole("link", { name: /Blackjack/ })).toHaveAttribute(
			"href",
			"/blackjack",
		);
		expect(screen.getByRole("link", { name: /Roulette/ })).toHaveAttribute(
			"href",
			"/roulette",
		);
		expect(screen.getByRole("link", { name: /Slots/ })).toHaveAttribute(
			"href",
			"/slots",
		);
	});
});
