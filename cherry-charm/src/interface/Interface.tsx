

import useGame from "../stores/store";
import Modal from "./modal/Modal";
import HelpButton from "./helpButton/HelpButton";
import "./style.css";

const Interface = () => {
  // const phase = useGame((state) => state.phase);
  const modal = useGame((state) => state.modal);
  const coins = useGame((state) => state.coins);
  const spins = useGame((state) => state.spins);

  return (
    <>
      {/* Help Button */}
      <HelpButton />

      {/* Modal */}
      {modal && <Modal />}

      {/* Logo */}
      <a
        target="_blank"
      >
        <img className="logo" src="./images/logo.png" alt="" />
      </a>

      <div className="interface">
        {/* Coins */}
        <div className="coins-section">
          <div className="coins-number">{coins}</div>
          <img className="coins-image" src="./images/coin.png" />
        </div>

        {/* Spins */}
        <div className="spins-section">
          <div className="spins-number">{spins}</div>
        </div>

        {/* Phase */}
        {/* <div >{phase.toUpperCase()}</div> */}
      </div>
    </>
  );
};

export default Interface;
