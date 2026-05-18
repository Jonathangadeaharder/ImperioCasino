import { json } from "@sveltejs/kit";
import {
	calculateHandValue,
	createDeck,
	shuffleDeck,
} from "$lib/server/games/blackjack";
import type { BlackjackState } from "$lib/types";
import type { RequestHandler } from "./$types";

export const POST: RequestHandler = async ({ request, locals }) => {
	const { wager } = await request.json();
	if (wager <= 0) return json({ error: "Invalid wager" }, { status: 400 });

	const userId = locals.user?.id;
	if (!userId) return json({ error: "Not authenticated" }, { status: 401 });

	const coins = await locals.db.getCoins(userId);
	if (coins < wager)
		return json({ error: "Not enough coins" }, { status: 400 });

	const deck = shuffleDeck(createDeck());
	const c1 = deck.pop();
	const c2 = deck.pop();
	const c3 = deck.pop();
	const c4 = deck.pop();
	if (!c1 || !c2 || !c3 || !c4)
		return json({ error: "Deck error" }, { status: 500 });
	const player_hand = [c1, c2];
	const dealer_hand = [c3, c4];
	const _playerValue = calculateHandValue(player_hand);
	const dealerValue = calculateHandValue(dealer_hand);

	const state: BlackjackState = {
		user_id: userId,
		deck,
		dealer_hand,
		player_hand,
		player_second_hand: null,
		player_coins: coins - wager,
		current_wager: wager,
		game_over: false,
		message: null,
		player_stood: false,
		double_down: false,
		split: false,
		current_hand: "first",
		dealer_value: dealerValue,
	};

	await locals.db.deductCoins(userId, wager);
	const gameId = await locals.db.createBlackjackGame(userId, state);

	return json({
		id: gameId,
		...state,
		deck: [],
		can_double_down: false,
		can_split:
			player_hand[0].name === player_hand[1].name &&
			["Jack", "Queen", "King"].includes(player_hand[0].name) ===
				["Jack", "Queen", "King"].includes(player_hand[1].name),
	});
};
