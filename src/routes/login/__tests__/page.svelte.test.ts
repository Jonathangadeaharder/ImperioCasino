// @vitest-environment jsdom
import { render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import Page from "../+page.svelte";

describe("login +page.svelte", () => {
	it("renders login heading", () => {
		render(Page);
		expect(screen.getByRole("heading", { name: "Login" })).toBeInTheDocument();
	});

	it("renders email and password inputs", () => {
		render(Page);
		expect(screen.getByLabelText("Email")).toBeInTheDocument();
		expect(screen.getByLabelText("Password")).toBeInTheDocument();
	});

	it("renders submit button", () => {
		render(Page);
		expect(screen.getByRole("button", { name: "Login" })).toBeInTheDocument();
	});

	it("renders link to signup", () => {
		render(Page);
		const link = screen.getByRole("link", { name: "Create account" });
		expect(link).toHaveAttribute("href", "/signup");
	});

	it("renders form with POST method", () => {
		render(Page);
		const form = screen.getByRole("button", { name: "Login" }).closest("form");
		expect(form).toHaveAttribute("method", "POST");
	});

	it("displays error message when form has error", () => {
		render(Page, { form: { error: "Invalid credentials" } });
		expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
	});

	it("does not display error when form has no error", () => {
		const { container } = render(Page, { form: null });
		expect(container.querySelector(".error")).not.toBeInTheDocument();
	});
});
