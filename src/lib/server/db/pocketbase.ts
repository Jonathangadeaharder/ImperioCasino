import type PocketBase from "pocketbase";
import type { BlackjackState, User } from "$lib/types";
import type { DBAdapter } from "./adapter";

export class PocketBaseAdapter implements DBAdapter {
	constructor(private pb: PocketBase) {}

	async getUser(id: string): Promise<User> {
		const record = await this.pb.collection("users").getOne(id);
		return { id: record.id, username: record.username, coins: record.coins };
	}

	async getUserByUsername(username: string): Promise<User | null> {
		const list = await this.pb.collection("users").getList(1, 1, {
			filter: `username="${username}"`,
		});
		if (list.items.length === 0) return null;
		const r = list.items[0];
		return { id: r.id, username: r.username, coins: r.coins };
	}

	async getCoins(userId: string): Promise<number> {
		const record = await this.pb.collection("users").getOne(userId);
		return record.coins;
	}

	async addCoins(userId: string, amount: number): Promise<number> {
		const record = await this.pb
			.collection("users")
			.update(userId, { coins: { increment: amount } });
		return record.coins;
	}

	async deductCoins(userId: string, amount: number): Promise<number> {
		const record = await this.pb
			.collection("users")
			.update(userId, { coins: { decrement: amount } });
		return record.coins;
	}

	async setCoins(userId: string, amount: number): Promise<number> {
		const record = await this.pb
			.collection("users")
			.update(userId, { coins: amount });
		return record.coins;
	}

	async createBlackjackGame(
		userId: string,
		state: BlackjackState,
	): Promise<string> {
		const { user_id: _, ...rest } = state;
		const record = await this.pb.collection("blackjack_games").create({
			user_id: userId,
			...rest,
		});
		return record.id;
	}

	async updateBlackjackGame(
		gameId: string,
		state: Partial<BlackjackState>,
	): Promise<void> {
		await this.pb.collection("blackjack_games").update(gameId, state);
	}

	async getBlackjackGame(gameId: string): Promise<BlackjackState> {
		const record = await this.pb
			.collection("blackjack_games")
			.getOne(gameId);
		return {
			id: record.id,
			user_id: record.user_id,
			deck: record.deck,
			dealer_hand: record.dealer_hand,
			player_hand: record.player_hand,
			player_second_hand: record.player_second_hand,
			player_coins: record.player_coins,
			current_wager: record.current_wager,
			game_over: record.game_over,
			message: record.message,
			player_stood: record.player_stood,
			double_down: record.double_down,
			split: record.split,
			current_hand: record.current_hand,
			dealer_value: record.dealer_value,
		};
	}
}
