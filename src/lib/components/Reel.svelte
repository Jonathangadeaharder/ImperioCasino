<script lang="ts">
	import { T, useFrame } from '@threlte/core';

	let { reelIndex, spinning }: { reelIndex: number; spinning: boolean } = $props();

	let mesh: any = $state(null);
	let rotationX = $state(0);
	let startTime = $state(0);

	$effect(() => {
		if (spinning) startTime = performance.now();
	});

	useFrame(({ delta }) => {
		if (!mesh) return;
		if (spinning) {
			rotationX += delta * 8;
			mesh.rotation.x = rotationX;
		}
	});
</script>

<T.Mesh position={[-1.5 + reelIndex * 1.5, 0.5, 0.5]} bind:ref={mesh}>
	<T.CylinderGeometry args={[0.6, 0.6, 0.1, 8]} />
	<T.MeshStandardMaterial color="#222" />
</T.Mesh>
