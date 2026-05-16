import { describe, it, expect } from 'vitest';
import { spinReels, segmentToFruit, calculatePayout } from '../slots';
import type { Fruit } from '$lib/types';

describe('slots', () => {
	it('spinReels returns 3 segments between 15-30', () => {
		const segments = spinReels();
		expect(segments.length).toBe(3);
		for (const s of segments) {
			expect(s).toBeGreaterThanOrEqual(15);
			expect(s).toBeLessThanOrEqual(30);
		}
	});

	it('segmentToFruit maps known segments', () => {
		const fruit = segmentToFruit(0, 16);
		expect(typeof fruit).toBe('string');
	});

	it('calculatePayout returns 50 for 3 cherries', () => {
		expect(calculatePayout(['CHERRY', 'CHERRY', 'CHERRY'])).toBe(50);
	});

	it('calculatePayout returns 40 for 2 cherries on right', () => {
		expect(calculatePayout(['CHERRY', 'CHERRY', 'APPLE'])).toBe(40);
	});

	it('calculatePayout returns 20 for 3 apples', () => {
		expect(calculatePayout(['APPLE', 'APPLE', 'APPLE'])).toBe(20);
	});

	it('calculatePayout returns 10 for 2 apples', () => {
		expect(calculatePayout(['APPLE', 'APPLE', 'LEMON'])).toBe(10);
	});

	it('calculatePayout returns 15 for 3 bananas', () => {
		expect(calculatePayout(['BANANA', 'BANANA', 'BANANA'])).toBe(15);
	});

	it('calculatePayout returns 5 for 2 bananas', () => {
		expect(calculatePayout(['BANANA', 'BANANA', 'CHERRY'])).toBe(5);
	});

	it('calculatePayout returns 3 for 3 lemons', () => {
		expect(calculatePayout(['LEMON', 'LEMON', 'LEMON'])).toBe(3);
	});

	it('calculatePayout returns 0 for no match', () => {
		expect(calculatePayout(['LEMON', 'BANANA', 'APPLE'])).toBe(0);
	});
});
