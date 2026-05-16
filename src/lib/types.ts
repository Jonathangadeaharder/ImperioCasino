export type Suit = 'Hearts' | 'Diamonds' | 'Clubs' | 'Spades';

export interface Card {
	suit: Suit;
	name: string;
	value: number;
}

export type Hand = Card[];

export type Deck = Card[];

export interface User {
	id: string;
	username: string;
	coins: number;
}

export interface BlackjackState {
	id?: string;
	user_id: string;
	deck: Deck;
	dealer_hand: Hand;
	player_hand: Hand;
	player_second_hand: Hand | null;
	player_coins: number;
	current_wager: number;
	game_over: boolean;
	message: string | null;
	player_stood: boolean;
	double_down: boolean;
	split: boolean;
	current_hand: 'first' | 'second';
	dealer_value: number;
}

export interface Bet {
	numbers: string;
	odds: number;
	amt: number;
}

export type Fruit = 'CHERRY' | 'LEMON' | 'BANANA' | 'APPLE';

export interface SpinResult {
	stop_segments: number[];
	fruits: [Fruit, Fruit, Fruit];
	payout: number;
}

export type GameAction = 'hit' | 'stand' | 'double' | 'split';
