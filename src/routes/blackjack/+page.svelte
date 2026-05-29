<script lang="ts">
import { page } from "$app/stores";
import BlackjackBoard from "$lib/components/BlackjackBoard.svelte";
import ChipSelector from "$lib/components/ChipSelector.svelte";
import ResultModal from "$lib/components/ResultModal.svelte";
import type { BlackjackState } from "$lib/types";

let _coins = $state($page.data.coins);
let _gameState = $state<BlackjackState | null>(null);
let wager = $state(10);
let _playing = $state(false);
let gameId = $state<string | null>(null);
let _resultMessage = $state<string | null>(null);
let _resultPayout = $state(0);

async function _startGame() {
	const res = await fetch("/blackjack/start", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ wager }),
	});
	if (!res.ok) {
		alert("Not enough coins!");
		return;
	}
	const data = await res.json();
	gameId = data.id;
	_gameState = data;
	_coins = data.player_coins;
	_playing = true;
	_resultMessage = null;
}

async function _handleAction(action: string) {
	if (!gameId) return;
	const res = await fetch("/blackjack/action", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ action, game_id: gameId }),
	});
	const d = await res.json();
	_gameState = d;
	_coins = d.player_coins;
	if (d.game_over) {
		_playing = false;
		_resultMessage = d.message;
		_resultPayout = d.player_coins;
	}
}
</script>

<h1>Blackjack</h1>

{#if !_gameState}
	<div class="start">
		<p>Coins: {_coins}</p>
		<ChipSelector {wager} setWager={(n: number) => wager = n} max={_coins} />
		<button onclick={_startGame} disabled={_playing}>Deal</button>
	</div>
{/if}

<BlackjackBoard gameState={_gameState} onAction={_handleAction} playing={_playing} />
<ResultModal show={_resultMessage !== null} message={_resultMessage} payout={_resultPayout} />

{#if _gameState && _gameState.game_over}
	<p class="coins-after">Coins: {_coins}</p>
{/if}

<style>
	h1 { text-align: center; color: #ffd700; margin-top: 1rem; }
	.start { text-align: center; margin-top: 2rem; }
	.start p { color: #a0a0c0; }
	.start button { margin-top: 1rem; padding: 0.6rem 2rem; background: #4caf50; color: #000; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }
	.coins-after { text-align: center; color: #ffd700; font-weight: 600; margin-top: 1rem; }
</style>
