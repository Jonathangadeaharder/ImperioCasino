/// <reference types="@sveltejs/kit" />
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
