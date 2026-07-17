import { redirect } from "@sveltejs/kit";
import { authService } from "$lib/server/auth-service";
import type { Actions } from "./$types";

export const actions: Actions = {
	default: async (event) => {
		await authService.signOut(event);
		redirect(303, "/login");
	},
};

export const load = async () => {
	redirect(303, "/login");
};
