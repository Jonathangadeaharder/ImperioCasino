import { json } from "@sveltejs/kit";
import { calculatePayouts, spinWheel } from "$lib/server/games/roulette";
import type { Bet } from "$lib/types";
import type { RequestHandler } from "./$types";

export const POST: RequestHandler = async ({ request, locals }) => {
	const body = await request.json();
	if (!Array.isArray(body.bets) || body.bets.length === 0) {
		return json({ error: "Place at least one bet" }, { status: 400 });
	}
	const bets: Bet[] = body.bets;
	for (const bet of bets) {
		if (
			typeof bet.amt !== "number" ||
			!Number.isFinite(bet.amt) ||
			bet.amt <= 0 ||
			typeof bet.numbers !== "string" ||
			typeof bet.odds !== "number"
		) {
			return json({ error: "Invalid bet entry" }, { status: 400 });
		}
	}

	const userId = locals.user?.id;
	if (!userId) return json({ error: "Not authenticated" }, { status: 401 });

	const totalBet = bets.reduce((s, b) => s + b.amt, 0);
	const coins = await locals.db.getCoins(userId);
	if (coins < totalBet)
		return json({ error: "Not enough coins" }, { status: 400 });

	const winningNumber = spinWheel();
	const totalWin = calculatePayouts(bets, winningNumber);

	await locals.db.deductCoins(userId, totalBet);
	if (totalWin > 0) {
		try {
			await locals.db.addCoins(userId, totalWin);
		} catch {
			await locals.db.addCoins(userId, totalBet);
			return json({ error: "Transaction failed" }, { status: 500 });
		}
	}

	const newCoins = await locals.db.getCoins(userId);
	return json({
		winning_number: winningNumber,
		total_bet: totalBet,
		total_win: totalWin,
		new_coins: newCoins,
	});
};
