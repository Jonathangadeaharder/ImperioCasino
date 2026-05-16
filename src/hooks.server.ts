import PocketBase from 'pocketbase';
import { building } from '$app/environment';
import type { Handle } from '@sveltejs/kit';
import { PocketBaseAdapter } from '$lib/server/db/pocketbase';
import { env } from '$env/dynamic/private';

export const handle: Handle = async ({ event, resolve }) => {
	if (building) return resolve(event);

	const pbUrl = env.POCKETBASE_URL || 'http://127.0.0.1:8090';
	const pb = new PocketBase(pbUrl);
	event.locals.pb = pb;
	event.locals.db = new PocketBaseAdapter(pb);

	const authCookie = event.request.headers.get('cookie') || '';
	pb.authStore.loadFromCookie(authCookie);

	try {
		if (pb.authStore.isValid) {
			const token = pb.authStore.token as string;
			const payload = JSON.parse(atob(token.split('.')[1]));
			const expiresAt = payload.exp * 1000;
			const fiveMinutes = 5 * 60 * 1000;
			if (Date.now() > expiresAt - fiveMinutes) {
				await pb.collection('users').authRefresh();
			}
		}
	} catch {
		pb.authStore.clear();
	}

	event.locals.user = pb.authStore.isValid
		? { id: pb.authStore.model!.id, username: pb.authStore.model!.username, coins: pb.authStore.model!.coins }
		: null;

	const response = await resolve(event);
	response.headers.set('set-cookie', pb.authStore.exportToCookie({ httpOnly: false }));
	return response;
};
