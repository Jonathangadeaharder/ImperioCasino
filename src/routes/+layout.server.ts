import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals, url }) => {
	const publicPaths = ['/login', '/signup'];
	if (!locals.user && !publicPaths.includes(url.pathname)) {
		redirect(303, '/login');
	}
	return { user: locals.user };
};
