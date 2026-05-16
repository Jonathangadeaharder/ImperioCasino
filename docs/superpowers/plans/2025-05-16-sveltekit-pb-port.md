# ImperioCasino SvelteKit + PocketBase Port — Implementation Plan

> **Sub-Skills:** subagent-driven-development or executing-plans. Steps use `- [ ]` syntax.

**Goal:** Replace Flask + React/jQuery casino stack with single SvelteKit app + PocketBase Go binary

**Architecture:** SvelteKit monolith with game logic in server endpoints, DB abstraction layer, Threlte for 3D slot. PocketBase handles auth + storage.

**Tech Stack:** Svelte 5, SvelteKit, PocketBase, Threlte, Vitest, pnpm, TypeScript

---

## File Map

| Path | Purpose |
|------|---------|
| `package.json` | SvelteKit + deps |
| `svelte.config.js` | Adapter auto |
| `vite.config.ts` | Vitest config |
| `tsconfig.json` | TS config |
| `src/app.html` | HTML shell |
| `src/app.css` | Global styles |
| `src/hooks.server.ts` | PocketBase per-request |
| `src/lib/types.ts` | Shared types |
| `src/lib/server/db/adapter.ts` | DBAdapter interface |
| `src/lib/server/db/pocketbase.ts` | PocketBase implementation |
| `src/lib/server/games/blackjack.ts` | Blackjack logic |
| `src/lib/server/games/roulette.ts` | Roulette logic |
| `src/lib/server/games/slots.ts` | Slots logic |
| `src/lib/server/auth.ts` | Auth actions |
| `src/routes/+layout.svelte` | App shell |
| `src/routes/+layout.server.ts` | Auth guard |
| `src/routes/+page.svelte` | Lobby |
| `src/routes/login/+page.svelte` | Login |
| `src/routes/login/+page.server.ts` | Login action |
| `src/routes/signup/+page.svelte` | Signup |
| `src/routes/signup/+page.server.ts` | Signup action |
| `src/routes/logout/+page.server.ts` | Logout |
| `src/routes/blackjack/+page.svelte` | Blackjack page |
| `src/routes/blackjack/+page.server.ts` | Blackjack server load |
| `src/routes/blackjack/start/+server.ts` | Start game |
| `src/routes/blackjack/action/+server.ts` | Hit/stand/double/split |
| `src/routes/roulette/+page.svelte` | Roulette page |
| `src/routes/roulette/+page.server.ts` | Roulette server load |
| `src/routes/roulette/spin/+server.ts` | Place bets + spin |
| `src/routes/slots/+page.svelte` | Slots page |
| `src/routes/slots/+page.server.ts` | Slots server load |
| `src/routes/slots/spin/+server.ts` | Spin reels |
| `src/lib/components/Nav.svelte` | Navigation |
| `src/lib/components/CoinBalance.svelte` | Coin display |
| `src/lib/components/Card.svelte` | Card display |
| `src/lib/components/ChipSelector.svelte` | Chip picker |
| `src/lib/components/BlackjackBoard.svelte` | Blackjack table |
| `src/lib/components/RouletteTable.svelte` | Betting grid |
| `src/lib/components/RouletteWheel.svelte` | Wheel animation |
| `src/lib/components/SlotMachine.svelte` | Threlte slot |
| `src/lib/components/Reel.svelte` | Threlte reel |
| `src/lib/components/ResultModal.svelte` | Win/loss modal |

---

### Task 1: Scaffold SvelteKit project

**Files:**
- Create: `package.json`
- Create: `svelte.config.js`
- Create: `vite.config.ts`
- Create: `tsconfig.json`
- Create: `src/app.html`
- Create: `src/app.css`

- [ ] **Step 1: Create SvelteKit project**

```bash
cd /Users/jonathangadeaharder/projects/ImperioCasino
pnpm create @sveltejs/kit@latest . -- --template minimal --types typescript --no-add-ons
```

When prompted: "Skeleton project", TypeScript, no ESLint/Prettier (biome handles), Playwright.

- [ ] **Step 2: Install dependencies**

```bash
pnpm add pocketbase threlte @threlte/core @threlte/extras three
pnpm add -D @types/three vitest @sveltejs/vite-plugin-svelte
```

- [ ] **Step 3: Configure `svelte.config.js`**

```js
import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

const config = {
	preprocess: vitePreprocess(),
	kit: { adapter: adapter() }
};

export default config;
```

- [ ] **Step 4: Configure `vite.config.ts` for Vitest**

```ts
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit()],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}']
	}
});
```

- [ ] **Step 5: Write `src/app.html`**

```html
<!doctype html>
<html lang="en">
	<head>
		<meta charset="utf-8" />
		<meta name="viewport" content="width=device-width, initial-scale=1" />
		<link rel="icon" href="%sveltekit.assets%/favicon.png" />
		%sveltekit.head%
	</head>
	<body>
		<div style="display: contents">%sveltekit.body%</div>
	</body>
</html>
```

- [ ] **Step 6: Verify scaffold builds**

```bash
pnpm run build
```

Expected: Build succeeds, `.svelte-kit/` directory created.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: scaffold SvelteKit project"
```

---

### Task 2: Write shared types

**Files:**
- Create: `src/lib/types.ts`

- [ ] **Step 1: Write `src/lib/types.ts`**

```ts
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
```

- [ ] **Step 2: Commit**

```bash
git add src/lib/types.ts && git commit -m "feat: add shared types"
```

---

### Task 3: Write DB adapter interface + PocketBase implementation

**Files:**
- Create: `src/lib/server/db/adapter.ts`
- Create: `src/lib/server/db/pocketbase.ts`

- [ ] **Step 1: Write `src/lib/server/db/adapter.ts`**

```ts
import type { User, BlackjackState } from '$lib/types';

export interface DBAdapter {
	getUser(id: string): Promise<User>;
	getUserByUsername(username: string): Promise<User | null>;
	getCoins(userId: string): Promise<number>;
	addCoins(userId: string, amount: number): Promise<number>;
	deductCoins(userId: string, amount: number): Promise<number>;
	setCoins(userId: string, amount: number): Promise<number>;
	createBlackjackGame(userId: string, state: BlackjackState): Promise<string>;
	updateBlackjackGame(gameId: string, state: Partial<BlackjackState>): Promise<void>;
	getBlackjackGame(gameId: string): Promise<BlackjackState>;
}
```

- [ ] **Step 2: Write `src/lib/server/db/pocketbase.ts`**

```ts
import PocketBase from 'pocketbase';
import type { DBAdapter } from './adapter';
import type { User, BlackjackState } from '$lib/types';

export class PocketBaseAdapter implements DBAdapter {
	constructor(private pb: PocketBase) {}

	async getUser(id: string): Promise<User> {
		const record = await this.pb.collection('users').getOne(id);
		return { id: record.id, username: record.username, coins: record.coins };
	}

