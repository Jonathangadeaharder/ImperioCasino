import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	if (locals.user) redirect(303, '/');
	return {};
};

export const actions: Actions = {
	default: async ({ request, locals }) => {
		const data = await request.formData();
		const username = data.get('username') as string;
		const email = data.get('email') as string;
		const password = data.get('password') as string;

		if (!username || !email || !password) return fail(400, { error: 'All fields required' });

		try {
			await locals.pb.collection('users').create({
				username, email, password, passwordConfirm: password, coins: 100
			});
			await locals.pb.collection('users').authWithPassword(email, password);
		} catch (e: unknown) {
			const msg = e instanceof Error ? e.message : 'Registration failed';
			return fail(400, { error: msg });
		}
		redirect(303, '/');
	}
};
