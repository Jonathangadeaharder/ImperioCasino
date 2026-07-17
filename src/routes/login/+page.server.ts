import { fail, redirect } from "@sveltejs/kit";
import { authService } from "$lib/server/auth-service";
import type { Actions, PageServerLoad } from "./$types";

export const load: PageServerLoad = async ({ locals }) => {
	if (locals.user) redirect(303, "/");
	return {};
};

export const actions: Actions = {
	default: async (event) => {
		const data = await event.request.formData();
		const email = (data.get("email") as string)?.trim();
		const password = data.get("password") as string;

		if (!email || !password)
			return fail(400, { error: "Email and password required" });

		const { user, error } = await authService.signIn(event, email, password);
		if (error || !user)
			return fail(401, { error: error ?? "Invalid credentials" });

		redirect(303, "/");
	},
};
