// @vitest-environment jsdom
import { render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import CoinBalance from "../CoinBalance.svelte";

describe("CoinBalance", () => {
	it("renders coin count from page store", async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { user: { coins: 500 } };
		render(CoinBalance);
		expect(screen.getByText(/500/)).toBeInTheDocument();
	});

	it("defaults to 0 when no user in page data", async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = {};
		render(CoinBalance);
		expect(screen.getByText(/0/)).toBeInTheDocument();
	});
});
