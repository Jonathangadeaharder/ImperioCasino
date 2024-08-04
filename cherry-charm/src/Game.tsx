// In `cherry-charm/src/Game.tsx`

import { useRef } from "react";
import { OrbitControls } from "@react-three/drei";
import Lights from "./lights/Lights";
import SlotMachine from "./SlotMachine";

const Game = () => {
    const slotMachineRef = useRef();

    return (
        <>
            <color args={["#141417"]} attach="background" />
            <OrbitControls enableRotate={false} /> {/* Disable rotation */}
            <Lights />
            <SlotMachine ref={slotMachineRef} value={[1, 2, 3]} />
        </>
    );
};

export default Game;