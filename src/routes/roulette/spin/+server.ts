import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { spinWheel, calculatePayouts } from '$lib/server/games/roulette';
import type { Bet } from '$lib/types';

export const POST: RequestHandler = async ({ request, locals }) => {
	const { bets } = await request.json() as { bets: Bet[] };
	if (!bets.length) return json({ error: 'Place at least one bet' }, { status: 400 });

	const totalBet = bets.reduce((s, b) => s + b.amt, 0);
	const coins = await locals.db.getCoins(locals.user!.id);
	if (coins < totalBet) return json({ error: 'Not enough coins' }, { status: 400 });

	const winningNumber = spinWheel();
	const totalWin = calculatePayouts(bets, winningNumber);

	await locals.db.deductCoins(locals.user!.id, totalBet);
	if (totalWin > 0) await locals.db.addCoins(locals.user!.id, totalWin);

	const newCoins = await locals.db.getCoins(locals.user!.id);
	return json({ winning_number: winningNumber, total_bet: totalBet, total_win: totalWin, new_coins: newCoins });
};
