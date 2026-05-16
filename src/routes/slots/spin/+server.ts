import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { spinReels, segmentToFruit, calculatePayout } from '$lib/server/games/slots';
import type { Fruit } from '$lib/types';

export const POST: RequestHandler = async ({ locals }) => {
	const coins = await locals.db.getCoins(locals.user!.id);
	if (coins < 1) return json({ error: 'Not enough coins' }, { status: 400 });

	await locals.db.deductCoins(locals.user!.id, 1);
	const segments = spinReels();
	const fruits: [Fruit, Fruit, Fruit] = [
		segmentToFruit(0, segments[0]),
		segmentToFruit(1, segments[1]),
		segmentToFruit(2, segments[2])
	];
	const payout = calculatePayout(fruits);
	if (payout > 0) await locals.db.addCoins(locals.user!.id, payout);
	const totalCoins = await locals.db.getCoins(locals.user!.id);

	return json({ stop_segments: segments, fruits, payout, total_coins: totalCoins });
};
