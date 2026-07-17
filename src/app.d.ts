/// <reference types="@sveltejs/kit" />
/// <reference types="@testing-library/jest-dom/vitest" />

import type { AuthSession } from "$lib/server/auth-service";
import type { DrizzleAdapter } from "$lib/server/db/adapter";
import type { User } from "$lib/types";

declare global {
	namespace App {
		interface Locals {
			db: DrizzleAdapter;
			auth: () => Promise<AuthSession | null>;
			user: User | null;
		}
	}
}
