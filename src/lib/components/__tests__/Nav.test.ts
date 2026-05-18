// @vitest-environment jsdom
import { render, screen } from "@testing-library/svelte";
import { beforeEach, describe, expect, it } from "vitest";
import Nav from "../Nav.svelte";

describe("Nav", () => {
	beforeEach(async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = {};
	});

	it("renders site title and navigation links", () => {
		render(Nav);
		expect(
			screen.getByRole("link", { name: "ImperioCasino" }),
		).toBeInTheDocument();
		expect(screen.getByRole("link", { name: "Blackjack" })).toBeInTheDocument();
		expect(screen.getByRole("link", { name: "Roulette" })).toBeInTheDocument();
		expect(screen.getByRole("link", { name: "Slots" })).toBeInTheDocument();
	});

	it("does not show logout link when no user", () => {
		render(Nav);
		expect(
			screen.queryByRole("link", { name: "Logout" }),
		).not.toBeInTheDocument();
	});
});
