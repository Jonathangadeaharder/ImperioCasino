import { useState, useEffect } from "react";  // Ensure both useState and useEffect are imported
import { Canvas } from "@react-three/fiber";
import Interface from "./interface/Interface";
import Game from "./Game";

const App = () => {
  const [windowWidth] = useState(window.innerWidth);
  const cameraPositionZ = windowWidth > 500 ? 30 : 40;

  // Extract userId from the URL
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const pathParts = window.location.pathname.split('/');
    const id = pathParts[1]; // Extract the userId from the URL
    setUserId(id || "defaultUserId"); // Set a default if no userId is found
  }, []);

  console.log("userId:", userId);

  // Pass userId to the components
  return (
    <>
      <Interface userId={userId} />  {/* Pass userId here */}
      <Canvas camera={{ fov: 75, position: [0, 0, cameraPositionZ] }}>
        <Game userId={userId} />  {/* Pass userId here */}
      </Canvas>
    </>
  );
};

export default App;
