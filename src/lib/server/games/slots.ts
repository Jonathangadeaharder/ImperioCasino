import type { Fruit } from '$lib/types';

const SEGMENT_MAPS: Record<number, Record<number, Fruit>> = {
	0: { 8: 'CHERRY', 9: 'APPLE', 10: 'BANANA', 11: 'LEMON', 12: 'CHERRY', 13: 'APPLE', 14: 'BANANA', 15: 'LEMON' },
	1: { 8: 'APPLE', 9: 'CHERRY', 10: 'LEMON', 11: 'BANANA', 12: 'APPLE', 13: 'CHERRY', 14: 'LEMON', 15: 'BANANA' },
	2: { 8: 'BANANA', 9: 'LEMON', 10: 'CHERRY', 11: 'APPLE', 12: 'BANANA', 13: 'LEMON', 14: 'CHERRY', 15: 'APPLE' }
};

export function spinReels(): number[] {
	return [
		Math.floor(Math.random() * 16) + 15,
		Math.floor(Math.random() * 16) + 15,
		Math.floor(Math.random() * 16) + 15
	];
}

function ceildiv(a: number, b: number): number {
	return Math.ceil(a / b);
}

export function segmentToFruit(reelIndex: number, segment: number): Fruit {
	const mapped = ceildiv(segment, 2);
	const map = SEGMENT_MAPS[reelIndex];
	return map[mapped] ?? 'LEMON';
}

export function calculatePayout(fruits: Fruit[]): number {
	const [f0, f1, f2] = fruits;
	if (f0 === f1 && f1 === f2) {
		switch (f0) {
			case 'CHERRY': return 50;
			case 'APPLE': return 20;
			case 'BANANA': return 15;
			case 'LEMON': return 3;
		}
	}
	if (f0 === f1) {
		switch (f0) {
			case 'CHERRY': return 40;
			case 'APPLE': return 10;
			case 'BANANA': return 5;
			default: return 0;
		}
	}
	return 0;
}
