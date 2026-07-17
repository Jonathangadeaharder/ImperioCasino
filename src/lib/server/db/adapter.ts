import { eq, type SQL, sql } from "drizzle-orm";
import type { BlackjackState, User } from "$lib/types";
import { db } from "./database";
import { blackjackGame, user } from "./schema";

type CoinValue = NonNullable<typeof user.$inferInsert.coins> | SQL;

export interface DBAdapter {
	getUser(id: string): Promise<User>;
	getUserByUsername(username: string): Promise<User | null>;
	getCoins(userId: string): Promise<number>;
	addCoins(userId: string, amount: number): Promise<number>;
	deductCoins(userId: string, amount: number): Promise<number>;
	setCoins(userId: string, amount: number): Promise<number>;
	createBlackjackGame(userId: string, state: BlackjackState): Promise<string>;
	updateBlackjackGame(
		gameId: string,
		state: Partial<BlackjackState>,
	): Promise<void>;
	getBlackjackGame(gameId: string): Promise<BlackjackState | null>;
}

function toUser(row: typeof user.$inferSelect): User {
	return { id: row.id, username: row.username, coins: row.coins };
}

// Maps BlackjackState snake_case keys to drizzle blackjackGame camelCase
// columns. Only keys present in `state` are copied into the patch.
const BLACKJACK_FIELD_MAP: ReadonlyArray<
	[keyof BlackjackState, keyof typeof blackjackGame.$inferInsert]
> = [
	["deck", "deck"],
	["dealer_hand", "dealerHand"],
	["player_hand", "playerHand"],
	["player_second_hand", "playerSecondHand"],
	["player_coins", "playerCoins"],
	["current_wager", "currentWager"],
	["game_over", "gameOver"],
	["message", "message"],
	["player_stood", "playerStood"],
	["double_down", "doubleDown"],
	["split", "split"],
	["current_hand", "currentHand"],
	["dealer_value", "dealerValue"],
];

async function updateUserCoins(
	userId: string,
	coinExpr: CoinValue,
): Promise<number> {
	const rows = await db
		.update(user)
		.set({ coins: coinExpr, updatedAt: new Date() })
		.where(eq(user.id, userId))
		.returning({ coins: user.coins });
	if (!rows[0]) throw new Error("User not found");
	return rows[0].coins;
}

export class DrizzleAdapter implements DBAdapter {
	async getUser(id: string): Promise<User> {
		const rows = await db.select().from(user).where(eq(user.id, id)).limit(1);
		if (!rows[0]) throw new Error("User not found");
		return toUser(rows[0]);
	}

	async getUserByUsername(username: string): Promise<User | null> {
		const rows = await db
			.select()
			.from(user)
			.where(eq(user.username, username))
			.limit(1);
		return rows[0] ? toUser(rows[0]) : null;
	}

	async getCoins(userId: string): Promise<number> {
		const rows = await db
			.select({ coins: user.coins })
			.from(user)
			.where(eq(user.id, userId))
			.limit(1);
		if (!rows[0]) throw new Error("User not found");
		return rows[0].coins;
	}

	async addCoins(userId: string, amount: number): Promise<number> {
		return updateUserCoins(userId, sql`${user.coins} + ${amount}`);
	}

	async deductCoins(userId: string, amount: number): Promise<number> {
		return updateUserCoins(userId, sql`${user.coins} - ${amount}`);
	}

	async setCoins(userId: string, amount: number): Promise<number> {
		return updateUserCoins(userId, amount);
	}

	async createBlackjackGame(
		userId: string,
		state: BlackjackState,
	): Promise<string> {
		const now = new Date();
		const rows = await db
			.insert(blackjackGame)
			.values({
				userId,
				deck: state.deck,
				dealerHand: state.dealer_hand,
				playerHand: state.player_hand,
				playerSecondHand: state.player_second_hand,
				playerCoins: state.player_coins,
				currentWager: state.current_wager,
				gameOver: state.game_over,
				message: state.message,
				playerStood: state.player_stood,
				doubleDown: state.double_down,
				split: state.split,
				currentHand: state.current_hand,
				dealerValue: state.dealer_value,
				createdAt: now,
				updatedAt: now,
			})
			.returning({ id: blackjackGame.id });
		return rows[0].id;
	}

	async updateBlackjackGame(
		gameId: string,
		state: Partial<BlackjackState>,
	): Promise<void> {
		const patch: Record<string, unknown> = { updatedAt: new Date() };
		for (const [stateKey, columnKey] of BLACKJACK_FIELD_MAP) {
			const value = state[stateKey];
			if (value !== undefined) patch[columnKey] = value;
		}
		await db
			.update(blackjackGame)
			.set(patch)
			.where(eq(blackjackGame.id, gameId));
	}

	async getBlackjackGame(gameId: string): Promise<BlackjackState | null> {
		const rows = await db
			.select()
			.from(blackjackGame)
			.where(eq(blackjackGame.id, gameId))
			.limit(1);
		const row = rows[0];
		if (!row) return null;
		return {
			id: row.id,
			user_id: row.userId,
			deck: row.deck,
			dealer_hand: row.dealerHand,
			player_hand: row.playerHand,
			player_second_hand: row.playerSecondHand,
			player_coins: row.playerCoins,
			current_wager: row.currentWager,
			game_over: row.gameOver,
			message: row.message,
			player_stood: row.playerStood,
			double_down: row.doubleDown,
			split: row.split,
			current_hand: row.currentHand as "first" | "second",
			dealer_value: row.dealerValue,
		};
	}
}

export const drizzleAdapter = new DrizzleAdapter();
