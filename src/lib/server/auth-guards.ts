import type { ServerLoadEvent } from "@sveltejs/kit";
import { redirect } from "@sveltejs/kit";

// Shared load for auth pages (login, signup): redirect authenticated
// users to the lobby, otherwise render the page with no data.
export async function authPageLoad(
	event: ServerLoadEvent,
): Promise<Record<string, never>> {
	if (event.locals.user) redirect(303, "/");
	return {};
}
