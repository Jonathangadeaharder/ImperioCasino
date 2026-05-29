<script lang="ts">
import { T } from "@threlte/core";
import SlotLights from "$lib/components/SlotLights.svelte";
import SlotCasing from "$lib/components/SlotCasing.svelte";
import Reel from "$lib/components/Reel.svelte";

let {
	onSpin,
	coins,
	spinning,
}: { onSpin: () => void; coins: number; spinning: boolean } = $props();
</script>

<T.Group>
	<SlotLights />
	<SlotCasing />
	{#each [0, 1, 2] as i (i)}
		<Reel reelIndex={i} {spinning} />
	{/each}
	<T.Mesh
		position={[0, -2.5, 1]}
		on:click={onSpin}
	>
		<T.BoxGeometry args={[1.2, 0.4, 0.1]} />
		<T.MeshStandardMaterial color={coins > 0 && !spinning ? '#ffd700' : '#555'} />
	</T.Mesh>
</T.Group>
