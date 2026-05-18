import type { Handle } from "@sveltejs/kit";
import PocketBase from "pocketbase";
import { building, dev } from "$app/environment";
import { PocketBaseAdapter } from "$lib/server/db/pocketbase";

export const handle: Handle = async ({ event, resolve }) => {
	if (building) return resolve(event);

	const pb = new PocketBase("http://127.0.0.1:8090");
	event.locals.pb = pb;
	event.locals.db = new PocketBaseAdapter(pb);

	const authCookie = event.request.headers.get("cookie") || "";
	pb.authStore.loadFromCookie(authCookie);

	try {
		if (pb.authStore.isValid) {
			await pb.collection("users").authRefresh();
		}
	} catch {
		pb.authStore.clear();
	}

	event.locals.user =
		pb.authStore.isValid && pb.authStore.model
			? {
					id: pb.authStore.model.id as string,
					username: pb.authStore.model.username as string,
					coins: pb.authStore.model.coins as number,
				}
			: null;

	const response = await resolve(event);
	response.headers.append(
		"set-cookie",
		pb.authStore.exportToCookie({
			httpOnly: true,
			secure: !dev,
			sameSite: "lax",
			path: "/",
		}),
	);
	return response;
};
