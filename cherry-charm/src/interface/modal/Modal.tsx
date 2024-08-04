// Copyright (c) 2023 Michael Kolesidis <michael.kolesidis@gmail.com>
// Licenciado bajo la GNU Affero General Public License v3.0.
// https://www.gnu.org/licenses/gpl-3.0.html

import useGame from "../../stores/store";
import "./style.css";

const Modal = () => {
  const { setModal } = useGame();

  return (
      <div className="modal" onClick={() => setModal(false)}>
        <div className="modal-box" onClick={(e) => e.stopPropagation()}>
          <div className="modal-main">
            <div className="modal-text">
              Haz clic en el botón SPIN o presiona ESPACIO para girar.
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/cherry.png" />
              <img className="modal-image" src="./images/cherry.png" />
              <img className="modal-image" src="./images/cherry.png" />
              <span> Paga 50 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/apple.png" />
              <img className="modal-image" src="./images/apple.png" />
              <img className="modal-image" src="./images/apple.png" />
              <span> Paga 20 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/banana.png" />
              <img className="modal-image" src="./images/banana.png" />
              <img className="modal-image" src="./images/banana.png" />
              <span> Paga 15 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/lemon.png" />
              <img className="modal-image" src="./images/lemon.png" />
              <img className="modal-image" src="./images/lemon.png" />
              <span> Paga 3 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/cherry.png" />
              <img className="modal-image" src="./images/cherry.png" />
              <span> Paga 40 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/apple.png" />
              <img className="modal-image" src="./images/apple.png" />
              <span> Paga 10 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/banana.png" />
              <img className="modal-image" src="./images/banana.png" />
              <span> Paga 5 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              Ten en cuenta que las máquinas tragamonedas solo consideran un par como coincidencia si están en orden de izquierda a derecha.
            </div>
            <div className="modal-text">
              Extra: Haz clic y mantén presionado en cualquier lugar y mueve el cursor para explorar la escena 3D.
            </div>
            <div>
              <div>
                <a>
                  © 2024 Bar Imperio.
                </a>
              </div>
              <div className="modal-about">
                <a href="https://www.gnu.org/licenses/agpl-3.0.en.html">
                  Licenciado bajo la GNU AGPL 3.0
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
  );
};

export default Modal;
