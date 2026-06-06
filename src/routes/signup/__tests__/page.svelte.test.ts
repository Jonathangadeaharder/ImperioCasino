// @vitest-environment jsdom
import { render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import Page from "../+page.svelte";

describe("signup +page.svelte", () => {
	it("renders signup heading", () => {
		render(Page);
		expect(screen.getByText("Sign Up")).toBeInTheDocument();
	});

	it("renders username, email, and password inputs", () => {
		render(Page);
		expect(screen.getByLabelText("Username")).toBeInTheDocument();
		expect(screen.getByLabelText("Email")).toBeInTheDocument();
		expect(screen.getByLabelText("Password")).toBeInTheDocument();
	});

	it("renders submit button", () => {
		render(Page);
		expect(
			screen.getByRole("button", { name: "Create Account" }),
		).toBeInTheDocument();
	});

	it("renders link to login", () => {
		render(Page);
		const link = screen.getByRole("link", {
			name: "Already have an account?",
		});
		expect(link).toHaveAttribute("href", "/login");
	});

	it("renders form with POST method", () => {
		render(Page);
		const form = screen
			.getByRole("button", { name: "Create Account" })
			.closest("form");
		expect(form).toHaveAttribute("method", "POST");
	});

	it("displays error message when form has error", () => {
		render(Page, { form: { error: "Username already taken" } });
		expect(screen.getByText("Username already taken")).toBeInTheDocument();
	});

	it("does not display error when form has no error", () => {
		const { container } = render(Page, { form: null });
		expect(container.querySelector(".error")).not.toBeInTheDocument();
	});
});
