import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	const coins = await locals.db.getCoins(locals.user!.id);
	return { coins };
};
