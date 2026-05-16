import { describe, it, expect } from 'vitest';
import { spinWheel, calculatePayouts } from '../roulette';
import type { Bet } from '$lib/types';

describe('roulette', () => {
	it('spinWheel returns 0-36', () => {
		for (let i = 0; i < 100; i++) {
			const result = spinWheel();
			expect(result).toBeGreaterThanOrEqual(0);
			expect(result).toBeLessThanOrEqual(36);
		}
	});

	it('calculatePayouts returns 0 for losing bet', () => {
		const bets: Bet[] = [{ numbers: '1,2,3', odds: 11, amt: 10 }];
		expect(calculatePayouts(bets, 0)).toBe(0);
	});

	it('calculatePayouts pays correctly for winning straight bet', () => {
		const bets: Bet[] = [{ numbers: '7', odds: 35, amt: 10 }];
		expect(calculatePayouts(bets, 7)).toBe(360); // 35 * 10 + 10
	});

	it('calculatePayouts handles multiple bets', () => {
		const bets: Bet[] = [
			{ numbers: '7', odds: 35, amt: 10 },
			{ numbers: '1,2,3', odds: 11, amt: 5 }
		];
		expect(calculatePayouts(bets, 7)).toBe(360); // only first wins
	});

	it('calculatePayouts returns 0 for empty bets', () => {
		expect(calculatePayouts([], 5)).toBe(0);
	});
});
