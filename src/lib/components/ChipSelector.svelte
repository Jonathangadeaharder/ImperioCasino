<script lang="ts">
	let { wager, setWager, max, disabled = false }: {
		wager: number;
		setWager: (n: number) => void;
		max: number;
		disabled?: boolean;
	} = $props();

	const chips = [10, 25, 50, 100];
</script>

<div class="chips">
	{#each chips as chip}
		<button
			class:selected={wager === chip}
			disabled={disabled || chip > max}
			onclick={() => setWager(chip)}
		>
			{chip}
		</button>
	{/each}
</div>

<style>
	.chips { display: flex; gap: 0.5rem; }
	button {
		padding: 0.5rem 1rem;
		border: 2px solid #ffd700;
		border-radius: 50%;
		background: transparent;
		color: #ffd700;
		font-weight: 600;
		cursor: pointer;
		min-width: 48px;
		min-height: 48px;
	}
	button:disabled { opacity: 0.4; cursor: not-allowed; }
	button.selected { background: #ffd700; color: #000; }
</style>
