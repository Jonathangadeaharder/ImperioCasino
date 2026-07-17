import { fail, redirect } from "@sveltejs/kit";
import { authPageLoad } from "$lib/server/auth-guards";
import { authService } from "$lib/server/auth-service";
import type { Actions, PageServerLoad } from "./$types";

export const load: PageServerLoad = authPageLoad;

export const actions: Actions = {
	default: async (event) => {
		const data = await event.request.formData();
		const username = (data.get("username") as string)?.trim();
		const email = (data.get("email") as string)?.trim();
		const password = data.get("password") as string;

		if (!username || !email || !password)
			return fail(400, { error: "All fields required" });

		const { user, error } = await authService.signUp(
			event,
			username,
			email,
			password,
		);
		if (error || !user)
			return fail(400, { error: error ?? "Registration failed" });

		redirect(303, "/");
	},
};
