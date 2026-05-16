<script lang="ts">
	let { show, message, payout }: { show: boolean; message: string | null; payout: number } = $props();
</script>

{#if show}
	<div class="overlay">
		<div class="modal">
			<h2 class:win={payout > 0} class:lose={payout === 0}>{message}</h2>
			<p>{payout > 0 ? `You won ${payout} coins!` : 'Better luck next time.'}</p>
			<a href="/blackjack" class="btn">Play Again</a>
		</div>
	</div>
{/if}

<style>
	.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; }
	.modal { background: #1a1a2e; padding: 2rem; border-radius: 12px; text-align: center; border: 1px solid #333; }
	.win { color: #4caf50; }
	.lose { color: #ff4444; }
	.btn { display: inline-block; margin-top: 1rem; padding: 0.5rem 1.5rem; background: #ffd700; color: #000; text-decoration: none; border-radius: 4px; font-weight: 600; }
</style>
