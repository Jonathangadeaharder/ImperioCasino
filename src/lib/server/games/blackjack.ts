import type { Card, Deck, Hand } from '$lib/types';

const SUITS: Card['suit'][] = ['Hearts', 'Diamonds', 'Clubs', 'Spades'];
const NAMES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace'];
const VALUES: Record<string, number> = {
	'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
	Jack: 10, Queen: 10, King: 10, Ace: 11
};

export function createDeck(): Deck {
	const deck: Deck = [];
	for (let d = 0; d < 6; d++) {
		for (const suit of SUITS) {
			for (const name of NAMES) {
				deck.push({ suit, name, value: VALUES[name] });
			}
		}
	}
	return deck;
}

export function shuffleDeck(deck: Deck): Deck {
	const d = [...deck];
	for (let i = d.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[d[i], d[j]] = [d[j], d[i]];
	}
	return d;
}

export function calculateHandValue(hand: Hand): number {
	let total = hand.reduce((sum, card) => sum + card.value, 0);
	let aces = hand.filter((c) => c.name === 'Ace').length;
	while (total > 21 && aces > 0) {
		total -= 10;
		aces--;
	}
	return total;
}

export function playerHit(hand: Hand, deck: Deck): { hand: Hand; deck: Deck; busted: boolean } {
	if (deck.length === 0) return { hand, deck, busted: calculateHandValue(hand) > 21 };
	const card = deck.pop() as Card;
	const newHand = [...hand, card];
	const busted = calculateHandValue(newHand) > 21;
	return { hand: newHand, deck, busted };
}

export function dealerTurn(deck: Deck, hand: Hand): { hand: Hand; deck: Deck } {
	let currentHand = [...hand];
	let currentDeck = [...deck];
	while (calculateHandValue(currentHand) < 17 && currentDeck.length > 0) {
		const card = currentDeck.pop() as Card;
		currentHand = [...currentHand, card];
	}
	return { hand: currentHand, deck: currentDeck };
}

export function compareHands(player: Hand, dealer: Hand): 'win' | 'lose' | 'tie' {
	const pv = calculateHandValue(player);
	const dv = calculateHandValue(dealer);
	if (pv > 21) return 'lose';
	if (dv > 21) return 'win';
	if (pv > dv) return 'win';
	if (pv < dv) return 'lose';
	return 'tie';
}

export function determineWinner(player: Hand, dealer: Hand): 'win' | 'lose' | 'tie' {
	return compareHands(player, dealer);
}
