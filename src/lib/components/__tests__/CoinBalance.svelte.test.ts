// @vitest-environment jsdom
import { render, screen } from "@testing-library/svelte";
import { beforeEach, describe, expect, it } from "vitest";
import CoinBalance from "../CoinBalance.svelte";

describe("CoinBalance.svelte", () => {
	beforeEach(async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { user: null };
	});

	it("shows 0 coins when no user", () => {
		render(CoinBalance);
		expect(screen.getByText(/0/)).toBeInTheDocument();
	});

	it("shows user coins from page store", async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { user: { id: "u1", username: "player", coins: 750 } };
		render(CoinBalance);
		expect(screen.getByText(/750/)).toBeInTheDocument();
	});

	it("renders coin emoji", () => {
		render(CoinBalance);
		expect(screen.getByText(/🪙/)).toBeInTheDocument();
	});
});