	async getUserByUsername(username: string): Promise<User | null> {
		try {
			const records = await this.pb.collection('users').getList(1, 1, {
				filter: `username = "${username}"`
			});
			if (records.items.length === 0) return null;
			const r = records.items[0];
			return { id: r.id, username: r.username, coins: r.coins };
		} catch {
			return null;
		}
	}

	async getCoins(userId: string): Promise<number> {
		const record = await this.pb.collection('users').getOne(userId);
		return record.coins;
	}

	async addCoins(userId: string, amount: number): Promise<number> {
		const record = await this.pb.collection('users').getOne(userId);
		const newCoins = record.coins + amount;
		await this.pb.collection('users').update(userId, { coins: newCoins });
		return newCoins;
	}

	async deductCoins(userId: string, amount: number): Promise<number> {
		const record = await this.pb.collection('users').getOne(userId);
		const newCoins = Math.max(0, record.coins - amount);
		await this.pb.collection('users').update(userId, { coins: newCoins });
		return newCoins;
	}

	async setCoins(userId: string, amount: number): Promise<number> {
		await this.pb.collection('users').update(userId, { coins: amount });
		return amount;
	}

	async createBlackjackGame(userId: string, state: BlackjackState): Promise<string> {
		const record = await this.pb.collection('blackjack_games').create({
			user: userId,
			deck: JSON.stringify(state.deck),
			dealer_hand: JSON.stringify(state.dealer_hand),
			player_hand: JSON.stringify(state.player_hand),
			player_second_hand: state.player_second_hand ? JSON.stringify(state.player_second_hand) : null,
			player_coins: state.player_coins,
			current_wager: state.current_wager,
			game_over: state.game_over,
			message: state.message,
			player_stood: state.player_stood,
			double_down: state.double_down,
			split: state.split,
			current_hand: state.current_hand,
			dealer_value: state.dealer_value
		});
		return record.id;
	}

	async updateBlackjackGame(gameId: string, state: Partial<BlackjackState>): Promise<void> {
		const data: Record<string, unknown> = {};
		if (state.deck !== undefined) data.deck = JSON.stringify(state.deck);
		if (state.dealer_hand !== undefined) data.dealer_hand = JSON.stringify(state.dealer_hand);
		if (state.player_hand !== undefined) data.player_hand = JSON.stringify(state.player_hand);
		if (state.player_second_hand !== undefined) data.player_second_hand = state.player_second_hand ? JSON.stringify(state.player_second_hand) : null;
		if (state.player_coins !== undefined) data.player_coins = state.player_coins;
		if (state.current_wager !== undefined) data.current_wager = state.current_wager;
		if (state.game_over !== undefined) data.game_over = state.game_over;
		if (state.message !== undefined) data.message = state.message;
		if (state.player_stood !== undefined) data.player_stood = state.player_stood;
		if (state.double_down !== undefined) data.double_down = state.double_down;
		if (state.split !== undefined) data.split = state.split;
		if (state.current_hand !== undefined) data.current_hand = state.current_hand;
		if (state.dealer_value !== undefined) data.dealer_value = state.dealer_value;
		await this.pb.collection('blackjack_games').update(gameId, data);
	}

	async getBlackjackGame(gameId: string): Promise<BlackjackState> {
		const record = await this.pb.collection('blackjack_games').getOne(gameId, {
			expand: 'user'
		});
		return {
			id: record.id,
			user_id: record.user,
			deck: JSON.parse(record.deck),
			dealer_hand: JSON.parse(record.dealer_hand),
			player_hand: JSON.parse(record.player_hand),
			player_second_hand: record.player_second_hand ? JSON.parse(record.player_second_hand) : null,
			player_coins: record.player_coins,
			current_wager: record.current_wager,
			game_over: record.game_over,
			message: record.message,
			player_stood: record.player_stood,
			double_down: record.double_down,
			split: record.split,
			current_hand: record.current_hand,
			dealer_value: record.dealer_value
		};
	}
}
```

- [ ] **Step 3: Commit**

```bash
git add src/lib/server/db/ && git commit -m "feat: add DB adapter interface + PocketBase implementation"
```

---

### Task 4: Write blackjack game logic (TypeScript port)

**Files:**
- Create: `src/lib/server/games/blackjack.ts`
- Create: `src/lib/server/games/__tests__/blackjack.test.ts`

- [ ] **Step 1: Write test for blackjack game logic**

```ts
import { describe, it, expect } from 'vitest';
import { createDeck, calculateHandValue, playerHit, determineWinner } from '../games/blackjack';
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
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run src/lib/server/games/__tests__/blackjack.test.ts
```

Expected: FAIL — import errors

- [ ] **Step 3: Write `src/lib/server/games/blackjack.ts`**

```ts
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
	const card = deck.pop()!;
	const newHand = [...hand, card];
	const busted = calculateHandValue(newHand) > 21;
	return { hand: newHand, deck, busted };
}

