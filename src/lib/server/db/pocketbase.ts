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
				filter: this.pb.filter('username = {:username}', { username })
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
		const record = await this.pb.collection('users').update(userId, { 'coins+': amount });
		return record.coins;
	}

	async deductCoins(userId: string, amount: number): Promise<number> {
		const record = await this.pb.collection('users').update(userId, { 'coins-': amount });
		return record.coins;
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
