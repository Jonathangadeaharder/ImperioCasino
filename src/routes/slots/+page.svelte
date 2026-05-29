<script lang="ts">
import { Canvas, T } from "@threlte/core";
import { page } from "$app/stores";
import SlotMachine from "$lib/components/SlotMachine.svelte";
import type { Fruit } from "$lib/types";

let coins = $state($page.data.coins);
let spinning = $state(false);
let _resultFruits = $state<Fruit[] | null>(null);
let _payout = $state(0);
let _message = $state<string | null>(null);

async function _spin() {
	if (spinning || coins < 1) return;
	spinning = true;
	_resultFruits = null;
	_message = null;
	_payout = 0;

	try {
		const res = await fetch("/slots/spin", { method: "POST" });
		const d = await res.json();
		if (res.ok) {
			_resultFruits = d.fruits;
			_payout = d.payout;
			coins = d.total_coins;
			_message =
				d.payout > 0 ? `You won ${d.payout} coins!` : "No win. Try again!";
		} else {
			_message = d.error ?? "Spin failed. Try again.";
		}
	} catch {
		_message = "Spin failed. Try again.";
	} finally {
		setTimeout(() => {
			spinning = false;
		}, 2000);
	}
}
</script>

<h1>Slots</h1>
<p class="coins">Coins: {coins}</p>

<div class="canvas-container">
	<Canvas>
		<T.PerspectiveCamera position={[0, 0, 5]} fov={50} />
		<SlotMachine onSpin={_spin} {coins} {spinning} />
	</Canvas>
</div>

<div class="controls" style="text-align: center; margin-top: 1rem;">
	<button onclick={_spin} disabled={spinning || coins < 1}>
		{spinning ? 'Spinning...' : coins < 1 ? 'No coins' : 'SPIN (1 coin)'}
	</button>
</div>

{#if _message}
	<div class="result" class:win={_payout > 0}>
		<p>{_message}</p>
		{#if _resultFruits}
			<p class="fruits">{_resultFruits.join(' - ')}</p>
		{/if}
	</div>
{/if}

<style>
	h1 { text-align: center; color: #ffd700; }
	.coins { text-align: center; color: #a0a0c0; }
	.canvas-container { width: 100%; height: 400px; }
	button { padding: 0.6rem 2rem; background: #ffd700; color: #000; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }
	button:disabled { opacity: 0.5; }
	.result { text-align: center; margin-top: 1rem; }
	.result.win { color: #4caf50; }
	.result:not(.win) { color: #ff4444; }
	.fruits { font-size: 1.5rem; letter-spacing: 0.5rem; }
</style>
