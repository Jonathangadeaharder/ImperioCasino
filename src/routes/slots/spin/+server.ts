import { json } from "@sveltejs/kit";
import {
	calculatePayout,
	segmentToFruit,
	spinReels,
} from "$lib/server/games/slots";
import type { Fruit } from "$lib/types";
import type { RequestHandler } from "./$types";

export const POST: RequestHandler = async ({ locals }) => {
	const userId = locals.user?.id;
	if (!userId) return json({ error: "Not authenticated" }, { status: 401 });
	const coins = await locals.db.getCoins(userId);
	if (coins < 1) return json({ error: "Not enough coins" }, { status: 400 });

	await locals.db.deductCoins(userId, 1);
	const segments = spinReels();
	const fruits: [Fruit, Fruit, Fruit] = [
		segmentToFruit(0, segments[0]),
		segmentToFruit(1, segments[1]),
		segmentToFruit(2, segments[2]),
	];
	const payout = calculatePayout(fruits);
	if (payout > 0) await locals.db.addCoins(userId, payout);
	const totalCoins = await locals.db.getCoins(userId);

	return json({
		stop_segments: segments,
		fruits,
		payout,
		total_coins: totalCoins,
	});
};
