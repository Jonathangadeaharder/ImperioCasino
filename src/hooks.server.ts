import type { Handle, RequestEvent } from "@sveltejs/kit";
import { redirect } from "@sveltejs/kit";
import { building } from "$app/environment";
import { type AuthSession, authService } from "$lib/server/auth-service";
import { DrizzleAdapter } from "$lib/server/db/adapter";
import { ensureDb } from "$lib/server/db/database";

const PUBLIC_PATHS = new Set(["/login", "/signup", "/logout"]);

function isPublicPath(pathname: string): boolean {
	return PUBLIC_PATHS.has(pathname) || pathname === "/";
}

function createAuthHandler(event: RequestEvent) {
	let cache: Promise<AuthSession | null> | undefined;
	return (): Promise<AuthSession | null> => {
		cache ??= authService.getSession(event);
		return cache;
	};
}

async function attachUser(event: RequestEvent): Promise<void> {
	const session = await event.locals.auth();
	event.locals.user = session?.user ?? null;
}

async function requireAuth(event: RequestEvent): Promise<Response | null> {
	if (isPublicPath(event.url.pathname)) return null;
	const session = await event.locals.auth();
	if (session) return null;
	return redirect(303, "/login");
}

function applySecurityHeaders(response: Response): void {
	response.headers.set("X-Frame-Options", "DENY");
	response.headers.set("X-Content-Type-Options", "nosniff");
	response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
	response.headers.set(
		"Permissions-Policy",
		"camera=(), microphone=(), geolocation=()",
	);
}

export const handle: Handle = async ({ event, resolve }) => {
	if (building) return resolve(event);

	await ensureDb();
	event.locals.db = new DrizzleAdapter();
	event.locals.auth = createAuthHandler(event);

	const authResponse = await requireAuth(event);
	if (authResponse) return authResponse;

	await attachUser(event);

	const response = await resolve(event);
	applySecurityHeaders(response);
	return response;
};
