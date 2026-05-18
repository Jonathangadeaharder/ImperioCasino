import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async ({ locals }) => {
	const userId = locals.user?.id;
	if (!userId) return { coins: 0 };
	const coins = await locals.db.getCoins(userId);
	return { coins };
};
