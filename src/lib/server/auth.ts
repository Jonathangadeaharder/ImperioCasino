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
