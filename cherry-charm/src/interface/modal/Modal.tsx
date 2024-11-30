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
              <span> Ganá 50 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/apple.png" />
              <img className="modal-image" src="./images/apple.png" />
              <img className="modal-image" src="./images/apple.png" />
              <span> Ganá 20 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/banana.png" />
              <img className="modal-image" src="./images/banana.png" />
              <img className="modal-image" src="./images/banana.png" />
              <span> Ganá 15 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/lemon.png" />
              <img className="modal-image" src="./images/lemon.png" />
              <img className="modal-image" src="./images/lemon.png" />
              <span> Ganá 3 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/cherry.png" />
              <img className="modal-image" src="./images/cherry.png" />
              <span> Ganá 40 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/apple.png" />
              <img className="modal-image" src="./images/apple.png" />
              <span> Ganá 10 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              <img className="modal-image" src="./images/banana.png" />
              <img className="modal-image" src="./images/banana.png" />
              <span> Ganá 5 </span>
              <img className="modal-image" src="./images/coin.png" />
            </div>
            <div className="modal-text">
              Solo se considera un par en orden de izquierda a derecha.
            </div>
            <div>
              <div>
                <a>
                  © 2024 Bar Imperio.
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
  );
};

export default Modal;
