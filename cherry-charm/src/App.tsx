import { useState, useEffect } from "react";
import { Canvas } from "@react-three/fiber";
import Interface from "./interface/Interface";
import Game from "./Game";

// Define the user management server URL
const userManagementServer = "http://13.61.3.232:5000";

const App = () => {
  const [windowWidth] = useState(window.innerWidth);
  const cameraPositionZ = windowWidth > 500 ? 30 : 40;

  // State to hold userId (or username) and token
  const [userId, setUserId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const id = searchParams.get('username') || "defaultUserId";
    const token = searchParams.get('token') || null;

    setUserId(id);
    setToken(token);

    if (token) {
      // Optionally store the token in local storage
      localStorage.setItem('authToken', token);

      // Verify the token
      fetch(`${userManagementServer}/verify-token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token: token, username: id }),
      })
        .then((response) => {
          // Log the status and the JSON response for debugging
          console.log("Token verification response status:", response.status);
          return response.json();
        })
        .then((data) => {
          console.log("Token verification response data:", data);
          if (data.message !== "Token is valid") {
            // If token is invalid, redirect to the login page on the other process/port
            //window.location.href = `${userManagementServer}/login`;
          }
        })
        .catch((error) => {
          console.error("Error verifying token:", error);
          // In case of an error (e.g., network issue), redirect to the login page
          //window.location.href = `${userManagementServer}/login`;
        });
    } else {
      // If there's no token, redirect to login
      //window.location.href = `${userManagementServer}/login`;
    }
  }, []);

  console.log("userId:", userId);
  console.log("token:", token);

  // Pass userId and token to the components
  return (
    <>
      <Interface userId={userId} token={token} />
      <Canvas camera={{ fov: 75, position: [0, 0, cameraPositionZ] }}>
        <Game userId={userId}
              token={token}/>
      </Canvas>
    </>
  );
};

export default App;
