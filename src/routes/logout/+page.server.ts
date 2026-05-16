import { redirect } from '@sveltejs/kit';
import type { Actions } from './$types';

export const actions: Actions = {
	default: async ({ locals }) => {
		locals.pb.authStore.clear();
		redirect(303, '/login');
	}
};

export const load = async () => {
	redirect(303, '/login');
};
