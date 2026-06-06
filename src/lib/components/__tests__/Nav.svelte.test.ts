// @vitest-environment jsdom
import { render, screen } from "@testing-library/svelte";
import { beforeEach, describe, expect, it } from "vitest";
import Nav from "../Nav.svelte";

describe("Nav.svelte", () => {
	beforeEach(async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { user: null };
	});

	it("renders site title link", () => {
		render(Nav);
		const link = screen.getByRole("link", { name: "ImperioCasino" });
		expect(link).toHaveAttribute("href", "/");
	});

	it("renders game navigation links", () => {
		render(Nav);
		expect(
			screen.getByRole("link", { name: "Blackjack" }),
		).toHaveAttribute("href", "/blackjack");
		expect(
			screen.getByRole("link", { name: "Roulette" }),
		).toHaveAttribute("href", "/roulette");
		expect(
			screen.getByRole("link", { name: "Slots" }),
		).toHaveAttribute("href", "/slots");
	});

	it("hides logout link when no user", () => {
		render(Nav);
		expect(
			screen.queryByRole("link", { name: "Logout" }),
		).not.toBeInTheDocument();
	});

	it("shows logout link when user is present", async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { user: { id: "u1", username: "player", coins: 100 } };
		render(Nav);
		expect(
			screen.getByRole("link", { name: "Logout" }),
		).toHaveAttribute("href", "/logout");
	});

	it("shows coin balance when user is present", async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { user: { id: "u1", username: "player", coins: 250 } };
		render(Nav);
		expect(screen.getByText(/250/)).toBeInTheDocument();
	});
});