export function dealerTurn(deck: Deck, hand: Hand): { hand: Hand; deck: Deck } {
	let currentHand = [...hand];
	while (calculateHandValue(currentHand) < 17) {
		const card = deck.pop()!;
		currentHand = [...currentHand, card];
	}
	return { hand: currentHand, deck };
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run src/lib/server/games/__tests__/blackjack.test.ts
```

Expected: All tests PASS

- [ ] **Step 5: Write remaining blackjack tests (split, double down, dealer edge cases)**

```ts
// Add to blackjack.test.ts
import { describe, it, expect } from 'vitest';
import { createDeck, calculateHandValue, playerHit, dealerTurn, determineWinner, compareHands } from '../games/blackjack';
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
```

- [ ] **Step 6: Run all blackjack tests**

```bash
npx vitest run src/lib/server/games/__tests__/blackjack.test.ts
```

Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add src/lib/server/games/blackjack.ts src/lib/server/games/__tests__/blackjack.test.ts && git commit -m "feat: port blackjack game logic to TypeScript"
```

---

### Task 5: Write roulette game logic

**Files:**
- Create: `src/lib/server/games/roulette.ts`
- Create: `src/lib/server/games/__tests__/roulette.test.ts`

- [ ] **Step 1: Write roulette test**

```ts
import { describe, it, expect } from 'vitest';
import { spinWheel, calculatePayouts } from '../games/roulette';
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run src/lib/server/games/__tests__/roulette.test.ts
```

Expected: FAIL

- [ ] **Step 3: Write `src/lib/server/games/roulette.ts`**

```ts
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run src/lib/server/games/__tests__/roulette.test.ts
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/server/games/roulette.ts src/lib/server/games/__tests__/roulette.test.ts && git commit -m "feat: port roulette game logic to TypeScript"
```

---

### Task 6: Write slots game logic

**Files:**
- Create: `src/lib/server/games/slots.ts`
- Create: `src/lib/server/games/__tests__/slots.test.ts`

- [ ] **Step 1: Write slots test**

```ts
import { describe, it, expect } from 'vitest';
import { spinReels, segmentToFruit, calculatePayout } from '../games/slots';
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run src/lib/server/games/__tests__/slots.test.ts
```

Expected: FAIL

- [ ] **Step 3: Write `src/lib/server/games/slots.ts`**

```ts
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run src/lib/server/games/__tests__/slots.test.ts
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/server/games/slots.ts src/lib/server/games/__tests__/slots.test.ts && git commit -m "feat: port slots game logic to TypeScript"
```

---

### Task 7: Auth hooks + auth helpers

**Files:**
- Create: `src/hooks.server.ts`
- Create: `src/lib/server/auth.ts`

- [ ] **Step 1: Write `src/hooks.server.ts`**

```ts
import PocketBase from 'pocketbase';
import { building } from '$app/environment';
import type { Handle } from '@sveltejs/kit';
import { PocketBaseAdapter } from '$lib/server/db/pocketbase';

export const handle: Handle = async ({ event, resolve }) => {
	if (building) return resolve(event);

	const pb = new PocketBase('http://127.0.0.1:8090');
	event.locals.pb = pb;
	event.locals.db = new PocketBaseAdapter(pb);

	const authCookie = event.request.headers.get('cookie') || '';
	pb.authStore.loadFromCookie(authCookie);

	try {
		if (pb.authStore.isValid) {
			await pb.collection('users').authRefresh();
		}
	} catch {
		pb.authStore.clear();
	}

	event.locals.user = pb.authStore.isValid
		? { id: pb.authStore.model!.id, username: pb.authStore.model!.username, coins: pb.authStore.model!.coins }
		: null;

	const response = await resolve(event);
	response.headers.set('set-cookie', pb.authStore.exportToCookie({ httpOnly: false }));
	return response;
};
```

- [ ] **Step 2: Add Locals type declaration in `src/app.d.ts`**

```ts
import type PocketBase from 'pocketbase';
import type { PocketBaseAdapter } from '$lib/server/db/pocketbase';
import type { User } from '$lib/types';

declare global {
	namespace App {
		interface Locals {
			pb: PocketBase;
			db: PocketBaseAdapter;
			user: User | null;
		}
	}
}

export {};
```

- [ ] **Step 3: Write `src/lib/server/auth.ts`**

```ts
import PocketBase from 'pocketbase';
import type { User } from '$lib/types';

export async function signup(pb: PocketBase, username: string, email: string, password: string): Promise<User> {
	const record = await pb.collection('users').create({
		username,
		email,
		password,
		passwordConfirm: password,
		coins: 100
	});
	await pb.collection('users').authWithPassword(email, password);
	return { id: record.id, username: record.username, coins: record.coins };
}

export async function login(pb: PocketBase, email: string, password: string): Promise<User> {
	const result = await pb.collection('users').authWithPassword(email, password);
	return { id: result.record.id, username: result.record.username, coins: result.record.coins };
}
```

- [ ] **Step 4: Commit**

```bash
git add src/hooks.server.ts src/app.d.ts src/lib/server/auth.ts && git commit -m "feat: add auth hooks + helpers"
```

---

### Task 8: Login, signup, logout, and auth guard routes

**Files:**
- Create: `src/routes/+layout.server.ts`
- Create: `src/routes/+layout.svelte`
- Create: `src/routes/login/+page.svelte`
- Create: `src/routes/login/+page.server.ts`
- Create: `src/routes/signup/+page.svelte`
- Create: `src/routes/signup/+page.server.ts`
- Create: `src/routes/logout/+page.server.ts`

- [ ] **Step 1: Write `src/routes/+layout.server.ts`**

```ts
import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals, url }) => {
	const publicPaths = ['/login', '/signup'];
	if (!locals.user && !publicPaths.includes(url.pathname)) {
		redirect(303, '/login');
	}
	return { user: locals.user };
};
```

- [ ] **Step 2: Write `src/routes/+layout.svelte`**

```svelte
<script lang="ts">
	import { page } from '$app/stores';
	import Nav from '$lib/components/Nav.svelte';
	let { children } = $props();
</script>

<Nav />
<main>
	{@render children()}
</main>

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		background: #0a0a0f;
		color: #e0e0e0;
	}
	main {
		max-width: 1200px;
		margin: 0 auto;
		padding: 1rem;
	}
</style>
```

- [ ] **Step 3: Write `src/lib/components/Nav.svelte`**

```svelte
<script lang="ts">
	import { page } from '$app/stores';
	import CoinBalance from './CoinBalance.svelte';
	let user = $derived($page.data.user);
</script>

<nav>
	<a href="/">ImperioCasino</a>
	<div class="links">
		<a href="/blackjack">Blackjack</a>
		<a href="/roulette">Roulette</a>
		<a href="/slots">Slots</a>
	</div>
	{#if user}
		<CoinBalance />
		<a href="/logout">Logout</a>
	{/if}
</nav>

<style>
	nav {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		padding: 0.75rem 1.5rem;
		background: #1a1a2e;
		border-bottom: 1px solid #2a2a4e;
	}
	nav > a:first-child {
		font-weight: 700;
		font-size: 1.2rem;
		color: #ffd700;
		text-decoration: none;
	}
	.links { display: flex; gap: 1rem; flex: 1; }
	.links a { color: #a0a0c0; text-decoration: none; }
	.links a:hover { color: #fff; }
</style>
```

- [ ] **Step 4: Write `src/lib/components/CoinBalance.svelte`**

```svelte
<script lang="ts">
	import { page } from '$app/stores';
	let coins = $derived($page.data.user?.coins ?? 0);
</script>

<span class="coins">🪙 {coins}</span>

<style>
	.coins {
		font-weight: 600;
		color: #ffd700;
	}
</style>
```

- [ ] **Step 5: Write `src/routes/login/+page.server.ts`**

```ts
import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	if (locals.user) redirect(303, '/');
	return {};
};

export const actions: Actions = {
	default: async ({ request, locals }) => {
		const data = await request.formData();
		const email = data.get('email') as string;
		const password = data.get('password') as string;

		if (!email || !password) return fail(400, { error: 'Email and password required' });

		try {
			await locals.pb.collection('users').authWithPassword(email, password);
		} catch {
			return fail(401, { error: 'Invalid credentials' });
		}
		redirect(303, '/');
	}
};
```

- [ ] **Step 6: Write `src/routes/login/+page.svelte`**

```svelte
<script lang="ts">
	let { form } = $props();
</script>

<h1>Login</h1>
<form method="POST">
	{#if form?.error}<p class="error">{form.error}</p>{/if}
	<label>Email <input type="email" name="email" required /></label>
	<label>Password <input type="password" name="password" required /></label>
	<button type="submit">Login</button>
	<p><a href="/signup">Create account</a></p>
</form>

<style>
	h1 { text-align: center; margin-top: 3rem; color: #ffd700; }
	form { max-width: 320px; margin: 2rem auto; display: flex; flex-direction: column; gap: 1rem; }
	label { display: flex; flex-direction: column; gap: 0.25rem; color: #a0a0c0; }
	input { padding: 0.5rem; border: 1px solid #333; border-radius: 4px; background: #1a1a2e; color: #e0e0e0; }
	button { padding: 0.6rem; background: #ffd700; color: #000; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }
	.error { color: #ff4444; text-align: center; }
	a { color: #88aaff; }
</style>
```

- [ ] **Step 7: Write `src/routes/signup/+page.server.ts`**

```ts
import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	if (locals.user) redirect(303, '/');
	return {};
};

export const actions: Actions = {
	default: async ({ request, locals }) => {
		const data = await request.formData();
		const username = data.get('username') as string;
		const email = data.get('email') as string;
		const password = data.get('password') as string;

		if (!username || !email || !password) return fail(400, { error: 'All fields required' });

		try {
			await locals.pb.collection('users').create({
				username, email, password, passwordConfirm: password, coins: 100
			});
			await locals.pb.collection('users').authWithPassword(email, password);
		} catch (e: unknown) {
			const msg = e instanceof Error ? e.message : 'Registration failed';
			return fail(400, { error: msg });
		}
		redirect(303, '/');
	}
};
```

- [ ] **Step 8: Write `src/routes/signup/+page.svelte`**

```svelte
<script lang="ts">
	let { form } = $props();
</script>

<h1>Sign Up</h1>
<form method="POST">
	{#if form?.error}<p class="error">{form.error}</p>{/if}
	<label>Username <input type="text" name="username" required /></label>
	<label>Email <input type="email" name="email" required /></label>
	<label>Password <input type="password" name="password" required /></label>
	<button type="submit">Create Account</button>
	<p><a href="/login">Already have an account?</a></p>
</form>

<style>
	h1 { text-align: center; margin-top: 3rem; color: #ffd700; }
	form { max-width: 320px; margin: 2rem auto; display: flex; flex-direction: column; gap: 1rem; }
	label { display: flex; flex-direction: column; gap: 0.25rem; color: #a0a0c0; }
	input { padding: 0.5rem; border: 1px solid #333; border-radius: 4px; background: #1a1a2e; color: #e0e0e0; }
	button { padding: 0.6rem; background: #ffd700; color: #000; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }
	.error { color: #ff4444; text-align: center; }
	a { color: #88aaff; }
</style>
```

- [ ] **Step 9: Write `src/routes/logout/+page.server.ts`**

```ts
import { redirect } from '@sveltejs/kit';
import type { Actions } from './$types';

export const actions: Actions = {
	default: async ({ locals }) => {
		locals.pb.authStore.clear();
		redirect(303, '/login');
	}
};

export const load = async () => {
	redirect(303, '/login');
};
```

- [ ] **Step 10: Commit**

```bash
git add src/routes/+layout.server.ts src/routes/+layout.svelte src/routes/login/ src/routes/signup/ src/routes/logout/ src/lib/components/Nav.svelte src/lib/components/CoinBalance.svelte && git commit -m "feat: add auth routes (login, signup, logout) + layout"
```

---

### Task 9: Lobby/dashboard page

**Files:**
- Create: `src/routes/+page.svelte`

- [ ] **Step 1: Write `src/routes/+page.svelte`**

```svelte
<script lang="ts">
	import { page } from '$app/stores';
	let user = $derived($page.data.user);
</script>

<h1>Welcome{user ? `, ${user.username}` : ''}</h1>
<p class="subtitle">Choose your game</p>

<div class="games">
	<a href="/blackjack" class="card blackjack">
		<h2>♠ Blackjack</h2>
		<p>Beat the dealer. Hit, stand, double down, split.</p>
	</a>
	<a href="/roulette" class="card roulette">
		<h2>🔴 Roulette</h2>
		<p>Place your bets. Spin the wheel.</p>
	</a>
	<a href="/slots" class="card slots">
		<h2>🍒 Slots</h2>
		<p>3D slot machine. Match 3 to win big.</p>
	</a>
</div>

<style>
	h1 { text-align: center; margin-top: 3rem; color: #ffd700; font-size: 2rem; }
	.subtitle { text-align: center; color: #888; margin-bottom: 2rem; }
	.games { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; max-width: 960px; margin: 0 auto; }
	.card { display: block; padding: 2rem; border-radius: 12px; text-decoration: none; color: #e0e0e0; border: 1px solid #333; transition: transform 0.2s, border-color 0.2s; }
	.card:hover { transform: translateY(-4px); }
	.card h2 { margin: 0 0 0.5rem; }
	.card p { margin: 0; color: #888; font-size: 0.9rem; }
	.blackjack:hover { border-color: #4caf50; }
	.roulette:hover { border-color: #ff4444; }
	.slots:hover { border-color: #ffd700; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add src/routes/+page.svelte && git commit -m "feat: add lobby/dashboard"
```

---

### Task 10: Blackjack routes + frontend

**Files:**
- Create: `src/routes/blackjack/+page.svelte`
- Create: `src/routes/blackjack/+page.server.ts`
- Create: `src/routes/blackjack/start/+server.ts`
- Create: `src/routes/blackjack/action/+server.ts`
- Create: `src/lib/components/Card.svelte`
- Create: `src/lib/components/ChipSelector.svelte`
- Create: `src/lib/components/BlackjackBoard.svelte`
- Create: `src/lib/components/ResultModal.svelte`

- [ ] **Step 1: Write `src/lib/components/Card.svelte`**

```svelte
<script lang="ts">
	import type { Card as CardType } from '$lib/types';
	let { card, hidden = false }: { card: CardType; hidden?: boolean } = $props();
</script>

<div class="card {hidden ? 'hidden' : ''}">
	{#if hidden}
		<span class="back">?</span>
	{:else}
		<span class="suit" style="color: {card.suit === 'Hearts' || card.suit === 'Diamonds' ? '#ff4444' : '#e0e0e0'}">
			{card.suit === 'Hearts' ? '♥' : card.suit === 'Diamonds' ? '♦' : card.suit === 'Clubs' ? '♣' : '♠'}
		</span>
		<span class="name">{card.name}</span>
	{/if}
</div>

<style>
	.card {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		width: 60px;
		height: 84px;
		border: 2px solid #555;
		border-radius: 8px;
		background: #1a1a2e;
		margin: 0 4px;
		font-size: 0.85rem;
	}
	.card.hidden { background: #2a1a4e; border-color: #6a3aae; }
	.back { font-size: 1.5rem; color: #6a3aae; }
	.suit { font-size: 1.2rem; }
	.name { font-weight: 600; font-size: 1rem; }
</style>
```

- [ ] **Step 2: Write `src/lib/components/ChipSelector.svelte`**

```svelte
<script lang="ts">
	let { wager, setWager, max, disabled = false }: {
		wager: number;
		setWager: (n: number) => void;
		max: number;
		disabled?: boolean;
	} = $props();

	const chips = [10, 25, 50, 100];
</script>

<div class="chips">
	{#each chips as chip}
		<button
			class:selected={wager === chip}
			disabled={disabled || chip > max}
			onclick={() => setWager(chip)}
		>
			{chip}
		</button>
	{/each}
</div>

<style>
	.chips { display: flex; gap: 0.5rem; }
	button {
		padding: 0.5rem 1rem;
		border: 2px solid #ffd700;
		border-radius: 50%;
		background: transparent;
		color: #ffd700;
		font-weight: 600;
		cursor: pointer;
		min-width: 48px;
		min-height: 48px;
	}
	button:disabled { opacity: 0.4; cursor: not-allowed; }
	button.selected { background: #ffd700; color: #000; }
</style>
```

- [ ] **Step 3: Write `src/lib/components/ResultModal.svelte`**

```svelte
<script lang="ts">
	let { show, message, payout }: { show: boolean; message: string | null; payout: number } = $props();
</script>

{#if show}
	<div class="overlay">
		<div class="modal">
			<h2 class:win={payout > 0} class:lose={payout === 0}>{message}</h2>
			<p>{payout > 0 ? `You won ${payout} coins!` : 'Better luck next time.'}</p>
			<a href="/blackjack" class="btn">Play Again</a>
		</div>
	</div>
{/if}

<style>
	.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; }
	.modal { background: #1a1a2e; padding: 2rem; border-radius: 12px; text-align: center; border: 1px solid #333; }
	.win { color: #4caf50; }
	.lose { color: #ff4444; }
	.btn { display: inline-block; margin-top: 1rem; padding: 0.5rem 1.5rem; background: #ffd700; color: #000; text-decoration: none; border-radius: 4px; font-weight: 600; }
</style>
```

- [ ] **Step 4: Write `src/lib/components/BlackjackBoard.svelte`**

```svelte
<script lang="ts">
	import type { Card as CardType, BlackjackState } from '$lib/types';
	import CardComponent from './Card.svelte';

	let { gameState, onAction, playing }: {
		gameState: BlackjackState | null;
		onAction: (action: string) => void;
		playing: boolean;
	} = $props();
</script>

{#if gameState}
	<div class="board">
		<div class="hand dealer">
			<h3>Dealer ({gameState.dealer_value || '?'})</h3>
			<div class="cards">
				{#each gameState.dealer_hand as card, i}
					<CardComponent card={card} hidden={i === 1 && !gameState.game_over} />
				{/each}
			</div>
		</div>
		<div class="hand player">
			<h3>Your Hand ({gameState.player_hand.reduce((s, c) => s + c.value, 0)})</h3>
			<div class="cards">
				{#each gameState.player_hand as card}
					<CardComponent card={card} />
				{/each}
			</div>
		</div>
		{#if gameState.split && gameState.player_second_hand}
			<div class="hand player">
				<h3>Second Hand ({gameState.player_second_hand.reduce((s, c) => s + c.value, 0)})</h3>
				<div class="cards">
					{#each gameState.player_second_hand as card}
						<CardComponent card={card} />
					{/each}
				</div>
			</div>
		{/if}
		{#if playing && !gameState.game_over}
			<div class="actions">
				<button onclick={() => onAction('hit')}>Hit</button>
				<button onclick={() => onAction('stand')}>Stand</button>
				<button onclick={() => onAction('double')} disabled={!gameState.can_double_down}>Double</button>
				<button onclick={() => onAction('split')} disabled={!gameState.can_split}>Split</button>
			</div>
		{/if}
	</div>
{/if}

<style>
	.board { max-width: 600px; margin: 2rem auto; }
	.hand { margin-bottom: 1.5rem; }
	.hand h3 { color: #a0a0c0; margin-bottom: 0.5rem; }
	.cards { display: flex; flex-wrap: wrap; gap: 4px; }
	.actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
	.actions button {
		padding: 0.6rem 1.2rem;
		border: 1px solid #555;
		border-radius: 4px;
		background: #2a2a4e;
		color: #e0e0e0;
		cursor: pointer;
		font-weight: 600;
	}
	.actions button:disabled { opacity: 0.4; cursor: not-allowed; }
	.actions button:hover:not(:disabled) { background: #3a3a5e; }
</style>
```

- [ ] **Step 5: Write `src/routes/blackjack/+page.server.ts`**

```ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	const coins = await locals.db.getCoins(locals.user!.id);
	return { coins, gameState: null };
};
```

- [ ] **Step 6: Write `src/routes/blackjack/start/+server.ts`**

```ts
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { createDeck, shuffleDeck, calculateHandValue } from '$lib/server/games/blackjack';
import type { BlackjackState } from '$lib/types';

export const POST: RequestHandler = async ({ request, locals }) => {
	const { wager } = await request.json();
	if (wager <= 0) return json({ error: 'Invalid wager' }, { status: 400 });

	const coins = await locals.db.getCoins(locals.user!.id);
	if (coins < wager) return json({ error: 'Not enough coins' }, { status: 400 });

	const deck = shuffleDeck(createDeck());
	const player_hand = [deck.pop()!, deck.pop()!];
	const dealer_hand = [deck.pop()!, deck.pop()!];

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
		dealer_value: calculateHandValue(dealer_hand)
	};

	await locals.db.deductCoins(locals.user!.id, wager);
	const gameId = await locals.db.createBlackjackGame(locals.user!.id, state);

	return json({ id: gameId, ...state });
};
```

- [ ] **Step 7: Write `src/routes/blackjack/action/+server.ts`**

```ts
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

	return json({
		...state,
		player_coins,
		can_double_down: action !== 'double' && state.player_hand.length === 2 && !state.split,
		can_split: !state.split && state.player_hand.length === 2 && state.player_hand[0].value === state.player_hand[1].value
	});
};
```

- [ ] **Step 8: Write `src/routes/blackjack/+page.svelte`**

```svelte
<script lang="ts">
	import { page } from '$app/stores';
	import ChipSelector from '$lib/components/ChipSelector.svelte';
	import BlackjackBoard from '$lib/components/BlackjackBoard.svelte';
	import ResultModal from '$lib/components/ResultModal.svelte';
	import type { BlackjackState } from '$lib/types';

	let { data } = $props();
	let coins = $state(data.coins);
	let gameState = $state<BlackjackState | null>(null);
	let wager = $state(10);
	let playing = $state(false);
	let gameId = $state<string | null>(null);
	let resultMessage = $state<string | null>(null);
	let resultPayout = $state(0);

	async function startGame() {
		const res = await fetch('/blackjack/start', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ wager })
		});
		if (!res.ok) { alert('Not enough coins!'); return; }
		const data = await res.json();
		gameId = data.id;
		gameState = data;
		coins = data.player_coins;
		playing = true;
		resultMessage = null;
	}

	async function handleAction(action: string) {
		if (!gameId) return;
		const res = await fetch('/blackjack/action', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ action, game_id: gameId })
		});
		const data = await res.json();
		gameState = data;
		coins = data.player_coins;
		if (data.game_over) {
			playing = false;
			resultMessage = data.message;
			resultPayout = data.player_coins - (data.player_coins - wager);
		}
	}
</script>

<h1>Blackjack</h1>

{#if !gameState}
	<div class="start">
		<p>Coins: {coins}</p>
		<ChipSelector {wager} setWager={(n) => wager = n} max={coins} />
		<button onclick={startGame} disabled={playing}>Deal</button>
	</div>
{/if}

<BlackjackBoard {gameState} onAction={handleAction} {playing} />
<ResultModal show={resultMessage !== null} message={resultMessage} payout={resultPayout} />

{#if gameState && gameState.game_over}
	<p class="coins-after">Coins: {coins}</p>
{/if}

<style>
	h1 { text-align: center; color: #ffd700; margin-top: 1rem; }
	.start { text-align: center; margin-top: 2rem; }
	.start p { color: #a0a0c0; }
	.start button { margin-top: 1rem; padding: 0.6rem 2rem; background: #4caf50; color: #000; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }
	.coins-after { text-align: center; color: #ffd700; font-weight: 600; margin-top: 1rem; }
</style>
```

- [ ] **Step 9: Commit**

```bash
git add src/routes/blackjack/ src/lib/components/Card.svelte src/lib/components/ChipSelector.svelte src/lib/components/BlackjackBoard.svelte src/lib/components/ResultModal.svelte && git commit -m "feat: add Blackjack game page"
```

---

### Task 11: Roulette routes + frontend

**Files:**
- Create: `src/routes/roulette/+page.svelte`
- Create: `src/routes/roulette/+page.server.ts`
- Create: `src/routes/roulette/spin/+server.ts`

- [ ] **Step 1: Write `src/routes/roulette/+page.server.ts`**

```ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	const coins = await locals.db.getCoins(locals.user!.id);
	return { coins };
};
```

- [ ] **Step 2: Write `src/routes/roulette/spin/+server.ts`**

```ts
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { spinWheel, calculatePayouts } from '$lib/server/games/roulette';
import type { Bet } from '$lib/types';

export const POST: RequestHandler = async ({ request, locals }) => {
	const { bets } = await request.json() as { bets: Bet[] };
	if (!bets.length) return json({ error: 'Place at least one bet' }, { status: 400 });

	const totalBet = bets.reduce((s, b) => s + b.amt, 0);
	const coins = await locals.db.getCoins(locals.user!.id);
	if (coins < totalBet) return json({ error: 'Not enough coins' }, { status: 400 });

	const winningNumber = spinWheel();
	const totalWin = calculatePayouts(bets, winningNumber);

	await locals.db.deductCoins(locals.user!.id, totalBet);
	if (totalWin > 0) await locals.db.addCoins(locals.user!.id, totalWin);

	const newCoins = await locals.db.getCoins(locals.user!.id);
	return json({ winning_number: winningNumber, total_bet: totalBet, total_win: totalWin, new_coins: newCoins });
};
```

- [ ] **Step 3: Write `src/routes/roulette/+page.svelte`**

```svelte
<script lang="ts">
	import { page } from '$app/stores';
	let { data } = $props();

	let coins = $state(data.coins);
	let bets = $state<{ numbers: string; odds: number; amt: number }[]>([]);
	let spinning = $state(false);
	let result = $state<{ winning_number: number; total_bet: number; total_win: number; new_coins: number } | null>(null);
	let error = $state<string | null>(null);

	const redNumbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
	const wheelOrder = [0,26,3,35,12,28,7,29,18,22,9,31,14,20,1,33,16,24,5,10,23,8,30,11,36,13,27,6,34,17,25,2,21,4,19,15,32];

	const singleBets = Array.from({ length: 37 }, (_, i) => ({
		numbers: String(i),
		odds: 35,
		label: String(i),
		color: i === 0 ? '#4caf50' : redNumbers.includes(i) ? '#ff4444' : '#e0e0e0'
	}));

	const specialBets = [
		{ numbers: '1,2,3,4,5,6,7,8,9,10,11,12', odds: 2, label: '1-12' },
		{ numbers: '13,14,15,16,17,18,19,20,21,22,23,24', odds: 2, label: '13-24' },
		{ numbers: '25,26,27,28,29,30,31,32,33,34,35,36', odds: 2, label: '25-36' },
		{ numbers: '1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35', odds: 1, label: 'Odd' },
		{ numbers: '2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36', odds: 1, label: 'Even' },
		{ numbers: '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18', odds: 1, label: '1-18' },
		{ numbers: '19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36', odds: 1, label: '19-36' },
		{ numbers: redNumbers.join(','), odds: 1, label: 'Red' },
		{ numbers: Array.from({ length: 37 }, (_, i) => i).filter(n => !redNumbers.includes(n) && n !== 0).join(','), odds: 1, label: 'Black' },
	];

	function toggleBet(bet: { numbers: string; odds: number; label: string }) {
		const existing = bets.find(b => b.numbers === bet.numbers);
		if (existing) {
			bets = bets.filter(b => b.numbers !== bet.numbers);
		} else {
			bets = [...bets, { numbers: bet.numbers, odds: bet.odds, amt: 10 }];
		}
	}

	async function spin() {
		if (bets.length === 0) return;
		spinning = true;
		error = null;
		result = null;

		const res = await fetch('/roulette/spin', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ bets })
		});
		const data = await res.json();
		if (res.ok) {
			result = data;
			coins = data.new_coins;
			bets = [];
		} else {
			error = data.error;
		}
		spinning = false;
	}
</script>

<h1>Roulette</h1>
<p class="coins">Coins: {coins}</p>

<div class="layout">
	<div class="table">
		<h3>Numbers</h3>
		<div class="grid">
			{#each singleBets as bet}
				<button
					class="cell"
					style="background: {bet.color}"
					class:selected={bets.some(b => b.numbers === bet.numbers)}
					onclick={() => toggleBet(bet)}
				>
					{bet.label}
				</button>
			{/each}
		</div>
		<h3>Outside Bets</h3>
		<div class="special">
			{#each specialBets as bet}
				<button
					class:selected={bets.some(b => b.numbers === bet.numbers)}
					onclick={() => toggleBet(bet)}
				>
					{bet.label}
				</button>
			{/each}
		</div>
	</div>
	<div class="info">
		<p>Current bets: {bets.reduce((s, b) => s + b.amt, 0)}</p>
		<button onclick={spin} disabled={bets.length === 0 || spinning}>
			{spinning ? 'Spinning...' : 'Spin!'}
		</button>
		{error && <p class="error">{error}</p>}
		{#if result}
			<div class="result">
				<h2>Result: {result.winning_number}</h2>
				<p class:win={result.total_win > 0} class:lose={result.total_win === 0}>
					{result.total_win > 0 ? `You won ${result.total_win} coins!` : 'No win this time.'}
				</p>
			</div>
		{/if}
	</div>
</div>

<style>
	h1 { text-align: center; color: #ffd700; }
	.coins { text-align: center; color: #a0a0c0; }
	.layout { display: flex; gap: 2rem; max-width: 800px; margin: 2rem auto; }
	.table { flex: 1; }
	.grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 2px; margin-bottom: 1rem; }
	.cell { padding: 0.5rem; border: 1px solid #333; border-radius: 2px; color: #fff; font-weight: 600; cursor: pointer; }
	.cell.selected { outline: 3px solid #ffd700; }
	.special { display: flex; flex-wrap: wrap; gap: 4px; }
	.special button { padding: 0.4rem 0.8rem; border: 1px solid #555; border-radius: 4px; background: #2a2a4e; color: #e0e0e0; cursor: pointer; }
	.special button.selected { background: #ffd700; color: #000; }
	.info { width: 200px; }
	.info button { width: 100%; padding: 0.6rem; background: #4caf50; color: #000; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }
	.info button:disabled { opacity: 0.5; }
	.error { color: #ff4444; }
	.result { margin-top: 1rem; }
	.result h2 { color: #ffd700; }
	.win { color: #4caf50; }
	.lose { color: #ff4444; }
</style>
```

- [ ] **Step 4: Commit**

```bash
git add src/routes/roulette/ && git commit -m "feat: add Roulette game page"
```

---

### Task 12: Slots (Threlte 3D) page

**Files:**
- Create: `src/routes/slots/+page.svelte`
- Create: `src/routes/slots/+page.server.ts`
- Create: `src/routes/slots/spin/+server.ts`
- Create: `src/lib/components/SlotMachine.svelte`
- Create: `src/lib/components/Reel.svelte`
- Create: `src/lib/components/SlotLights.svelte`
- Create: `src/lib/components/SlotCasing.svelte`
- Create: `src/params/fruit.ts`

- [ ] **Step 1: Write `src/routes/slots/+page.server.ts`**

```ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	const coins = await locals.db.getCoins(locals.user!.id);
	return { coins };
};
```

- [ ] **Step 2: Write `src/routes/slots/spin/+server.ts`**

```ts
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { spinReels, segmentToFruit, calculatePayout } from '$lib/server/games/slots';
import type { Fruit } from '$lib/types';

export const POST: RequestHandler = async ({ locals }) => {
	const coins = await locals.db.getCoins(locals.user!.id);
	if (coins < 1) return json({ error: 'Not enough coins' }, { status: 400 });

	await locals.db.deductCoins(locals.user!.id, 1);
	const segments = spinReels();
	const fruits: [Fruit, Fruit, Fruit] = [
		segmentToFruit(0, segments[0]),
		segmentToFruit(1, segments[1]),
		segmentToFruit(2, segments[2])
	];
	const payout = calculatePayout(fruits);
	if (payout > 0) await locals.db.addCoins(locals.user!.id, payout);
	const totalCoins = await locals.db.getCoins(locals.user!.id);

	return json({ stop_segments: segments, fruits, payout, total_coins: totalCoins });
};
```

- [ ] **Step 3: Write `src/lib/components/SlotCasing.svelte`**

```svelte
<script lang="ts">
	import { T } from '@threlte/core';
</script>

<T.Mesh position={[0, -1.5, -2]}>
	<T.BoxGeometry args={[6, 4, 1.5]} />
	<T.MeshStandardMaterial color="#1a1a3e" metalness={0.6} roughness={0.2} />
</T.Mesh>
```

- [ ] **Step 4: Write `src/lib/components/SlotLights.svelte`**

```svelte
<script lang="ts">
	import { T } from '@threlte/core';
</script>

<T.DirectionalLight position={[-2, 3, 2]} intensity={1} />
<T.DirectionalLight position={[2, 3, 2]} intensity={1} />
<T.AmbientLight intensity={0.5} />
```

- [ ] **Step 5: Write `src/lib/components/Reel.svelte`**

```svelte
<script lang="ts">
	import { T, useFrame } from '@threlte/core';
	import { type } from 'svelte';

	let { reelIndex, spinning, targetSegment }: { reelIndex: number; spinning: boolean; targetSegment: number | null } = $props();

	const WHEEL_SEGMENT = Math.PI / 4;
	let mesh: any = $state(null);
	let rotationX = $state(0);
	let spinningStart = $state(0);

	$effect(() => {
		if (spinning && targetSegment !== null) {
			spinningStart = performance.now();
		}
	});

	useFrame(({ delta }) => {
		if (!mesh) return;
		if (spinning && targetSegment !== null) {
			const elapsed = (performance.now() - spinningStart) / 1000;
			if (elapsed < 1.5) {
				rotationX += delta * 8;
				mesh.rotation.x = rotationX;
			} else {
				const target = targetSegment * WHEEL_SEGMENT;
				const diff = target - mesh.rotation.x;
				mesh.rotation.x += diff * 0.15;
				if (Math.abs(diff) < 0.01) {
					mesh.rotation.x = target;
				}
			}
		} else if (spinning) {
			rotationX += delta * 4;
			mesh.rotation.x = rotationX;
		}
	});

	const reelFaces = [
		{ fruit: '🍒', color: '#ff0044' },
		{ fruit: '🍎', color: '#ff4400' },
		{ fruit: '🍌', color: '#ffdd00' },
		{ fruit: '🍋', color: '#00ff44' },
		{ fruit: '🍒', color: '#ff0044' },
		{ fruit: '🍎', color: '#ff4400' },
		{ fruit: '🍌', color: '#ffdd00' },
		{ fruit: '🍋', color: '#00ff44' },
	];
</script>

<T.Mesh position={[-1.5 + reelIndex * 1.5, 0.5, 0.5]} bind:ref={mesh}>
	<T.CylinderGeometry args={[0.6, 0.6, 0.1, 8]} />
	<T.MeshStandardMaterial color="#222" />
</T.Mesh>
```

- [ ] **Step 6: Write `src/lib/components/SlotMachine.svelte`**

```svelte
<script lang="ts">
	import { T } from '@threlte/core';
	import SlotCasing from './SlotCasing.svelte';
	import SlotLights from './SlotLights.svelte';
	import Reel from './Reel.svelte';
	import type { Fruit } from '$lib/types';

	let { onSpin, coins, spinning }: { onSpin: () => void; coins: number; spinning: boolean } = $props();

	const fruits = ['CHERRY', 'LEMON', 'BANANA', 'APPLE'] as Fruit[];
</script>

<T.Group>
	<SlotLights />
	<SlotCasing />
	{#each [0, 1, 2] as i}
		<Reel reelIndex={i} spinning={spinning} targetSegment={null} />
	{/each}
	<T.Mesh
		position={[0, -2.5, 1]}
		onclick={onSpin}
		on:click={onSpin}
	>
		<T.BoxGeometry args={[1.2, 0.4, 0.1]} />
		<T.MeshStandardMaterial color={coins > 0 && !spinning ? '#ffd700' : '#555'} />
	</T.Mesh>
</T.Group>
```

- [ ] **Step 7: Write `src/routes/slots/+page.svelte`**

```svelte
<script lang="ts">
	import { page } from '$app/stores';
	import { Canvas } from '@threlte/core';
	import SlotMachine from '$lib/components/SlotMachine.svelte';
	import type { Fruit } from '$lib/types';

	let { data } = $props();
	let coins = $state(data.coins);
	let spinning = $state(false);
	let resultFruits = $state<Fruit[] | null>(null);
	let payout = $state(0);
	let message = $state<string | null>(null);

	async function spin() {
		if (spinning || coins < 1) return;
		spinning = true;
		resultFruits = null;
		message = null;
		payout = 0;

		const res = await fetch('/slots/spin', { method: 'POST' });
		const data = await res.json();
		if (res.ok) {
			resultFruits = data.fruits;
			payout = data.payout;
			coins = data.total_coins;
			data.payout > 0
				? message = `You won ${data.payout} coins!`
				: message = 'No win. Try again!';
		}
		setTimeout(() => { spinning = false; }, 2000);
	}
</script>

<h1>Slots</h1>
<p class="coins">Coins: {coins}</p>

<div class="canvas-container">
	<Canvas camera={{ position: [0, 0, 5], fov: 50 }}>
		<SlotMachine {onSpin={spin}} {coins} {spinning} />
	</Canvas>
</div>

<div class="controls" style="text-align: center; margin-top: 1rem;">
	<button onclick={spin} disabled={spinning || coins < 1}>
		{spinning ? 'Spinning...' : coins < 1 ? 'No coins' : 'SPIN (1 coin)'}
	</button>
</div>

{#if message}
	<div class="result" class:win={payout > 0}>
		<p>{message}</p>
		{#if resultFruits}
			<p class="fruits">{resultFruits.join(' - ')}</p>
		{/if}
	</div>
{/if}

<style>
	h1 { text-align: center; color: #ffd700; }
	.coins { text-align: center; color: #a0a0c0; }
	.canvas-container { width: 100%; height: 400px; }
	button { padding: 0.6rem 2rem; background: #ffd700; color: #000; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }
	button:disabled { opacity: 0.5; }
	.result { text-align: center; margin-top: 1rem; }
	.result.win { color: #4caf50; }
	.result:not(.win) { color: #ff4444; }
	.fruits { font-size: 1.5rem; letter-spacing: 0.5rem; }
</style>
```

- [ ] **Step 8: Commit**

```bash
git add src/routes/slots/ src/lib/components/SlotMachine.svelte src/lib/components/Reel.svelte src/lib/components/SlotCasing.svelte src/lib/components/SlotLights.svelte && git commit -m "feat: add Slots 3D game page with Threlte"
```

---

### Task 15: Verify full build + create PR

**Files:**
- Create: `pocketbase/pb_schema.json` (documentation only — schema is created via PocketBase admin UI)
- Run full build check

- [ ] **Step 1: Verify full build**

```bash
pnpm run build
```

Expected: No errors. SvelteKit builds successfully.

- [ ] **Step 2: Run all tests**

```bash
npx vitest run
```

Expected: All game logic tests pass.

- [ ] **Step 3: Create branch and open PR**

```bash
git checkout -b feat/sveltekit-pocketbase-port
git push -u origin feat/sveltekit-pocketbase-port
gh pr create --title "feat: port to SvelteKit + PocketBase" --body "## Summary\n- Port Flask + React/jQuery casino to single SvelteKit app\n- PocketBase auth + DB with adapter abstraction layer\n- All game logic ported to TypeScript server endpoints\n- Threlte 3D slot machine\n\nCloses: port from Flask to SvelteKit"
```

---

### Task 13.5: Copy static assets from existing project

**Files:**
- Create: `static/images/` (copy from `cherry-charm/public/images/` and `blackjack-master/img/`)

- [ ] **Step 1: Copy card images and GLB models**

```bash
mkdir -p static/images static/models
cp -r blackjack-master/img/* static/images/ 2>/dev/null || true
cp -r cherry-charm/public/images/* static/images/ 2>/dev/null || true
cp -r cherry-charm/public/models/* static/models/ 2>/dev/null || true
```

- [ ] **Step 2: Commit**

```bash
git add static/ && git commit -m "feat: add static assets (card images, GLB models)"
```

---

### Task 14: PocketBase schema setup instructions

**Files:** (no code — admin UI setup)

- [ ] **Step 1: Start PocketBase and create collections**

```bash
# Download PocketBase if not present
mkdir -p pocketbase
cd pocketbase

# macOS ARM64
curl -L https://github.com/pocketbase/pocketbase/releases/download/v0.22.0/pocketbase_0.22.0_darwin_arm64.zip -o pb.zip
unzip -o pb.zip && rm pb.zip
cd ..

# Start PocketBase
./pocketbase/pocketbase serve --dir=./pocketbase/pb_data
```

Open `http://127.0.0.1:8090/_/` in browser.

**Create collections via Admin UI:**

1. **users** (built-in auth collection) — already exists
   - Add field: `coins` (number, default 100)
   - Enable: `List`, `View`, `Create`, `Update` auth rule for "users" (authenticated users manage themselves)

2. **blackjack_games**
   - Fields:
     - `user` (relation → users, required)
     - `deck` (json, required)
     - `dealer_hand` (json, required)
     - `player_hand` (json, required)
     - `player_second_hand` (json)
     - `player_coins` (number, required)
     - `current_wager` (number, required)
     - `game_over` (bool, default false)
     - `message` (text)
     - `player_stood` (bool, default false)
     - `double_down` (bool, default false)
     - `split` (bool, default false)
     - `current_hand` (text, default "first")
     - `dealer_value` (number, default 0)
   - API rules: Create/List/View/Update only for users who own the record

---

## Spec Coverage Check

| Spec Requirement | Task |
|-----------------|------|
| SvelteKit project scaffold | Task 1 |
| Shared types | Task 2 |
| DB adapter interface | Task 3 |
| PocketBase implementation | Task 3 |
| Blackjack game logic (TS) | Task 4 |
| Roulette game logic (TS) | Task 5 |
| Slots game logic (TS) | Task 6 |
| Auth hooks (PocketBase per-request) | Task 7 |
| Login/signup/logout routes | Task 8 |
| Auth guard layout | Task 8 |
| Lobby/dashboard | Task 9 |
| Blackjack UI + API endpoints | Task 10 |
| Roulette UI + API endpoints | Task 11 |
| Slots Threlte 3D + API endpoints | Task 12 |
| Static assets (images, GLB models) | Task 13.5 |
| PocketBase schema setup | Task 14 |
| Full build verification | Task 15 |
| All game logic tests pass | Tasks 4-6 + 15 |
