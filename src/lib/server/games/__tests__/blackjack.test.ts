import { describe, it, expect } from 'vitest';
import { createDeck, calculateHandValue, playerHit, dealerTurn, determineWinner, compareHands } from '../blackjack';
import type { Card, Hand } from '$lib/types';

function makeCard(name: string, value: number, suit: 'Hearts' | 'Spades' | 'Diamonds' | 'Clubs' = 'Hearts'): Card {
	return { suit, name, value };
}

describe('blackjack', () => {
	it('createDeck returns 312 cards (6 decks)', () => {
		const deck = createDeck();
		expect(deck.length).toBe(312);
	});

	it('calculateHandValue sums card values', () => {
		const hand: Hand = [makeCard('5', 5), makeCard('K', 10)];
		expect(calculateHandValue(hand)).toBe(15);
	});

	it('calculateHandValue counts Ace as 11 when under 21', () => {
		const hand: Hand = [makeCard('Ace', 11), makeCard('7', 7)];
		expect(calculateHandValue(hand)).toBe(18);
	});

	it('calculateHandValue counts Ace as 1 when 11 would bust', () => {
		const hand: Hand = [makeCard('Ace', 11), makeCard('7', 7), makeCard('8', 8)];
		expect(calculateHandValue(hand)).toBe(16);
	});

	it('calculateHandValue handles multiple Aces', () => {
		const hand: Hand = [makeCard('Ace', 11), makeCard('Ace', 11), makeCard('9', 9)];
		expect(calculateHandValue(hand)).toBe(21);
	});

	it('playerHit adds card to hand and pops from deck', () => {
		const deck = [makeCard('K', 10), makeCard('5', 5)];
		const hand: Hand = [makeCard('Ace', 11)];
		const result = playerHit(hand, deck);
		expect(result.hand.length).toBe(2);
		expect(result.deck.length).toBe(1);
		expect(result.busted).toBe(false);
	});

	it('playerHit detects bust', () => {
		const deck = [makeCard('K', 10)];
		const hand: Hand = [makeCard('K', 10), makeCard('Q', 10)];
		const result = playerHit(hand, deck);
		expect(result.busted).toBe(true);
	});

	it('dealerTurn hits until >= 17', () => {
		const deck = [makeCard('K', 10), makeCard('5', 5), makeCard('3', 3)];
		const hand: Hand = [makeCard('10', 10), makeCard('5', 5)];
		const result = dealerTurn(deck, hand);
		expect(calculateHandValue(result.hand)).toBeGreaterThanOrEqual(17);
	});

	it('dealerTurn stands on 17', () => {
		const deck = [makeCard('K', 10)];
		const hand: Hand = [makeCard('10', 10), makeCard('7', 7)];
		const result = dealerTurn(deck, hand);
		expect(result.hand.length).toBe(2);
	});

	it('determineWinner returns win when player > dealer', () => {
		const dealer: Hand = [makeCard('K', 10), makeCard('5', 5)];
		const player: Hand = [makeCard('K', 10), makeCard('9', 9)];
		expect(determineWinner(player, dealer)).toBe('win');
	});

	it('determineWinner returns lose when player busts', () => {
		const dealer: Hand = [makeCard('K', 10), makeCard('5', 5)];
		const player: Hand = [makeCard('K', 10), makeCard('7', 7), makeCard('8', 8)];
		expect(determineWinner(player, dealer)).toBe('lose');
	});

	it('determineWinner returns tie when equal value', () => {
		const dealer: Hand = [makeCard('K', 10), makeCard('7', 7)];
		const player: Hand = [makeCard('Q', 10), makeCard('7', 7)];
		expect(determineWinner(player, dealer)).toBe('tie');
	});

	it('determineWinner returns lose when dealer > player (no bust)', () => {
		const dealer: Hand = [makeCard('K', 10), makeCard('9', 9)];
		const player: Hand = [makeCard('K', 10), makeCard('5', 5)];
		expect(determineWinner(player, dealer)).toBe('lose');
	});

	it('determineWinner returns win when dealer busts', () => {
		const dealer: Hand = [makeCard('K', 10), makeCard('7', 7), makeCard('8', 8)];
		const player: Hand = [makeCard('K', 10), makeCard('5', 5)];
		expect(determineWinner(player, dealer)).toBe('win');
	});

	it('compareHands returns lose for player bust', () => {
		const player: Hand = [makeCard('K', 10), makeCard('Q', 10), makeCard('5', 5)];
		const dealer: Hand = [makeCard('K', 10), makeCard('5', 5)];
		expect(compareHands(player, dealer)).toBe('lose');
	});

	it('compareHands returns win for dealer bust', () => {
		const player: Hand = [makeCard('K', 10), makeCard('5', 5)];
		const dealer: Hand = [makeCard('K', 10), makeCard('Q', 10), makeCard('5', 5)];
		expect(compareHands(player, dealer)).toBe('win');
	});
});
