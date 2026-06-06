// @vitest-environment jsdom
import { render, screen } from "@testing-library/svelte";
import { beforeEach, describe, expect, it } from "vitest";
import Layout from "../+layout.svelte";

describe("+layout.svelte", () => {
	beforeEach(async () => {
		const { page } = await import("$app/stores");
		// @ts-expect-error - mock store setter
		page.data = { user: null };
	});

	it("renders Nav component with site title", () => {
		render(Layout, {
			children: () => "",
		});

		expect(
			screen.getByRole("link", { name: "ImperioCasino" }),
		).toBeInTheDocument();
	});

	it("renders main element", () => {
		const { container } = render(Layout, {
			children: () => "",
		});

		expect(container.querySelector("main")).toBeInTheDocument();
	});

	it("renders main element for children", () => {
		const { container } = render(Layout, {
			children: () => "",
		});

		const main = container.querySelector("main");
		expect(main).toBeInTheDocument();
	});
});
