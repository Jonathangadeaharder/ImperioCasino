import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { createDeck, shuffleDeck, calculateHandValue } from '$lib/server/games/blackjack';
import type { BlackjackState, Card } from '$lib/types';

export const POST: RequestHandler = async ({ request, locals }) => {
	const { wager } = await request.json();
	if (wager <= 0) return json({ error: 'Invalid wager' }, { status: 400 });

	const coins = await locals.db.getCoins(locals.user!.id);
	if (coins < wager) return json({ error: 'Not enough coins' }, { status: 400 });

	const deck = shuffleDeck(createDeck());
	const player_hand = [deck.pop() as Card, deck.pop() as Card];
	const dealer_hand = [deck.pop() as Card, deck.pop() as Card];
	const playerValue = calculateHandValue(player_hand);
	const dealerValue = calculateHandValue(dealer_hand);

	const state: BlackjackState = {
		user_id: locals.user!.id,
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
		current_hand: 'first',
		dealer_value: dealerValue
	};

	await locals.db.deductCoins(locals.user!.id, wager);
	const gameId = await locals.db.createBlackjackGame(locals.user!.id, state);

	return json({
		id: gameId,
		...state,
		deck: [],
		can_double_down: true,
		can_split: player_hand[0].value === player_hand[1].value
	});
};
