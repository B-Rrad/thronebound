import "./styles.css";
import { RingboundWebGame } from "./ringbound";

const canvas = document.querySelector<HTMLCanvasElement>("#game");

if (!canvas) {
  throw new Error("Canvas element #game was not found.");
}

const game = new RingboundWebGame(canvas);
game.start();
