import { existsSync, readFileSync, rmSync } from "node:fs";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { PGlite } from "@electric-sql/pglite";
import { drizzle, type PgliteDatabase } from "drizzle-orm/pglite";
import { migrate } from "drizzle-orm/pglite/migrator";
import * as schema from "./schema";

export type DrizzleDb = PgliteDatabase<typeof schema>;

const globalForDb = globalThis as unknown as {
	__pglite?: PGlite;
	__db?: DrizzleDb;
	__dbInitPromise?: Promise<void>;
};

let _pglite: PGlite | undefined = globalForDb.__pglite;
let _db: DrizzleDb | undefined = globalForDb.__db;
let _initPromise: Promise<void> | undefined = globalForDb.__dbInitPromise;

function persistToGlobal(): void {
	globalForDb.__pglite = _pglite;
	globalForDb.__db = _db;
	globalForDb.__dbInitPromise = _initPromise;
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const migrationsFolder = path.resolve(__dirname, "./migrations");

function resolveDataDir(): string {
	const fromEnv = process.env.PGLITE_DATA_DIR;
	if (fromEnv && fromEnv !== "memory") return fromEnv;
	if (process.env.NODE_ENV === "test") return "memory";
	return path.resolve(process.cwd(), ".pglite");
}

function cleanStalePid(dataDir: string): void {
	const pidFile = path.join(dataDir, "postmaster.pid");
	if (!existsSync(pidFile)) return;
	if (isProcessAlive(readPidFile(pidFile))) return;
	try {
		rmSync(pidFile, { force: true });
	} catch {
		// Best-effort; PGlite will handle it.
	}
}

function readPidFile(pidFile: string): number | null {
	try {
		const content = readFileSync(pidFile, "utf8").trim();
		const pid = Number.parseInt(content.split("\n")[0] ?? "", 10);
		return Number.isFinite(pid) && pid > 0 ? pid : null;
	} catch {
		return null;
	}
}

function isProcessAlive(pid: number | null): boolean {
	if (pid === null) return false;
	try {
		process.kill(pid, 0);
		return true;
	} catch (err) {
		return (err as NodeJS.ErrnoException).code === "EPERM";
	}
}

async function createPglite(dataDir: string): Promise<PGlite> {
	if (dataDir === "memory") return PGlite.create();
	if (!existsSync(dataDir)) await mkdir(dataDir, { recursive: true });
	cleanStalePid(dataDir);
	return PGlite.create(dataDir, { relaxedDurability: false });
}

async function runMigrations(pglite: PGlite): Promise<void> {
	const db = drizzle(pglite, { schema });
	await migrate(db, { migrationsFolder });
}

async function initDb(): Promise<void> {
	if (_db) return;
	const dataDir = resolveDataDir();
	try {
		_pglite = await createPglite(dataDir);
		_db = drizzle(_pglite, { schema });
		persistToGlobal();
		await runMigrations(_pglite);
	} catch (err) {
		// Recovery: fall back to in-memory so dev/test keep working.
		console.error("[Database] Init failed, falling back to in-memory:", err);
		_pglite = await PGlite.create();
		_db = drizzle(_pglite, { schema });
		persistToGlobal();
		await runMigrations(_pglite);
	}
}

export async function ensureDb(): Promise<void> {
	_initPromise ??= initDb();
	try {
		await _initPromise;
	} catch (err) {
		_initPromise = undefined;
		globalForDb.__dbInitPromise = undefined;
		throw err;
	}
}

export const db = new Proxy({} as DrizzleDb, {
	get(_target, prop, receiver) {
		if (prop === "then") return undefined;
		if (_db === undefined) {
			throw new Error(
				"Database not initialized. Call await ensureDb() at startup (hooks.server.ts).",
			);
		}
		return Reflect.get(_db, prop, receiver);
	},
});

export async function closeDb(): Promise<void> {
	if (_pglite) {
		try {
			await _pglite.close();
		} catch {
			// Best-effort on shutdown.
		}
		_pglite = undefined;
		_db = undefined;
		_initPromise = undefined;
		persistToGlobal();
	}
}
