import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	if (locals.user) redirect(303, '/');
	return {};
};

export const actions: Actions = {
	default: async ({ request, locals }) => {
		const data = await request.formData();
		const email = data.get('email') as string;
		const password = data.get('password') as string;

		if (!email || !password) return fail(400, { error: 'Email and password required' });

		try {
			await locals.pb.collection('users').authWithPassword(email, password);
		} catch {
			return fail(401, { error: 'Invalid credentials' });
		}
		redirect(303, '/');
	}
};
