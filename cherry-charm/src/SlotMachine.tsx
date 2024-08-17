import {
  useRef,
  useEffect,
  forwardRef,
  useImperativeHandle,
  useState,
} from "react";
import { useFrame } from "@react-three/fiber";
import { Text } from "@react-three/drei";
import * as THREE from "three";
import useGame from "./stores/store";
import devLog from "./utils/functions/devLog";
import segmentToFruit from "./utils/functions/segmentToFruit";
import endgame from "./utils/functions/endgame";
import { WHEEL_SEGMENT } from "./utils/constants";
import Reel from "./Reel";
import Button from "./Button";

interface ReelGroup extends THREE.Group {
  reelSegment?: number;
  reelPosition?: number;
  reelSpinUntil?: number;
  reelStopSegment?: number;
}

interface SlotMachineProps {
  value: (0 | 1 | 2 | 3 | 4 | 5 | 6 | 7)[];
  userId: string;  // Assuming userId is passed as a prop
}

const SlotMachine = forwardRef(({ value, userId }: SlotMachineProps, ref) => {
  const fruit0 = useGame((state) => state.fruit0);
  const fruit1 = useGame((state) => state.fruit1);
  const fruit2 = useGame((state) => state.fruit2);
  const setFruit0 = useGame((state) => state.setFruit0);
  const setFruit1 = useGame((state) => state.setFruit1);
  const setFruit2 = useGame((state) => state.setFruit2);
  const phase = useGame((state) => state.phase);
  const start = useGame((state) => state.start);
  const end = useGame((state) => state.end);
  const addSpin = useGame((state) => state.addSpin);
  const coins = useGame((state) => state.coins);
  const updateCoins = useGame((state) => state.updateCoins);
  const fetchCoins = useGame((state) => state.fetchCoins);

  // Fetch initial coins when the component mounts
  useEffect(() => {
    console.log("Component mounted, userId:", userId);
    if (userId) {
      fetchCoins(userId);
    } else {
      console.error("userId is undefined. Cannot fetch initial coins.");
    }
  }, [userId, fetchCoins]);

  useEffect(() => {
    devLog("PHASE: " + phase);

    if (phase === "idle") {
      console.log("User ID:", userId); // Überprüfen, ob userId definiert ist
      const winnings = endgame(fruit0, fruit1, fruit2);
      console.log("Winnings:", winnings);
      if (userId && winnings !== 0) {  // Nur wenn userId definiert ist und winnings nicht null sind
        console.log("Updating coins for userId:", userId, "with winnings:", winnings);
        updateCoins(userId, winnings);
      } else {
        console.warn("Skipping updateCoins due to missing userId or winnings being 0.");
      }
    }
  }, [phase, fruit0, fruit1, fruit2, updateCoins, userId]);

  const reelRefs = [
    useRef<ReelGroup>(null),
    useRef<ReelGroup>(null),
    useRef<ReelGroup>(null),
  ];

  const spinSlotMachine = () => {
    console.log("Spinning slot machine");
    start();
    const min = 15;
    const max = 30;
    const getRandomStopSegment = () =>
      Math.floor(Math.random() * (max - min + 1)) + min;

    const spinReel = (reelIndex: number) => {
      const reel = reelRefs[reelIndex].current;
      if (reel) {
        // Reset rotation
        reel.rotation.x = 0;
        // Reset all attributes
        reel.reelSegment = 0;
        reel.reelPosition = 0;
        reel.reelSpinUntil = 0;
        reel.reelStopSegment = 0;
        // Clear fruits from previous spins
        setFruit0("");
        setFruit1("");
        setFruit2("");
        const stopSegment = getRandomStopSegment();
        devLog(`Stop segment of reel ${reelIndex}: ${stopSegment}`);

        reel.reelSpinUntil = stopSegment;
      }
    };

    spinReel(0);
    spinReel(1);
    spinReel(2);
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code === "Space") {
        if (phase !== "spinning") {
          if (coins > 0) {
            console.log("Space key pressed, spinning slot machine");
            spinSlotMachine();
            addSpin();
            if (userId) {
              updateCoins(userId, -1);
            } else {
              console.error("userId is undefined, cannot update coins.");
            }
          } else {
            console.warn("Not enough coins to spin the slot machine.");
          }
        } else {
          console.log("Slot machine is already spinning.");
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [phase, coins, userId, spinSlotMachine, addSpin, updateCoins]);

  useFrame(() => {
    for (let i = 0; i < reelRefs.length; i++) {
      const reel = reelRefs[i].current;
      if (reel) {
        if (reel.reelSpinUntil !== undefined) {
          if (reel.reelSegment === undefined) {
            reel.reelSegment = 0;
          }

          const targetRotationX =
            (reel.reelSpinUntil - reel.reelSegment) * WHEEL_SEGMENT;
          const rotationSpeed = 0.1;

          if (reel.rotation.x < targetRotationX) {
            reel.rotation.x += rotationSpeed;
            reel.reelSegment = Math.floor(reel.rotation.x / WHEEL_SEGMENT);
          } else if (reel.rotation.x >= targetRotationX) {
            // The reel has stopped spinning at the desired segment
            setTimeout(() => {
              end();
            }, 1000);
            const fruit = segmentToFruit(i, reel.reelSegment);

            if (fruit) {
              switch (i) {
                case 0:
                  setFruit0(fruit);
                  break;
                case 1:
                  setFruit1(fruit);
                  break;
                case 2:
                  setFruit2(fruit);
                  break;
              }
            }

            devLog(
              `Reel ${i + 1} stopped at segment ${reel.reelSegment} ${fruit}`
            );
            reel.reelSpinUntil = undefined; // Reset reelSpinUntil to stop further logging
          }
        }
      }
    }
  });

  useImperativeHandle(ref, () => ({
    reelRefs,
  }));

  const [buttonZ, setButtonZ] = useState(0);
  const [buttonY, setButtonY] = useState(-13);

  const [textZ, setTextZ] = useState(1.6);
  const [textY, setTextY] = useState(-14);

  return (
    <>
      <Reel
        ref={reelRefs[0]}
        value={value[0]}
        map={0}
        position={[-7, 0, 0]}
        rotation={[0, 0, 0]}
        scale={[10, 10, 10]}
        reelSegment={0}
      />
      <Reel
        ref={reelRefs[1]}
        value={value[1]}
        map={1}
        position={[0, 0, 0]}
        rotation={[0, 0, 0]}
        scale={[10, 10, 10]}
        reelSegment={0}
      />
      <Reel
        ref={reelRefs[2]}
        value={value[2]}
        map={2}
        position={[7, 0, 0]}
        rotation={[0, 0, 0]}
        scale={[10, 10, 10]}
        reelSegment={0}
      />
      <Button
        scale={[0.055, 0.045, 0.045]}
        position={[0, buttonY, buttonZ]}
        rotation={[-Math.PI / 8, 0, 0]}
        onClick={() => {
          if (phase !== "spinning") {
            if (coins > 0) {
              console.log("Button clicked, spinning slot machine");
              spinSlotMachine();
              addSpin();
              if (userId) {
                updateCoins(userId, -1);
              } else {
                console.error("userId is undefined, cannot update coins.");
              }
            } else {
              console.warn("Not enough coins to spin the slot machine.");
            }
          }
        }}
        onPointerDown={() => {
          setButtonZ(-1);
          setButtonY(-13.5);
        }}
        onPointerUp={() => {
          setButtonZ(0);
          setButtonY(-13);
        }}
      />
      <Text
        color="white"
        anchorX="center"
        anchorY="middle"
        position={[0, textY, textZ]}
        rotation={[-Math.PI / 8, 0, 0]}
        fontSize={3}
        font="./fonts/nickname.otf"
        onPointerDown={() => {
          setTextZ(1.3);
          setTextY(-14.1);
        }}
        onPointerUp={() => {
          setTextZ(1.6);
          setTextY(-14);
        }}
      >
        {phase === "idle" ? "GIRAR" : "GIRANDO"}
      </Text>
    </>
  );
});

export default SlotMachine;
