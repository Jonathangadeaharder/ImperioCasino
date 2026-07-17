import type { InferInsertModel, InferSelectModel } from "drizzle-orm";
import {
	boolean,
	integer,
	jsonb,
	pgTable,
	text,
	timestamp,
	uuid,
} from "drizzle-orm/pg-core";
import type { BlackjackState } from "$lib/types";

const STARTING_COINS = 100;

export const user = pgTable("user", {
	id: uuid("id").primaryKey().defaultRandom(),
	username: text("username").notNull().unique(),
	email: text("email").notNull().unique(),
	passwordHash: text("password_hash").notNull(),
	coins: integer("coins").default(STARTING_COINS).notNull(),
	createdAt: timestamp("created_at").notNull(),
	updatedAt: timestamp("updated_at").notNull(),
});

export type User = InferSelectModel<typeof user>;
export type NewUser = InferInsertModel<typeof user>;

export const session = pgTable("session", {
	id: uuid("id").primaryKey().defaultRandom(),
	userId: uuid("user_id")
		.references(() => user.id)
		.notNull(),
	tokenHash: text("token_hash").notNull().unique(),
	expiresAt: timestamp("expires_at").notNull(),
	createdAt: timestamp("created_at").notNull(),
	updatedAt: timestamp("updated_at").notNull(),
});

export type Session = InferSelectModel<typeof session>;

export const blackjackGame = pgTable("blackjack_game", {
	id: uuid("id").primaryKey().defaultRandom(),
	userId: uuid("user_id")
		.references(() => user.id)
		.notNull(),
	deck: jsonb("deck").$type<BlackjackState["deck"]>().notNull(),
	dealerHand: jsonb("dealer_hand")
		.$type<BlackjackState["dealer_hand"]>()
		.notNull(),
	playerHand: jsonb("player_hand")
		.$type<BlackjackState["player_hand"]>()
		.notNull(),
	playerSecondHand:
		jsonb("player_second_hand").$type<BlackjackState["player_second_hand"]>(),
	playerCoins: integer("player_coins").notNull(),
	currentWager: integer("current_wager").notNull(),
	gameOver: boolean("game_over").notNull(),
	message: text("message"),
	playerStood: boolean("player_stood").notNull(),
	doubleDown: boolean("double_down").notNull(),
	split: boolean("split").notNull(),
	currentHand: text("current_hand").notNull(),
	dealerValue: integer("dealer_value").notNull(),
	createdAt: timestamp("created_at").notNull(),
	updatedAt: timestamp("updated_at").notNull(),
});

export type BlackjackGame = InferSelectModel<typeof blackjackGame>;
export type NewBlackjackGame = InferInsertModel<typeof blackjackGame>;
