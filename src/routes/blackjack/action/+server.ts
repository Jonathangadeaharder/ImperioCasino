import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { playerHit, dealerTurn, determineWinner, calculateHandValue } from '$lib/server/games/blackjack';
import type { BlackjackState, GameAction } from '$lib/types';

export const POST: RequestHandler = async ({ request, locals }) => {
	const { action, game_id } = await request.json() as { action: GameAction; game_id: string };
	const state = await locals.db.getBlackjackGame(game_id);
	if (state.game_over) return json({ error: 'Game already over' }, { status: 400 });

	if (action === 'hit') {
		const result = playerHit(state.player_hand, state.deck);
		state.player_hand = result.hand;
		state.deck = result.deck;
		if (result.busted) {
			state.game_over = true;
			state.message = 'Bust! You lose.';
		}
	} else if (action === 'stand') {
		state.player_stood = true;
		const dealer = dealerTurn(state.deck, state.dealer_hand);
		state.dealer_hand = dealer.hand;
		state.deck = dealer.deck;
		state.dealer_value = calculateHandValue(state.dealer_hand);
		state.game_over = true;
		const winner = determineWinner(state.player_hand, state.dealer_hand);
		state.message = winner === 'win' ? 'You win!' : winner === 'tie' ? 'Push!' : 'Dealer wins.';
		if (winner === 'win') await locals.db.addCoins(locals.user!.id, state.current_wager * 2);
		else if (winner === 'tie') await locals.db.addCoins(locals.user!.id, state.current_wager);
	} else if (action === 'double') {
		await locals.db.deductCoins(locals.user!.id, state.current_wager);
		state.player_coins -= state.current_wager;
		state.current_wager *= 2;
		const result = playerHit(state.player_hand, state.deck);
		state.player_hand = result.hand;
		state.deck = result.deck;
		const dealer = dealerTurn(state.deck, state.dealer_hand);
		state.dealer_hand = dealer.hand;
		state.deck = dealer.deck;
		state.dealer_value = calculateHandValue(state.dealer_hand);
		state.game_over = true;
		const winner = determineWinner(state.player_hand, state.dealer_hand);
		state.message = winner === 'win' ? 'You win!' : winner === 'tie' ? 'Push!' : 'Dealer wins.';
		if (winner === 'win') await locals.db.addCoins(locals.user!.id, state.current_wager * 2);
		else if (winner === 'tie') await locals.db.addCoins(locals.user!.id, state.current_wager);
	}

	state.dealer_value = calculateHandValue(state.dealer_hand);
	await locals.db.updateBlackjackGame(game_id, state);
	const player_coins = await locals.db.getCoins(locals.user!.id);
	const canSplit = !state.split && state.player_hand.length === 2 && state.player_hand[0].value === state.player_hand[1].value;

	return json({
		...state,
		player_coins,
		can_double_down: action !== 'double' && state.player_hand.length === 2 && !state.split,
		can_split: canSplit
	});
};
