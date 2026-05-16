import type { Bet } from '$lib/types';

export function spinWheel(): number {
	return Math.floor(Math.random() * 37);
}

export function calculatePayouts(bets: Bet[], winningNumber: number): number {
	let total = 0;
	for (const bet of bets) {
		const numbers = bet.numbers.split(',').map((n) => parseInt(n.trim(), 10));
		if (numbers.includes(winningNumber)) {
			total += bet.odds * bet.amt + bet.amt;
		}
	}
	return total;
}
