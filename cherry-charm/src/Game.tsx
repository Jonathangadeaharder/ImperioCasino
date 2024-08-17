import { useRef } from "react";
import { OrbitControls } from "@react-three/drei";
import Lights from "./lights/Lights";
import SlotMachine from "./SlotMachine";

interface GameProps {
  userId: string | null;  // Accept userId as a prop
}

const Game = ({ userId }: GameProps) => {
  const slotMachineRef = useRef();

  return (
    <>
      <color args={["#141417"]} attach="background" />
      <OrbitControls enableRotate={false} /> {/* Disable rotation */}
      <Lights />
      <SlotMachine ref={slotMachineRef} value={[1, 2, 3]} userId={userId} />  {/* Pass userId to SlotMachine */}
    </>
  );
};

export default Game;
