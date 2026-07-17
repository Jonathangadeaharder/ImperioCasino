import { createHash, randomBytes } from "node:crypto";
import type { RequestEvent } from "@sveltejs/kit";
import { compare, hash } from "bcryptjs";
import { and, eq } from "drizzle-orm";
import type { User } from "$lib/types";
import { db } from "./db/database";
import { session, user } from "./db/schema";

const DUMMY_BCRYPT_HASH = `$2a$12$${"x".repeat(53)}`;
const SESSION_EXPIRY_DAYS = 7;
const SECONDS_PER_MINUTE = 60;
const MINUTES_PER_HOUR = 60;
const HOURS_PER_DAY = 24;
const SESSION_EXPIRY_MS =
	SECONDS_PER_MINUTE *
	MINUTES_PER_HOUR *
	HOURS_PER_DAY *
	SESSION_EXPIRY_DAYS *
	1000;
const SESSION_TOKEN_RE = /imperio_session=([^;]+)/;
const MIN_PASSWORD_LENGTH = 8;
const MAX_PASSWORD_LENGTH = 128;
const BCRYPT_SALT_ROUNDS = 12;
const COOKIE_NAME = "imperio_session";
const STARTING_COINS = 100;
const SIGN_UP_FAILED_MESSAGE =
	"Could not create your account. Please try again.";

export type AuthUser = Pick<User, "id" | "username" | "coins"> & {
	email: string;
};

export interface AuthSession {
	user: AuthUser;
	expires: string;
}

function extractSessionToken(cookieHeader: string): string | null {
	const match = SESSION_TOKEN_RE.exec(cookieHeader);
	return match?.[1] ?? null;
}

function setSessionCookie(event: RequestEvent, token: string): void {
	event.cookies.set(COOKIE_NAME, token, {
		httpOnly: true,
		secure: process.env.NODE_ENV === "production",
		sameSite: "lax",
		path: "/",
	});
}

function clearSessionCookie(event: RequestEvent): void {
	event.cookies.delete(COOKIE_NAME, { path: "/" });
}

function hashToken(token: string): string {
	return createHash("sha256").update(token).digest("hex");
}

function toAuthUser(row: typeof user.$inferSelect): AuthUser {
	return {
		id: row.id,
		username: row.username,
		email: row.email,
		coins: row.coins,
	};
}

async function createSession(
	userId: string,
): Promise<{ token: string; expiresAt: Date }> {
	const token = randomBytes(32).toString("base64url");
	const tokenHash = hashToken(token);
	const now = new Date();
	const expiresAt = new Date(now.getTime() + SESSION_EXPIRY_MS);
	await db.insert(session).values({
		userId,
		tokenHash,
		expiresAt,
		createdAt: now,
		updatedAt: now,
	});
	return { token, expiresAt };
}

export class AuthService {
	async getSession(event: RequestEvent): Promise<AuthSession | null> {
		const cookieHeader = event.request.headers.get("cookie") ?? "";
		const sessionToken = extractSessionToken(cookieHeader);
		if (!sessionToken) return null;

		const sessionRows = await db
			.select()
			.from(session)
			.where(eq(session.tokenHash, hashToken(sessionToken)))
			.limit(1);
		if (!sessionRows[0]) return null;

		const sessionRow = sessionRows[0];
		if (new Date(sessionRow.expiresAt) < new Date()) return null;

		const userRows = await db
			.select()
			.from(user)
			.where(eq(user.id, sessionRow.userId))
			.limit(1);
		if (!userRows[0]) return null;

		return {
			user: toAuthUser(userRows[0]),
			expires: sessionRow.expiresAt.toISOString(),
		};
	}

	async signUp(
		event: RequestEvent,
		username: string,
		email: string,
		password: string,
	): Promise<{ user: AuthUser | null; error: string | null }> {
		if (password.length < MIN_PASSWORD_LENGTH) {
			return { user: null, error: "Password must be at least 8 characters." };
		}
		if (password.length > MAX_PASSWORD_LENGTH) {
			return {
				user: null,
				error: "Password must be less than 128 characters.",
			};
		}

		const existingByUsername = await db
			.select()
			.from(user)
			.where(eq(user.username, username))
			.limit(1);
		const existingByEmail = await db
			.select()
			.from(user)
			.where(eq(user.email, email))
			.limit(1);
		if (existingByUsername[0] || existingByEmail[0]) {
			await hash(password, BCRYPT_SALT_ROUNDS);
			return { user: null, error: SIGN_UP_FAILED_MESSAGE };
		}

		const passwordHash = await hash(password, BCRYPT_SALT_ROUNDS);
		const now = new Date();
		const rows = await db
			.insert(user)
			.values({
				username,
				email,
				passwordHash,
				coins: STARTING_COINS,
				createdAt: now,
				updatedAt: now,
			})
			.returning();
		const newUser = rows[0];
		if (!newUser) return { user: null, error: SIGN_UP_FAILED_MESSAGE };

		const { token } = await createSession(newUser.id);
		setSessionCookie(event, token);
		return { user: toAuthUser(newUser), error: null };
	}

	async signIn(
		event: RequestEvent,
		email: string,
		password: string,
	): Promise<{ user: AuthUser | null; error: string | null }> {
		const userRows = await db
			.select()
			.from(user)
			.where(eq(user.email, email))
			.limit(1);
		const foundUser = userRows[0];
		if (!foundUser) {
			await compare(password, DUMMY_BCRYPT_HASH);
			return { user: null, error: "Invalid email or password." };
		}

		const valid = await compare(password, foundUser.passwordHash);
		if (!valid) return { user: null, error: "Invalid email or password." };

		const { token } = await createSession(foundUser.id);
		setSessionCookie(event, token);
		return { user: toAuthUser(foundUser), error: null };
	}

	async signOut(event: RequestEvent): Promise<void> {
		const cookieHeader = event.request.headers.get("cookie") ?? "";
		const sessionToken = extractSessionToken(cookieHeader);
		if (sessionToken) {
			try {
				await db
					.delete(session)
					.where(eq(session.tokenHash, hashToken(sessionToken)));
			} catch {
				// Session may already be deleted.
			}
		}
		clearSessionCookie(event);
	}

	async getUserByEmail(email: string): Promise<AuthUser | null> {
		const rows = await db
			.select()
			.from(user)
			.where(and(eq(user.email, email)))
			.limit(1);
		return rows[0] ? toAuthUser(rows[0]) : null;
	}
}

export const authService = new AuthService();
