<script lang="ts">
	import ChipSelector from '$lib/components/ChipSelector.svelte';
	import BlackjackBoard from '$lib/components/BlackjackBoard.svelte';
	import ResultModal from '$lib/components/ResultModal.svelte';
	import type { BlackjackState } from '$lib/types';

	import { page } from '$app/stores';
	let coins = $state($page.data.coins);
	let gameState = $state<BlackjackState | null>(null);
	let wager = $state(10);
	let playing = $state(false);
	let gameId = $state<string | null>(null);
	let resultMessage = $state<string | null>(null);
	let resultPayout = $state(0);

	async function startGame() {
		const res = await fetch('/blackjack/start', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ wager })
		});
		if (!res.ok) { alert('Not enough coins!'); return; }
		const data = await res.json();
		gameId = data.id;
		gameState = data;
		coins = data.player_coins;
		playing = true;
		resultMessage = null;
	}

	async function handleAction(action: string) {
		if (!gameId) return;
		const res = await fetch('/blackjack/action', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ action, game_id: gameId })
		});
		const d = await res.json();
		gameState = d;
		coins = d.player_coins;
		if (d.game_over) {
			playing = false;
			resultMessage = d.message;
			resultPayout = d.player_coins;
		}
	}
</script>

<h1>Blackjack</h1>

{#if !gameState}
	<div class="start">
		<p>Coins: {coins}</p>
		<ChipSelector {wager} setWager={(n) => wager = n} max={coins} />
		<button onclick={startGame} disabled={playing}>Deal</button>
	</div>
{/if}

<BlackjackBoard {gameState} onAction={handleAction} {playing} />
<ResultModal show={resultMessage !== null} message={resultMessage} payout={resultPayout} />

{#if gameState && gameState.game_over}
	<p class="coins-after">Coins: {coins}</p>
{/if}

<style>
	h1 { text-align: center; color: #ffd700; margin-top: 1rem; }
	.start { text-align: center; margin-top: 2rem; }
	.start p { color: #a0a0c0; }
	.start button { margin-top: 1rem; padding: 0.6rem 2rem; background: #4caf50; color: #000; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }
	.coins-after { text-align: center; color: #ffd700; font-weight: 600; margin-top: 1rem; }
</style>
