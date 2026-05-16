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
