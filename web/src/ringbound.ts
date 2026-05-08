import heroData from "../../data/hero_cards.json";
import dominionData from "../../data/dominions.json";
import realmData from "../../data/realm_cards.json";

type Player = "P1" | "P2";
type GameState = "loading" | "splash" | "drafting" | "playing" | "gameover";
type PlayPhase = "ATTACK" | "DEFEND" | "REINFORCE";
type CardKind = "realm" | "hero";
type AiKind = "Random" | "Greedy" | "Strategic";
type GameMode = "2p" | "random-ai" | "greedy-ai" | "strategic-ai";

type RealmCard = {
  id: string;
  name: string;
  suit: string;
  rank: number;
  image: string;
};

type HeroCard = {
  id: string;
  name: string;
  faction: string;
  power: string;
  image: string;
};

type Card = RealmCard | HeroCard;

type CardHitbox = {
  kind: "draft-realm" | "draft-hero" | "hand" | "attack" | "button" | "suit" | "noop";
  x: number;
  y: number;
  w: number;
  h: number;
  index?: number;
  label?: string;
  suit?: string;
  enabled?: boolean;
  card?: Card;
};

type PendingAction =
  | { type: "aragorn_return"; owner: Player; hero: HeroCard }
  | { type: "saruman_exchange"; owner: Player; hero: HeroCard; targetCard: RealmCard }
  | { type: "choose_suit"; owner: Player; hero: HeroCard; mode: "gollum_trump" | "wormtongue_block" }
  | { type: "hero_attack_card"; owner: Player; hero: HeroCard; mode: "legolas_bonus" | "balrog_attack" };

type RoundEffects = {
  trumpDisabled: boolean;
  temporaryTrumpSuit: string | null;
  nazgulActive: boolean;
  wormtongueSuit: string | null;
  legolasBonus: number;
  balrogActive: Player | null;
  balrogAttackCard: RealmCard | null;
  gandalfRanks: number[];
};

type AiAction =
  | { type: "realm"; card: RealmCard }
  | { type: "hero"; card: HeroCard }
  | { type: "concede" }
  | { type: "end" }
  | { type: "pass" };

const MAX_REALM_CARDS = 6;
const MAX_HERO_CARDS = 4;
const DRAFT_REALM_DISPLAY_COUNT = 10;
const DRAFT_HERO_DISPLAY_COUNT = 8;
const WOUND_LIMIT = 6;
const CARD_PNG_URLS = import.meta.glob("../../output/card_placeholders/**/*.png", {
  eager: true,
  query: "?url",
  import: "default"
}) as Record<string, string>;
const CARD_SVG_URLS = import.meta.glob("../../output/card_placeholders/**/*.svg", {
  eager: true,
  query: "?url",
  import: "default"
}) as Record<string, string>;
const CARD_ASSET_URLS = { ...CARD_PNG_URLS, ...CARD_SVG_URLS };
const MUSIC_URLS = Object.entries(
  import.meta.glob("../../music/*.mp3", {
    eager: true,
    query: "?url",
    import: "default"
  }) as Record<string, string>
)
  .sort(([left], [right]) => left.localeCompare(right))
  .map(([, url]) => url);
const SUIT_COLORS: Record<string, string> = Object.fromEntries(
  dominionData.dominions.map((dominion) => [dominion.name, dominion.color.hex])
);
const THEME = {
  bg: "#0d0b0e",
  surface: "#1a1520",
  surfaceSoft: "rgba(18, 14, 22, 0.78)",
  gold: "#c9a84c",
  ember: "#b84a2e",
  text: "#e8dfc8",
  muted: "#7a6f5e",
  border: "#534838",
  selected: "#e0c35f",
  disabled: "rgba(0, 0, 0, 0.55)"
};
const BACKGROUND_URL = new URL("../../background.jpg", import.meta.url).href;

function isRealm(card: Card): card is RealmCard {
  return "suit" in card;
}

function isHero(card: Card): card is HeroCard {
  return "faction" in card;
}

function getOpponent(player: Player): Player {
  return player === "P1" ? "P2" : "P1";
}

function shuffle<T>(items: T[]): T[] {
  const next = [...items];
  for (let i = next.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [next[i], next[j]] = [next[j], next[i]];
  }
  return next;
}

function drawWrappedText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
  maxLines = 3
) {
  const words = text.split(/\s+/);
  const lines: string[] = [];
  let line = "";

  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (ctx.measureText(candidate).width <= maxWidth) {
      line = candidate;
    } else {
      if (line) {
        lines.push(line);
      }
      line = word;
      if (lines.length >= maxLines) {
        break;
      }
    }
  }

  if (line && lines.length < maxLines) {
    lines.push(line);
  }

  lines.forEach((current, index) => {
    ctx.fillText(ellipsizeText(ctx, current, maxWidth), x, y + index * lineHeight);
  });
}

function ellipsizeText(ctx: CanvasRenderingContext2D, text: string, maxWidth: number) {
  if (ctx.measureText(text).width <= maxWidth) {
    return text;
  }
  let next = text;
  while (next.length > 1 && ctx.measureText(`${next}...`).width > maxWidth) {
    next = next.slice(0, -1);
  }
  return `${next.trimEnd()}...`;
}

function drawFittedText(ctx: CanvasRenderingContext2D, text: string, x: number, y: number, maxWidth: number) {
  ctx.fillText(ellipsizeText(ctx, text, maxWidth), x, y);
}

function drawCenteredFittedText(ctx: CanvasRenderingContext2D, text: string, centerX: number, y: number, maxWidth: number) {
  ctx.fillText(ellipsizeText(ctx, text, maxWidth), centerX, y);
}

function rgba(color: string, alpha: number) {
  if (!color.startsWith("#")) {
    return color;
  }
  const hex = color.slice(1);
  const bigint = Number.parseInt(hex.length === 3 ? hex.split("").map((char) => char + char).join("") : hex, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export class RingboundWebGame {
  private readonly canvas: HTMLCanvasElement;
  private readonly ctx: CanvasRenderingContext2D;
  private hitboxes: CardHitbox[] = [];
  private width = 1280;
  private height = 760;
  private backgroundImage: HTMLImageElement | null = null;
  private cardImageCache = new Map<string, HTMLImageElement>();
  private mouseX = -1;
  private mouseY = -1;
  private hoveredHitbox: CardHitbox | null = null;
  private lastWounds: Record<Player, number> = { P1: 0, P2: 0 };
  private woundFlashUntil: Record<Player, number> = { P1: 0, P2: 0 };
  private music: HTMLAudioElement | null = null;
  private musicEnabled = false;
  private musicIndex = 0;
  private musicPlaylist: string[] = [];
  private showHowToPlay = false;
  private mode: GameMode = "2p";
  private aiPlayer: Player | null = null;
  private aiKind: AiKind | null = null;
  private aiTimer: number | null = null;
  private aiActing = false;

  private state: GameState = "loading";
  private statusMessage = "Loading Thronebound...";
  private gameLog: string[] = [];
  private logScroll = 0;

  private allRealmCards: RealmCard[] = [];
  private allHeroCards: HeroCard[] = [];
  private allSuits: string[] = [];
  private realmDeck: RealmCard[] = [];
  private heroDeck: HeroCard[] = [];
  private trumpCard: RealmCard | null = null;
  private trumpSuit: string | null = null;

  private p1Hand: RealmCard[] = [];
  private p2Hand: RealmCard[] = [];
  private p1Heroes: HeroCard[] = [];
  private p2Heroes: HeroCard[] = [];
  private wounds: Record<Player, number> = { P1: 0, P2: 0 };

  private currentDrafter: Player = "P1";
  private firstAttacker: Player = "P1";
  private attacker: Player = "P1";
  private defender: Player = "P2";
  private currentPlayer: Player = "P1";
  private playPhase: PlayPhase = "ATTACK";

  private realmDraft: RealmCard[] = [];
  private heroDraft: HeroCard[] = [];
  private tableAttacks: RealmCard[] = [];
  private tableDefenses: Card[] = [];
  private discardPile: Card[] = [];
  private heroDiscard: HeroCard[] = [];
  private pendingAction: PendingAction | null = null;
  private revealedHand: { viewer: Player; target: Player } | null = null;
  private roundEffects: RoundEffects = this.newRoundEffects();

  private winner: Player | null = null;
  private winReason = "";

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw new Error("2D canvas is not available.");
    }
    this.ctx = ctx;
    this.backgroundImage = new Image();
    this.backgroundImage.src = BACKGROUND_URL;
    if (MUSIC_URLS.length > 0) {
      this.musicPlaylist = shuffle(MUSIC_URLS);
      this.music = new Audio();
      this.music.volume = 0.42;
      this.music.addEventListener("ended", () => this.advanceMusic());
    }
  }

  start() {
    window.addEventListener("resize", () => this.resize());
    this.canvas.addEventListener("click", (event) => this.handleClick(event));
    this.canvas.addEventListener("mousemove", (event) => this.handleMouseMove(event));
    this.canvas.addEventListener("mouseleave", () => {
      this.mouseX = -1;
      this.mouseY = -1;
      this.hoveredHitbox = null;
      this.canvas.style.cursor = "default";
    });
    this.resize();
    void this.loadData();
    requestAnimationFrame(() => this.frame());
  }

  private async loadData() {
    try {
      this.allRealmCards = realmData.realm_cards;
      this.allHeroCards = heroData.hero_cards;
      this.allSuits = [...new Set(this.allRealmCards.map((card) => card.suit))].sort();
      this.state = "splash";
      this.setStatus("Click Start to begin a local two-player game.");
    } catch (error) {
      this.setStatus(`Could not load card data: ${String(error)}`);
    }
  }

  private frame() {
    this.draw();
    requestAnimationFrame(() => this.frame());
  }

  private resize() {
    const dpr = window.devicePixelRatio || 1;
    this.width = Math.max(1024, window.innerWidth);
    this.height = Math.max(640, window.innerHeight);
    this.canvas.width = Math.floor(this.width * dpr);
    this.canvas.height = Math.floor(this.height * dpr);
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  private setStatus(message: string) {
    this.statusMessage = message;
    if (this.shouldLogStatus(message) && this.gameLog[this.gameLog.length - 1] !== message) {
      this.gameLog.push(message);
      this.gameLog = this.gameLog.slice(-10);
      this.logScroll = Math.min(this.logScroll, Math.max(0, this.gameLog.length - 5));
    }
  }

  private shouldLogStatus(message: string) {
    if (this.state === "drafting" && (message.endsWith(" is drafting.") || message.endsWith(" drafts first."))) {
      return false;
    }
    return true;
  }

  private newRoundEffects(): RoundEffects {
    return {
      trumpDisabled: false,
      temporaryTrumpSuit: null,
      nazgulActive: false,
      wormtongueSuit: null,
      legolasBonus: 0,
      balrogActive: null,
      balrogAttackCard: null,
      gandalfRanks: []
    };
  }

  private resetGame() {
    if (this.aiTimer !== null) {
      window.clearTimeout(this.aiTimer);
      this.aiTimer = null;
    }
    this.realmDeck = [];
    this.heroDeck = [];
    this.trumpCard = null;
    this.trumpSuit = null;
    this.p1Hand = [];
    this.p2Hand = [];
    this.p1Heroes = [];
    this.p2Heroes = [];
    this.wounds = { P1: 0, P2: 0 };
    this.currentDrafter = "P1";
    this.firstAttacker = "P1";
    this.attacker = "P1";
    this.defender = "P2";
    this.currentPlayer = "P1";
    this.playPhase = "ATTACK";
    this.realmDraft = [];
    this.heroDraft = [];
    this.tableAttacks = [];
    this.tableDefenses = [];
    this.discardPile = [];
    this.heroDiscard = [];
    this.pendingAction = null;
    this.revealedHand = null;
    this.roundEffects = this.newRoundEffects();
    this.winner = null;
    this.winReason = "";
    this.gameLog = [];
    this.mode = "2p";
    this.aiPlayer = null;
    this.aiKind = null;
  }

  private setupGame(mode: GameMode = "2p") {
    this.resetGame();
    this.mode = mode;
    this.aiPlayer = mode === "2p" ? null : "P2";
    this.aiKind = this.aiKindFromMode(mode);
    this.realmDeck = shuffle(this.allRealmCards.map((card) => ({ ...card })));
    this.heroDeck = shuffle(this.allHeroCards.map((card) => ({ ...card })));

    const p1Initial = this.realmDeck.pop();
    const p2Initial = this.realmDeck.pop();
    const trump = this.realmDeck.pop();
    if (!p1Initial || !p2Initial || !trump) {
      this.state = "gameover";
      this.winReason = "At least three realm cards are required to start.";
      return;
    }

    this.p1Hand.push(p1Initial);
    this.p2Hand.push(p2Initial);
    this.trumpCard = trump;
    this.trumpSuit = trump.suit;

    if (p1Initial.rank > p2Initial.rank) {
      this.currentDrafter = "P1";
      this.firstAttacker = "P2";
    } else if (p2Initial.rank > p1Initial.rank) {
      this.currentDrafter = "P2";
      this.firstAttacker = "P1";
    } else {
      this.currentDrafter = Math.random() < 0.5 ? "P1" : "P2";
      this.firstAttacker = getOpponent(this.currentDrafter);
    }

    this.realmDraft = this.realmDeck.splice(-DRAFT_REALM_DISPLAY_COUNT).reverse();
    this.heroDraft = this.heroDeck.splice(-DRAFT_HERO_DISPLAY_COUNT).reverse();
    this.state = "drafting";
    this.setStatus(`${this.playerLabel(this.currentDrafter)} drafts first.`);
    this.scheduleAiTurn();
  }

  private getPlayerRealmHand(player: Player) {
    return player === "P1" ? this.p1Hand : this.p2Hand;
  }

  private getPlayerHeroHand(player: Player) {
    return player === "P1" ? this.p1Heroes : this.p2Heroes;
  }

  private getPlayerTotalCards(player: Player) {
    return this.getPlayerRealmHand(player).length + this.getPlayerHeroHand(player).length;
  }

  private getKnownOpponentCards(player: Player) {
    if (this.revealedHand?.viewer === player) {
      return [...this.getPlayerRealmHand(getOpponent(player))];
    }
    return null;
  }

  private isAiPlayer(player: Player) {
    return this.aiPlayer === player;
  }

  private playerLabel(player: Player) {
    return this.isAiPlayer(player) ? `${this.aiKind ?? "Random"} AI` : "Player";
  }

  private aiKindFromMode(mode: GameMode): AiKind | null {
    if (mode === "random-ai") {
      return "Random";
    }
    if (mode === "greedy-ai") {
      return "Greedy";
    }
    if (mode === "strategic-ai") {
      return "Strategic";
    }
    return null;
  }

  private isHumanTurn() {
    if (this.state === "drafting") {
      return !this.isAiPlayer(this.currentDrafter);
    }
    if (this.state === "playing") {
      return !this.isAiPlayer(this.currentPlayer);
    }
    return true;
  }

  private getEffectiveTrumpSuit() {
    if (this.roundEffects.trumpDisabled) {
      return null;
    }
    return this.roundEffects.temporaryTrumpSuit ?? this.trumpSuit;
  }

  private isTrumpCard(card: RealmCard) {
    const effectiveTrump = this.getEffectiveTrumpSuit();
    return effectiveTrump !== null && card.suit === effectiveTrump;
  }

  private getCurrentAttackCard() {
    if (this.tableAttacks.length > this.tableDefenses.length) {
      return this.tableAttacks[this.tableAttacks.length - 1] ?? null;
    }
    return null;
  }

  private getReinforceRanks() {
    const ranks: number[] = [];
    for (const card of [...this.tableAttacks, ...this.tableDefenses]) {
      if (isRealm(card)) {
        ranks.push(card.rank);
      }
    }
    return ranks;
  }

  private getAllowedAttackRanks() {
    const ranks = [...this.getReinforceRanks()];
    for (const rank of this.roundEffects.gandalfRanks) {
      if (!ranks.includes(rank)) {
        ranks.push(rank);
      }
    }
    return ranks;
  }

  private legalAttackCards(player: Player) {
    return this.getPlayerRealmHand(player).filter((card) => this.canAttackWithCard(card));
  }

  private legalDefenseCards(player: Player) {
    return this.getPlayerRealmHand(player).filter((card) => this.canDefendWithCard(card, this.getCurrentAttackCard()));
  }

  private usableHeroes(player: Player) {
    const previousPlayer = this.currentPlayer;
    this.currentPlayer = player;
    try {
      return this.getPlayerHeroHand(player).filter((hero) => this.canUseHero(hero));
    } finally {
      this.currentPlayer = previousPlayer;
    }
  }

  private canDraftCardType(player: Player, cardType: CardKind) {
    if (cardType === "realm") {
      return this.getPlayerRealmHand(player).length < MAX_REALM_CARDS;
    }
    return this.getPlayerHeroHand(player).length < MAX_HERO_CARDS;
  }

  private draftingHasAvailablePick(player: Player) {
    return (
      (this.canDraftCardType(player, "realm") && this.realmDraft.length > 0) ||
      (this.canDraftCardType(player, "hero") && this.heroDraft.length > 0)
    );
  }

  private draftingIsComplete() {
    const full =
      this.p1Hand.length >= MAX_REALM_CARDS &&
      this.p2Hand.length >= MAX_REALM_CARDS &&
      this.p1Heroes.length >= MAX_HERO_CARDS &&
      this.p2Heroes.length >= MAX_HERO_CARDS;
    const noPicks = !this.draftingHasAvailablePick("P1") && !this.draftingHasAvailablePick("P2");
    return full || noPicks;
  }

  private attemptDraft(index: number, cardType: CardKind) {
    if (!this.canDraftCardType(this.currentDrafter, cardType)) {
      return;
    }
    if (cardType === "realm") {
      const [card] = this.realmDraft.splice(index, 1);
      if (!card) {
        return;
      }
      this.getPlayerRealmHand(this.currentDrafter).push(card);
    } else {
      const [card] = this.heroDraft.splice(index, 1);
      if (!card) {
        return;
      }
      this.getPlayerHeroHand(this.currentDrafter).push(card);
    }
    this.switchDrafter();
    this.checkDraftComplete();
    this.scheduleAiTurn();
  }

  private switchDrafter() {
    let nextDrafter = getOpponent(this.currentDrafter);
    if (!this.draftingHasAvailablePick(nextDrafter) && this.draftingHasAvailablePick(this.currentDrafter)) {
      nextDrafter = this.currentDrafter;
    }
    this.currentDrafter = nextDrafter;
    this.setStatus(`${this.playerLabel(this.currentDrafter)} is drafting.`);
  }

  private checkDraftComplete() {
    if (!this.draftingIsComplete()) {
      return;
    }
    this.attacker = this.firstAttacker;
    this.defender = getOpponent(this.attacker);
    this.currentPlayer = this.attacker;
    this.playPhase = "ATTACK";
    this.state = "playing";
    this.setStatus(`${this.playerLabel(this.attacker)} opens the first attack.`);
    this.scheduleAiTurn();
  }

  private canDefendWithCard(defenseCard: RealmCard, attackCard: RealmCard | null) {
    if (!attackCard) {
      return false;
    }
    if (this.roundEffects.wormtongueSuit === defenseCard.suit) {
      return false;
    }
    if (this.roundEffects.nazgulActive && !this.isTrumpCard(defenseCard)) {
      return false;
    }
    if (defenseCard.suit === attackCard.suit && defenseCard.rank > attackCard.rank) {
      return true;
    }
    if (this.isTrumpCard(defenseCard) && !this.isTrumpCard(attackCard)) {
      return true;
    }
    if (this.isTrumpCard(defenseCard) && this.isTrumpCard(attackCard)) {
      return defenseCard.rank > attackCard.rank;
    }
    return false;
  }

  private canAttackWithCard(attackCard: RealmCard) {
    const forcedRanks = this.roundEffects.gandalfRanks;
    if (this.playPhase === "ATTACK") {
      if (forcedRanks.length > 0) {
        return forcedRanks.includes(attackCard.rank);
      }
      return true;
    }
    if (this.playPhase !== "REINFORCE") {
      return false;
    }
    if (this.roundEffects.legolasBonus > 0) {
      return true;
    }
    const validRanks = this.getAllowedAttackRanks();
    if (validRanks.length === 0) {
      return true;
    }
    return validRanks.includes(attackCard.rank);
  }

  private getSarumanTargetCard() {
    const defenderHand = [...this.getPlayerRealmHand(this.defender)];
    if (defenderHand.length === 0) {
      return null;
    }
    const effectiveTrump = this.getEffectiveTrumpSuit();
    const trumpCards = defenderHand.filter((card) => effectiveTrump !== null && card.suit === effectiveTrump);
    const candidates = trumpCards.length > 0 ? trumpCards : defenderHand;
    return candidates.reduce((best, card) => (card.rank > best.rank ? card : best), candidates[0]!);
  }

  private canUseHero(heroCard: HeroCard) {
    if (this.pendingAction !== null) {
      return false;
    }
    const heroId = heroCard.id;
    const realmCount = this.getPlayerRealmHand(this.currentPlayer).length;
    const attackCard = this.getCurrentAttackCard();
    const legalAttackExists = this.getPlayerRealmHand(this.currentPlayer).some((card) => this.canAttackWithCard(card));

    if (heroId === "aragorn") {
      return this.currentPlayer === this.attacker && ["ATTACK", "REINFORCE"].includes(this.playPhase) && this.tableAttacks.length > 0;
    }
    if (heroId === "legolas") {
      return this.currentPlayer === this.attacker && ["ATTACK", "REINFORCE"].includes(this.playPhase) && realmCount > 0 && this.roundEffects.legolasBonus === 0;
    }
    if (heroId === "gandalf") {
      return this.currentPlayer === this.defender && this.playPhase === "DEFEND" && attackCard !== null && !this.isTrumpCard(attackCard);
    }
    if (heroId === "galadriel") {
      return this.wounds[this.currentPlayer] > 0;
    }
    if (heroId === "frodo") {
      return this.currentPlayer === this.attacker && ["ATTACK", "REINFORCE"].includes(this.playPhase) && !this.roundEffects.trumpDisabled;
    }
    if (heroId === "boromir") {
      return this.currentPlayer === this.defender && this.playPhase === "DEFEND" && attackCard !== null;
    }
    if (heroId === "nazgul") {
      return this.currentPlayer === this.attacker && ["ATTACK", "REINFORCE"].includes(this.playPhase) && !this.roundEffects.nazgulActive && this.getEffectiveTrumpSuit() !== null;
    }
    if (heroId === "saruman") {
      return this.currentPlayer === this.attacker && this.playPhase === "ATTACK" && this.tableAttacks.length === 0 && realmCount > 0 && this.getSarumanTargetCard() !== null;
    }
    if (heroId === "sauron") {
      return this.currentPlayer === this.attacker && this.playPhase === "ATTACK" && this.tableAttacks.length === 0 && this.revealedHand === null;
    }
    if (heroId === "balrog") {
      return this.currentPlayer === this.attacker && ["ATTACK", "REINFORCE"].includes(this.playPhase) && this.roundEffects.balrogActive === null && legalAttackExists;
    }
    if (heroId === "gollum") {
      return this.currentPlayer === this.attacker && ["ATTACK", "REINFORCE"].includes(this.playPhase) && !this.roundEffects.trumpDisabled && this.roundEffects.temporaryTrumpSuit === null;
    }
    if (heroId === "wormtongue") {
      return this.currentPlayer === this.attacker && ["ATTACK", "REINFORCE"].includes(this.playPhase) && this.roundEffects.wormtongueSuit === null;
    }
    return false;
  }

  private heroName(heroId: string) {
    return this.allHeroCards.find((card) => card.id === heroId)?.name ?? heroId;
  }

  private canSelectHeroAttackCard(card: RealmCard) {
    if (this.pendingAction?.type !== "hero_attack_card") {
      return false;
    }
    if (!this.getPlayerRealmHand(this.pendingAction.owner).includes(card)) {
      return false;
    }
    if (this.pendingAction.mode === "legolas_bonus") {
      return true;
    }
    return this.canAttackWithCard(card);
  }

  private discardCard(card: Card) {
    this.discardPile.push(card);
    if (isHero(card)) {
      this.heroDiscard.push(card);
    }
  }

  private consumeHeroCard(player: Player, heroCard: HeroCard) {
    const hand = this.getPlayerHeroHand(player);
    const index = hand.indexOf(heroCard);
    if (index >= 0) {
      hand.splice(index, 1);
      this.discardCard(heroCard);
    }
  }

  private removeRandomCardFromPlayer(player: Player) {
    const realmHand = this.getPlayerRealmHand(player);
    const heroHand = this.getPlayerHeroHand(player);
    const combined: Card[] = [...realmHand, ...heroHand];
    if (combined.length === 0) {
      return null;
    }
    const discarded = combined[Math.floor(Math.random() * combined.length)];
    if (isRealm(discarded)) {
      realmHand.splice(realmHand.indexOf(discarded), 1);
    } else {
      heroHand.splice(heroHand.indexOf(discarded), 1);
    }
    this.discardCard(discarded);
    return discarded;
  }

  private attemptHeroPlay(heroCard: HeroCard) {
    if (!this.canUseHero(heroCard)) {
      return;
    }
    const heroId = heroCard.id;
    if (heroId === "aragorn") {
      this.pendingAction = { type: "aragorn_return", owner: this.currentPlayer, hero: heroCard };
      this.setStatus(`${heroCard.name}: choose one attack card on the table.`);
      return;
    }
    if (heroId === "saruman") {
      const targetCard = this.getSarumanTargetCard();
      if (!targetCard) {
        return;
      }
      this.pendingAction = { type: "saruman_exchange", owner: this.currentPlayer, hero: heroCard, targetCard };
      this.setStatus(`${heroCard.name}: choose one realm card to swap with ${targetCard.name}.`);
      return;
    }
    if (heroId === "gollum") {
      this.pendingAction = { type: "choose_suit", owner: this.currentPlayer, hero: heroCard, mode: "gollum_trump" };
      this.setStatus(`${heroCard.name}: choose the temporary crown suit.`);
      return;
    }
    if (heroId === "wormtongue") {
      this.pendingAction = { type: "choose_suit", owner: this.currentPlayer, hero: heroCard, mode: "wormtongue_block" };
      this.setStatus(`${heroCard.name}: choose the dominion the defender cannot play.`);
      return;
    }
    if (heroId === "legolas") {
      this.pendingAction = { type: "hero_attack_card", owner: this.currentPlayer, hero: heroCard, mode: "legolas_bonus" };
      this.setStatus(`${heroCard.name}: choose one realm card to attack with.`);
      return;
    }
    if (heroId === "balrog") {
      this.pendingAction = { type: "hero_attack_card", owner: this.currentPlayer, hero: heroCard, mode: "balrog_attack" };
      this.setStatus(`${heroCard.name}: choose one legal realm attack card.`);
      return;
    }
    if (heroId === "galadriel") {
      const before = this.wounds[this.currentPlayer];
      this.wounds[this.currentPlayer] = Math.max(0, before - 2);
      this.consumeHeroCard(this.currentPlayer, heroCard);
      this.setStatus(`${heroCard.name} heals ${before - this.wounds[this.currentPlayer]} wound(s) for ${this.currentPlayer}.`);
    } else {
      this.consumeHeroCard(this.currentPlayer, heroCard);
      if (heroId === "gandalf") {
        this.resolveGandalf();
      } else if (heroId === "frodo") {
        this.roundEffects.trumpDisabled = true;
        this.roundEffects.temporaryTrumpSuit = null;
        this.setStatus(`${heroCard.name} disables the crown suit for the rest of the round.`);
      } else if (heroId === "boromir") {
        this.resolveBoromir();
      } else if (heroId === "nazgul") {
        this.roundEffects.nazgulActive = true;
        this.setStatus(`${heroCard.name} forces the defender to use crown cards only.`);
      } else if (heroId === "sauron") {
        this.revealedHand = { viewer: this.currentPlayer, target: getOpponent(this.currentPlayer) };
        this.setStatus(`${heroCard.name} reveals ${this.revealedHand.target}'s hand.`);
      }
    }
    this.checkGameOver();
  }

  private resolveGandalf() {
    const attackCard = this.getCurrentAttackCard();
    if (!attackCard) {
      return;
    }
    const playedRanks = this.getReinforceRanks();
    const removedAttack = this.tableAttacks.pop();
    if (removedAttack) {
      this.discardCard(removedAttack);
    }
    this.roundEffects.gandalfRanks = playedRanks;
    if (this.getPlayerTotalCards(this.defender) === 0 && this.tableAttacks.length === this.tableDefenses.length) {
      this.endRound(false, false);
      return;
    }
    this.syncTurnAfterTableChange();
    this.setStatus(`${this.heroName("gandalf")} cancels the latest non-crown attack.`);
  }

  private resolveBoromir() {
    if (!this.getCurrentAttackCard()) {
      return;
    }
    this.tableDefenses.push({ id: "boromir_guard", name: this.heroName("boromir"), faction: "Legend", power: "Auto-defense", image: "" });
    const discarded = this.removeRandomCardFromPlayer(this.attacker);
    if (this.getPlayerTotalCards(this.defender) === 0) {
      this.endRound(false, false);
      return;
    }
    this.playPhase = "REINFORCE";
    this.currentPlayer = this.attacker;
    const heroName = this.heroName("boromir");
    this.setStatus(discarded ? `${heroName} auto-defends. ${this.attacker} discards ${discarded.name}.` : `${heroName} auto-defends.`);
  }

  private resolveSuitChoice(suit: string) {
    if (this.pendingAction?.type !== "choose_suit") {
      return;
    }
    const { owner, hero, mode } = this.pendingAction;
    this.consumeHeroCard(owner, hero);
    if (mode === "gollum_trump") {
      this.roundEffects.temporaryTrumpSuit = suit;
      this.setStatus(`${hero.name} sets crown to ${suit} for this round.`);
    } else {
      this.roundEffects.wormtongueSuit = suit;
      this.setStatus(`${hero.name} forbids ${suit} for the defender.`);
    }
    this.pendingAction = null;
    this.currentPlayer = owner;
  }

  private resolveAragorn(attackIndex: number) {
    if (this.pendingAction?.type !== "aragorn_return") {
      return;
    }
    if (attackIndex < 0 || attackIndex >= this.tableAttacks.length) {
      return;
    }
    const { owner, hero } = this.pendingAction;
    const [returnedAttack] = this.tableAttacks.splice(attackIndex, 1);
    this.getPlayerRealmHand(owner).push(returnedAttack);
    if (attackIndex < this.tableDefenses.length) {
      const [removedDefense] = this.tableDefenses.splice(attackIndex, 1);
      this.discardCard(removedDefense);
    }
    this.consumeHeroCard(owner, hero);
    this.pendingAction = null;
    if (this.getPlayerTotalCards(this.defender) === 0 && this.tableAttacks.length === this.tableDefenses.length) {
      this.endRound(false, false);
      return;
    }
    this.syncTurnAfterTableChange();
    this.setStatus(`${hero.name} returns an attack card to hand.`);
  }

  private resolveSarumanExchange(chosenCard: RealmCard) {
    if (this.pendingAction?.type !== "saruman_exchange") {
      return;
    }
    const { owner, hero, targetCard } = this.pendingAction;
    const ownerRealm = this.getPlayerRealmHand(owner);
    const defenderRealm = this.getPlayerRealmHand(this.defender);
    if (!ownerRealm.includes(chosenCard) || !defenderRealm.includes(targetCard)) {
      return;
    }
    ownerRealm.splice(ownerRealm.indexOf(chosenCard), 1);
    defenderRealm.splice(defenderRealm.indexOf(targetCard), 1);
    ownerRealm.push(targetCard);
    defenderRealm.push(chosenCard);
    this.consumeHeroCard(owner, hero);
    this.pendingAction = null;
    this.setStatus(`${hero.name} swaps ${chosenCard.name} for ${targetCard.name}.`);
  }

  private resolveHeroAttackCard(chosenCard: RealmCard) {
    if (this.pendingAction?.type !== "hero_attack_card" || !this.canSelectHeroAttackCard(chosenCard)) {
      return;
    }
    const { owner, hero, mode } = this.pendingAction;
    this.pendingAction = null;
    this.currentPlayer = owner;
    this.consumeHeroCard(owner, hero);
    if (mode === "legolas_bonus") {
      this.roundEffects.legolasBonus = 1;
    } else {
      this.roundEffects.balrogActive = owner;
      this.roundEffects.balrogAttackCard = chosenCard;
    }
    this.attemptPlayCard(chosenCard);
    if (this.state !== "gameover") {
      this.setStatus(mode === "legolas_bonus" ? `${hero.name} joins with ${chosenCard.name}.` : `${hero.name} charges with ${chosenCard.name}.`);
    }
  }

  private handleHandCardClick(card: Card) {
    if (this.pendingAction?.type === "saruman_exchange") {
      if (isRealm(card)) {
        this.resolveSarumanExchange(card);
      }
      return;
    }
    if (this.pendingAction?.type === "hero_attack_card") {
      if (isRealm(card)) {
        this.resolveHeroAttackCard(card);
      }
      return;
    }
    if (isHero(card)) {
      this.attemptHeroPlay(card);
      return;
    }
    this.attemptPlayCard(card);
  }

  private attemptPlayCard(card: RealmCard) {
    if (this.isAiPlayer(this.currentPlayer) && !this.aiActing) {
      return;
    }
    const currentHand = this.getPlayerRealmHand(this.currentPlayer);
    if (!currentHand.includes(card)) {
      return;
    }
    if (["ATTACK", "REINFORCE"].includes(this.playPhase) && !this.canAttackWithCard(card)) {
      return;
    }
    if (this.playPhase === "DEFEND" && !this.canDefendWithCard(card, this.getCurrentAttackCard())) {
      return;
    }
    currentHand.splice(currentHand.indexOf(card), 1);

    if (this.playPhase === "ATTACK" || this.playPhase === "REINFORCE") {
      this.tableAttacks.push(card);
      if (this.roundEffects.gandalfRanks.length > 0) {
        this.roundEffects.gandalfRanks = [];
      }
      if (this.roundEffects.legolasBonus > 0) {
        this.roundEffects.legolasBonus -= 1;
      }
      this.playPhase = "DEFEND";
      this.currentPlayer = this.defender;
      this.setStatus(`${this.defender} must defend ${card.name}.`);
    } else {
      this.tableDefenses.push(card);
      if (this.getPlayerTotalCards(this.defender) === 0) {
        this.endRound(false, false);
      } else {
        this.playPhase = "REINFORCE";
        this.currentPlayer = this.attacker;
        this.setStatus(`${this.attacker} may reinforce or end the attack.`);
      }
    }
    this.checkGameOver();
    this.scheduleAiTurn();
  }

  private concedeDefense() {
    if (this.isAiPlayer(this.currentPlayer) && !this.aiActing) {
      return;
    }
    if (this.playPhase !== "DEFEND" || this.pendingAction !== null) {
      return;
    }
    this.wounds[this.defender] += 1;
    this.setStatus(`${this.defender} takes a wound.`);
    this.endRound(true, true);
    this.scheduleAiTurn();
  }

  private syncTurnAfterTableChange() {
    if (this.tableAttacks.length > this.tableDefenses.length) {
      this.playPhase = "DEFEND";
      this.currentPlayer = this.defender;
      this.setStatus(`${this.defender} must answer the latest attack.`);
    } else if (this.tableAttacks.length > 0) {
      this.playPhase = "REINFORCE";
      this.currentPlayer = this.attacker;
      this.setStatus(`${this.attacker} may reinforce or end the attack.`);
    } else if (this.roundEffects.gandalfRanks.length > 0) {
      this.playPhase = "REINFORCE";
      this.currentPlayer = this.attacker;
      this.setStatus(`${this.attacker} must continue with a played rank or end the attack.`);
    } else {
      this.playPhase = "ATTACK";
      this.currentPlayer = this.attacker;
      this.setStatus(`${this.attacker} may lead a fresh attack.`);
    }
  }

  private clearRoundState() {
    this.tableAttacks = [];
    this.tableDefenses = [];
    this.playPhase = "ATTACK";
    this.currentPlayer = this.attacker;
    this.pendingAction = null;
    this.revealedHand = null;
    this.roundEffects = this.newRoundEffects();
  }

  private endRound(defenderTookWound: boolean, pickupDefenses: boolean) {
    const balrogAttack = this.roundEffects.balrogAttackCard;
    const balrogFullyDefended =
      balrogAttack !== null &&
      this.tableAttacks.includes(balrogAttack) &&
      this.tableAttacks.length === this.tableDefenses.length;
    if (!defenderTookWound && this.roundEffects.balrogActive === this.attacker && balrogFullyDefended) {
      this.wounds[this.defender] += 1;
      this.setStatus(`${this.heroName("balrog")} wounds ${this.defender} despite the defense.`);
    }

    if (!defenderTookWound) {
      [this.attacker, this.defender] = [this.defender, this.attacker];
    } else if (pickupDefenses) {
      const defenderHand = this.getPlayerRealmHand(this.defender);
      for (const defenseCard of this.tableDefenses) {
        if (isRealm(defenseCard)) {
          defenderHand.push(defenseCard);
        }
      }
    }

    for (const attackCard of this.tableAttacks) {
      this.discardCard(attackCard);
    }
    for (const defenseCard of this.tableDefenses) {
      if (pickupDefenses && isRealm(defenseCard)) {
        continue;
      }
      this.discardCard(defenseCard);
    }
    this.drawBackToSix(this.attacker);
    this.drawBackToSix(this.defender);
    this.clearRoundState();
    this.checkGameOver();
    if (this.state !== "gameover") {
      this.setStatus(defenderTookWound ? `${this.playerLabel(this.attacker)} keeps the attack.` : `${this.playerLabel(this.attacker)} leads the next round.`);
      this.scheduleAiTurn();
    }
  }

  private scheduleAiTurn() {
    if (this.aiTimer !== null || !this.shouldAiAct()) {
      return;
    }
    this.aiTimer = window.setTimeout(() => {
      this.aiTimer = null;
      this.performAiTurn();
    }, 650);
  }

  private shouldAiAct() {
    if (this.aiPlayer === null || this.state === "gameover") {
      return false;
    }
    if (this.state === "drafting") {
      return this.currentDrafter === this.aiPlayer;
    }
    if (this.state === "playing") {
      return this.currentPlayer === this.aiPlayer && this.pendingAction === null;
    }
    return false;
  }

  private performAiTurn() {
    if (!this.shouldAiAct()) {
      return;
    }
    this.aiActing = true;
    try {
      if (this.state === "drafting") {
        this.performAiDraft();
      } else if (this.state === "playing") {
        this.performAiPlay();
      }
    } finally {
      this.aiActing = false;
    }
    this.scheduleAiTurn();
  }

  private performAiDraft() {
    const choices: Array<{ type: CardKind; index: number }> = [];
    if (this.canDraftCardType(this.currentDrafter, "realm")) {
      this.realmDraft.forEach((_, index) => choices.push({ type: "realm", index }));
    }
    if (this.canDraftCardType(this.currentDrafter, "hero")) {
      this.heroDraft.forEach((_, index) => choices.push({ type: "hero", index }));
    }
    const choice = this.chooseAiDraftPick(choices);
    if (choice) {
      this.attemptDraft(choice.index, choice.type);
    }
  }

  private performAiPlay() {
    const player = this.currentPlayer;
    if (this.playPhase === "DEFEND") {
      this.performAiAction(this.chooseAiDefenseAction(player));
      return;
    }

    if (this.playPhase === "REINFORCE") {
      this.performAiAction(this.chooseAiReinforceAction(player));
      return;
    }

    this.performAiAction(this.chooseAiAttackAction(player));
  }

  private performAiAction(action: AiAction) {
    if (action.type === "realm") {
      this.attemptPlayCard(action.card);
      return;
    }
    if (action.type === "hero") {
      this.attemptHeroPlay(action.card);
      this.resolveAiPendingAction(action.card);
      this.scheduleAiTurn();
      return;
    }
    if (action.type === "concede") {
      this.concedeDefense();
      return;
    }
    if (action.type === "end") {
      this.endRound(false, false);
      return;
    }
    this.checkGameOver();
  }

  private resolveAiPendingAction(heroCard: HeroCard) {
    if (this.pendingAction === null || this.pendingAction.owner !== this.aiPlayer) {
      return;
    }
    const owner = this.pendingAction.owner;
    if (this.pendingAction.type === "choose_suit") {
      this.resolveSuitChoice(this.chooseAiSuit(owner, heroCard));
    } else if (this.pendingAction.type === "aragorn_return") {
      const target = this.chooseAiAragornTarget(owner);
      if (target !== null) {
        this.resolveAragorn(target);
      }
    } else if (this.pendingAction.type === "saruman_exchange") {
      const card = this.chooseAiSarumanExchangeCard(owner);
      if (card !== null) {
        this.resolveSarumanExchange(card);
      }
    } else if (this.pendingAction.type === "hero_attack_card") {
      const legalCards = this.getPlayerRealmHand(owner).filter((card) => this.canSelectHeroAttackCard(card));
      const card = heroCard.id === "legolas" && this.aiKind !== "Random"
        ? this.lowestRankCard(legalCards)
        : this.chooseAiBestAttackCard(owner, legalCards);
      if (card !== null) {
        this.resolveHeroAttackCard(card);
      }
    }
  }

  private chooseAiDraftPick(choices: Array<{ type: CardKind; index: number }>) {
    if (this.aiKind === "Random") {
      return this.randomChoice(choices);
    }
    return choices.reduce<{ type: CardKind; index: number } | null>((best, choice) => {
      const card = choice.type === "realm" ? this.realmDraft[choice.index] : this.heroDraft[choice.index];
      if (!card) {
        return best;
      }
      if (best === null) {
        return choice;
      }
      const bestCard = best.type === "realm" ? this.realmDraft[best.index] : this.heroDraft[best.index];
      return bestCard && this.aiDraftScore(card) > this.aiDraftScore(bestCard) ? choice : best;
    }, null);
  }

  private aiDraftScore(card: Card) {
    const heroScores: Record<string, number> = {
      galadriel: 8.8,
      boromir: 8.5,
      gandalf: 8.2,
      balrog: 8.0,
      sauron: 7.8,
      saruman: 7.6,
      nazgul: 7.2,
      wormtongue: 7.0,
      frodo: 6.8,
      aragorn: 6.7,
      legolas: 6.5,
      gollum: 6.0
    };
    if (isRealm(card)) {
      const base = card.rank - 5;
      return this.aiKind === "Strategic" && card.rank >= 12 ? base + 1.5 : base;
    }
    const base = heroScores[card.id] ?? 5.0;
    return this.aiKind === "Strategic" ? base + 0.6 : base;
  }

  private chooseAiAttackAction(player: Player): AiAction {
    const legalRealm = this.legalAttackCards(player);
    const heroes = this.usableHeroes(player);
    if (this.aiKind === "Random") {
      if (heroes.length > 0 && Math.random() < 0.3) {
        return { type: "hero", card: this.randomChoice(heroes)! };
      }
      const card = this.randomChoice(legalRealm);
      return card ? { type: "realm", card } : { type: "pass" };
    }

    const hero = this.chooseAiAttackHero(player, heroes);
    if (this.aiKind === "Strategic") {
      if (hero !== null && ["sauron", "saruman", "wormtongue", "nazgul", "frodo", "balrog", "legolas"].includes(hero.id)) {
        return { type: "hero", card: hero };
      }
      const card = this.chooseAiBestAttackCard(player, legalRealm);
      if (card !== null) {
        return { type: "realm", card };
      }
      return hero !== null ? { type: "hero", card: hero } : { type: "pass" };
    }

    if (hero !== null) {
      return { type: "hero", card: hero };
    }
    const card = this.lowestRankCard(legalRealm);
    return card ? { type: "realm", card } : { type: "pass" };
  }

  private chooseAiDefenseAction(player: Player): AiAction {
    const legalRealm = this.legalDefenseCards(player);
    const heroes = this.usableHeroes(player);
    if (this.aiKind === "Random") {
      if (heroes.length > 0 && Math.random() < 0.35) {
        return { type: "hero", card: this.randomChoice(heroes)! };
      }
      const card = this.randomChoice(legalRealm);
      return card ? { type: "realm", card } : { type: "concede" };
    }
    const hero = this.chooseAiDefenseHero(player, legalRealm, heroes);
    if (hero !== null) {
      return { type: "hero", card: hero };
    }
    const card = this.lowestRankCard(legalRealm);
    return card ? { type: "realm", card } : { type: "concede" };
  }

  private chooseAiReinforceAction(player: Player): AiAction {
    const legalRealm = this.legalAttackCards(player);
    const heroes = this.usableHeroes(player);
    if (this.aiKind === "Random") {
      if (heroes.length > 0 && Math.random() < 0.25) {
        return { type: "hero", card: this.randomChoice(heroes)! };
      }
      if (legalRealm.length > 0 && Math.random() < 0.55) {
        return { type: "realm", card: this.randomChoice(legalRealm)! };
      }
      return { type: "end" };
    }

    const hero = this.chooseAiAttackHero(player, heroes);
    if (this.aiKind === "Strategic") {
      if (hero !== null) {
        return { type: "hero", card: hero };
      }
      if (legalRealm.length === 0) {
        return { type: "end" };
      }
      const opponent = getOpponent(player);
      if (this.getPlayerTotalCards(opponent) <= this.getPlayerTotalCards(player)) {
        const card = this.chooseAiBestAttackCard(player, legalRealm);
        return card ? { type: "realm", card } : { type: "end" };
      }
      return { type: "end" };
    }

    if (hero !== null && ["balrog", "legolas", "aragorn"].includes(hero.id)) {
      return { type: "hero", card: hero };
    }
    if (legalRealm.length === 0) {
      return { type: "end" };
    }
    const opponent = getOpponent(player);
    if (this.getPlayerRealmHand(opponent).length <= this.getPlayerRealmHand(player).length) {
      const card = this.lowestRankCard(legalRealm);
      if (card !== null && card.rank <= 11) {
        return { type: "realm", card };
      }
    }
    return { type: "end" };
  }

  private chooseAiAttackHero(player: Player, usableHeroes: HeroCard[]) {
    const heroMap = new Map(usableHeroes.map((hero) => [hero.id, hero]));
    const opponent = getOpponent(player);
    const opponentKnown = this.getKnownOpponentCards(player);
    const opponentTrumps = opponentKnown?.filter((card) => this.isTrumpCard(card)).length ?? 0;

    if (this.aiKind !== "Random") {
      if (heroMap.has("galadriel") && this.wounds[player] >= 3) return heroMap.get("galadriel")!;
      if (heroMap.has("sauron") && this.playPhase === "ATTACK" && this.tableAttacks.length === 0) return heroMap.get("sauron")!;
      if (heroMap.has("saruman") && this.playPhase === "ATTACK" && this.tableAttacks.length === 0) {
        const target = this.getSarumanTargetCard();
        if (target !== null && (this.isTrumpCard(target) || target.rank >= 12)) return heroMap.get("saruman")!;
      }
      if (heroMap.has("wormtongue") && (this.playPhase === "ATTACK" || this.getCurrentAttackCard() !== null)) return heroMap.get("wormtongue")!;
      if (heroMap.has("nazgul") && opponentTrumps <= 2) return heroMap.get("nazgul")!;
      if (heroMap.has("frodo") && opponentTrumps >= 2) return heroMap.get("frodo")!;
      if (heroMap.has("balrog") && this.wounds[opponent] >= 3) return heroMap.get("balrog")!;
      if (heroMap.has("legolas") && this.playPhase === "REINFORCE") return heroMap.get("legolas")!;
      if (heroMap.has("aragorn") && this.tableAttacks.some((_, index) => index < this.tableDefenses.length)) return heroMap.get("aragorn")!;
      if (heroMap.has("gollum") && ["ATTACK", "REINFORCE"].includes(this.playPhase)) return heroMap.get("gollum")!;
      return null;
    }

    if (heroMap.has("galadriel") && this.wounds[player] >= 4) {
      return heroMap.get("galadriel")!;
    }
    return null;
  }

  private chooseAiDefenseHero(player: Player, legalRealm: RealmCard[], usableHeroes: HeroCard[]) {
    const heroMap = new Map(usableHeroes.map((hero) => [hero.id, hero]));
    const attack = this.getCurrentAttackCard();
    if (attack === null) {
      return null;
    }
    if (this.aiKind !== "Random") {
      if (heroMap.has("galadriel") && this.wounds[player] >= 3) return heroMap.get("galadriel")!;
      if (heroMap.has("gandalf") && (legalRealm.length === 0 || attack.rank >= 12)) return heroMap.get("gandalf")!;
      if (heroMap.has("boromir") && (legalRealm.length === 0 || this.isTrumpCard(attack))) return heroMap.get("boromir")!;
      return null;
    }
    if (heroMap.has("galadriel") && this.wounds[player] >= 4) {
      return heroMap.get("galadriel")!;
    }
    return null;
  }

  private chooseAiBestAttackCard(player: Player, legalRealm: RealmCard[]) {
    if (legalRealm.length === 0) {
      return null;
    }
    if (this.aiKind !== "Strategic") {
      return this.lowestRankCard(legalRealm);
    }
    const opponentCards = this.getKnownOpponentCards(player);
    return legalRealm.reduce((best, card) => {
      const score = this.aiAttackScore(card, opponentCards);
      return score > best.score ? { card, score } : best;
    }, { card: legalRealm[0]!, score: this.aiAttackScore(legalRealm[0]!, opponentCards) }).card;
  }

  private aiAttackScore(card: RealmCard, opponentCards: RealmCard[] | null) {
    let difficulty = 0;
    if (opponentCards !== null) {
      const defendable = opponentCards.some((opponentCard) => this.canDefendWithCard(opponentCard, card));
      difficulty = defendable ? 0 : 2;
    }
    const trumpPenalty = this.isTrumpCard(card) ? 3 : 0;
    return difficulty - trumpPenalty - card.rank / 20;
  }

  private chooseAiSuit(player: Player, heroCard: HeroCard) {
    const knownOpponent = this.getKnownOpponentCards(player);
    if (this.aiKind === "Random") {
      return this.randomChoice(this.allSuits) ?? this.allSuits[0] ?? "";
    }
    if (heroCard.id === "wormtongue") {
      const attack = this.getCurrentAttackCard();
      if (this.aiKind === "Strategic" && attack !== null) {
        return attack.suit;
      }
      if (knownOpponent !== null && knownOpponent.length > 0) {
        return this.mostCommonSuit(knownOpponent) ?? this.allSuits[0] ?? "";
      }
      if (attack !== null) {
        return attack.suit;
      }
    }
    const ownCards = this.getPlayerRealmHand(player);
    if (this.aiKind === "Strategic" && heroCard.id === "gollum" && knownOpponent !== null) {
      let bestSuit = this.allSuits[0] ?? "";
      let bestScore = Number.NEGATIVE_INFINITY;
      for (const suit of this.allSuits) {
        const score = ownCards.filter((card) => card.suit === suit).length - knownOpponent.filter((card) => card.suit === suit).length;
        if (score > bestScore) {
          bestScore = score;
          bestSuit = suit;
        }
      }
      return bestSuit;
    }
    return this.mostCommonSuit(ownCards) ?? this.allSuits[0] ?? "";
  }

  private chooseAiAragornTarget(player: Player) {
    if (this.tableAttacks.length === 0) {
      return null;
    }
    if (this.aiKind === "Random") {
      const card = this.randomChoice(this.tableAttacks);
      return card === null ? null : this.tableAttacks.indexOf(card);
    }
    return this.tableAttacks.reduce((best, card, index) => {
      const score = (this.isTrumpCard(card) ? 100 : 0) + (index < this.tableDefenses.length ? 10 : 0) + card.rank;
      return score > best.score ? { index, score } : best;
    }, { index: 0, score: Number.NEGATIVE_INFINITY }).index;
  }

  private chooseAiSarumanExchangeCard(player: Player) {
    const cards = this.getPlayerRealmHand(player);
    return this.aiKind === "Random" ? this.randomChoice(cards) : this.lowestRankCard(cards);
  }

  private lowestRankCard(cards: RealmCard[]) {
    if (cards.length === 0) {
      return null;
    }
    return cards.reduce((best, card) => {
      const bestScore = (this.isTrumpCard(best) ? 100 : 0) + best.rank;
      const cardScore = (this.isTrumpCard(card) ? 100 : 0) + card.rank;
      return cardScore < bestScore ? card : best;
    }, cards[0]!);
  }

  private mostCommonSuit(cards: RealmCard[]) {
    const counts = new Map<string, number>();
    for (const card of cards) {
      counts.set(card.suit, (counts.get(card.suit) ?? 0) + 1);
    }
    let bestSuit: string | null = null;
    let bestCount = 0;
    for (const [suit, count] of counts) {
      if (count > bestCount) {
        bestSuit = suit;
        bestCount = count;
      }
    }
    return bestSuit;
  }

  private randomChoice<T>(items: T[]) {
    if (items.length === 0) {
      return null;
    }
    return items[Math.floor(Math.random() * items.length)] ?? null;
  }

  private drawBackToSix(player: Player) {
    const hand = this.getPlayerRealmHand(player);
    while (hand.length < MAX_REALM_CARDS && this.realmDeck.length > 0) {
      const card = this.realmDeck.pop();
      if (card) {
        hand.push(card);
      }
    }
  }

  private checkGameOver() {
    if (this.wounds.P1 >= WOUND_LIMIT) {
      this.winner = "P2";
      this.winReason = "P1 reached 6 wounds.";
      this.state = "gameover";
      return;
    }
    if (this.wounds.P2 >= WOUND_LIMIT) {
      this.winner = "P1";
      this.winReason = "P2 reached 6 wounds.";
      this.state = "gameover";
      return;
    }
    if (this.realmDeck.length > 0) {
      return;
    }
    const p1RealmEmpty = this.p1Hand.length === 0;
    const p2RealmEmpty = this.p2Hand.length === 0;
    if (p1RealmEmpty && !p2RealmEmpty) {
      this.winner = "P1";
      this.winReason = "P1 emptied all realm cards after the deck ran out.";
      this.state = "gameover";
    } else if (p2RealmEmpty && !p1RealmEmpty) {
      this.winner = "P2";
      this.winReason = "P2 emptied all realm cards after the deck ran out.";
      this.state = "gameover";
    } else if (p1RealmEmpty && p2RealmEmpty) {
      if (this.wounds.P1 < this.wounds.P2) {
        this.winner = "P1";
        this.winReason = "Both players ran out of realm cards; P1 had fewer wounds.";
      } else if (this.wounds.P2 < this.wounds.P1) {
        this.winner = "P2";
        this.winReason = "Both players ran out of realm cards; P2 had fewer wounds.";
      } else {
        const p1Total = this.getPlayerTotalCards("P1");
        const p2Total = this.getPlayerTotalCards("P2");
        if (p1Total < p2Total) {
          this.winner = "P1";
          this.winReason = "Realm cards were exhausted and tied on wounds; P1 had fewer total cards left.";
        } else if (p2Total < p1Total) {
          this.winner = "P2";
          this.winReason = "Realm cards were exhausted and tied on wounds; P2 had fewer total cards left.";
        } else {
          this.winner = Math.random() < 0.5 ? "P1" : "P2";
          this.winReason = "All endgame tiebreakers were equal, so the winner was chosen at random.";
        }
      }
      this.state = "gameover";
    }
  }

  private isCardPlayable(card: Card) {
    if (this.pendingAction?.type === "saruman_exchange") {
      return isRealm(card);
    }
    if (this.pendingAction?.type === "hero_attack_card") {
      return isRealm(card) && this.canSelectHeroAttackCard(card);
    }
    if (isHero(card)) {
      return this.canUseHero(card);
    }
    if (this.playPhase === "DEFEND") {
      return this.canDefendWithCard(card, this.getCurrentAttackCard());
    }
    return this.canAttackWithCard(card);
  }

  private handleClick(event: MouseEvent) {
    const rect = this.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const hit = [...this.hitboxes].reverse().find((box) => box.enabled !== false && x >= box.x && x <= box.x + box.w && y >= box.y && y <= box.y + box.h);
    if (!hit) {
      return;
    }
    if (!this.isHumanTurn() && !(hit.kind === "button" && ["music_toggle", "how_to_play", "close_how_to_play"].includes(hit.label ?? ""))) {
      return;
    }
    if (hit.kind === "button") {
      this.handleButton(hit.label ?? "");
    } else if (hit.kind === "draft-realm" && typeof hit.index === "number") {
      this.attemptDraft(hit.index, "realm");
    } else if (hit.kind === "draft-hero" && typeof hit.index === "number") {
      this.attemptDraft(hit.index, "hero");
    } else if (hit.kind === "hand" && typeof hit.index === "number") {
      const hand = [...this.getPlayerRealmHand(this.currentPlayer), ...this.getPlayerHeroHand(this.currentPlayer)];
      const card = hand[hit.index];
      if (card) {
        this.handleHandCardClick(card);
      }
    } else if (hit.kind === "attack" && typeof hit.index === "number") {
      this.resolveAragorn(hit.index);
    } else if (hit.kind === "suit" && hit.suit) {
      this.resolveSuitChoice(hit.suit);
    }
  }

  private handleMouseMove(event: MouseEvent) {
    const rect = this.canvas.getBoundingClientRect();
    this.mouseX = event.clientX - rect.left;
    this.mouseY = event.clientY - rect.top;
    this.hoveredHitbox = [...this.hitboxes].reverse().find(
      (box) => box.enabled !== false && this.mouseX >= box.x && this.mouseX <= box.x + box.w && this.mouseY >= box.y && this.mouseY <= box.y + box.h
    ) ?? null;
    this.canvas.style.cursor = this.hoveredHitbox ? "none" : "default";
  }

  private handleButton(label: string) {
    if (label === "start") {
      void this.enableMusic();
      this.setupGame();
    } else if (label === "start_random_ai") {
      void this.enableMusic();
      this.setupGame("random-ai");
    } else if (label === "start_greedy_ai") {
      void this.enableMusic();
      this.setupGame("greedy-ai");
    } else if (label === "start_strategic_ai") {
      void this.enableMusic();
      this.setupGame("strategic-ai");
    } else if (label === "how_to_play") {
      this.showHowToPlay = true;
    } else if (label === "close_how_to_play") {
      this.showHowToPlay = false;
    } else if (label === "restart") {
      this.state = "splash";
      this.setStatus("Click Start to begin a local two-player game.");
    } else if (label === "concede") {
      this.concedeDefense();
    } else if (label === "end") {
      if ((this.playPhase === "REINFORCE" || (this.playPhase === "ATTACK" && this.roundEffects.gandalfRanks.length > 0)) && this.pendingAction === null) {
        this.endRound(false, false);
        this.scheduleAiTurn();
      }
    } else if (label === "log_up") {
      this.logScroll = Math.min(this.logScroll + 1, Math.max(0, this.gameLog.length - 5));
    } else if (label === "log_down") {
      this.logScroll = Math.max(0, this.logScroll - 1);
    } else if (label === "music_toggle") {
      this.toggleMusic();
    }
  }

  private toggleMusic() {
    if (this.musicEnabled) {
      this.disableMusic();
    } else {
      void this.enableMusic();
    }
  }

  private async enableMusic() {
    if (!this.music || MUSIC_URLS.length === 0) {
      this.setStatus("No music tracks found.");
      return;
    }
    this.musicEnabled = true;
    if (this.musicPlaylist.length === 0) {
      this.musicPlaylist = shuffle(MUSIC_URLS);
    }
    if (!this.music.src) {
      this.musicIndex = 0;
      this.music.src = this.musicPlaylist[this.musicIndex]!;
    }
    try {
      await this.music.play();
      this.setStatus("Music enabled.");
    } catch {
      this.musicEnabled = false;
      this.setStatus("Click Music On to enable music.");
    }
  }

  private disableMusic() {
    this.musicEnabled = false;
    this.music?.pause();
    this.setStatus("Music disabled.");
  }

  private advanceMusic() {
    if (!this.musicEnabled || !this.music || MUSIC_URLS.length === 0) {
      return;
    }
    this.musicIndex += 1;
    if (this.musicIndex >= this.musicPlaylist.length) {
      const previousTrack = this.musicPlaylist[this.musicPlaylist.length - 1];
      this.musicPlaylist = shuffle(MUSIC_URLS);
      if (this.musicPlaylist.length > 1 && this.musicPlaylist[0] === previousTrack) {
        const swapIndex = 1 + Math.floor(Math.random() * (this.musicPlaylist.length - 1));
        [this.musicPlaylist[0], this.musicPlaylist[swapIndex]] = [this.musicPlaylist[swapIndex]!, this.musicPlaylist[0]!];
      }
      this.musicIndex = 0;
    }
    this.music.src = this.musicPlaylist[this.musicIndex]!;
    void this.music.play().catch(() => {
      this.musicEnabled = false;
    });
  }

  private addHitbox(hitbox: CardHitbox) {
    this.hitboxes.push(hitbox);
  }

  private draw() {
    this.hitboxes = [];
    this.drawBackground();

    if (this.state === "playing") {
      this.drawHeader();
    }
    if (this.state === "loading") {
      this.drawCenteredPanel("Loading Thronebound", this.statusMessage);
    } else if (this.state === "splash") {
      this.drawSplash();
    } else if (this.state === "drafting") {
      this.drawDrafting();
    } else if (this.state === "playing") {
      this.drawPlaying();
    } else {
      this.drawGameOver();
    }
    if (this.showHowToPlay) {
      this.drawHowToPlay();
    }
    this.drawHoveredCardPreview();
    this.drawCustomCursor();
  }

  private drawBackground() {
    const ctx = this.ctx;
    if (this.backgroundImage?.complete && this.backgroundImage.naturalWidth > 0) {
      const image = this.backgroundImage;
      const scale = Math.max(this.width / image.naturalWidth, this.height / image.naturalHeight);
      const w = image.naturalWidth * scale;
      const h = image.naturalHeight * scale;
      ctx.drawImage(image, (this.width - w) / 2, (this.height - h) / 2, w, h);
      ctx.fillStyle = "rgba(13, 11, 14, 0.42)";
      ctx.fillRect(0, 0, this.width, this.height);
      return;
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, this.height);
    gradient.addColorStop(0, THEME.bg);
    gradient.addColorStop(1, "#17131b");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, this.width, this.height);
  }

  private panel(x: number, y: number, w: number, h: number, fill = "rgba(18, 14, 22, 0.76)", border = "rgba(201, 168, 76, 0.42)") {
    const ctx = this.ctx;
    ctx.save();
    ctx.shadowColor = "rgba(0, 0, 0, 0.42)";
    ctx.shadowBlur = 12;
    ctx.shadowOffsetY = 4;
    ctx.fillStyle = fill;
    ctx.strokeStyle = border;
    ctx.lineWidth = 2;
    this.roundRect(x, y, w, h, 16);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  private textBubble(text: string, centerX: number, centerY: number, font: string, fill: string, border: string, padX = 22, padY = 12) {
    const ctx = this.ctx;
    ctx.save();
    ctx.font = font;
    const metrics = ctx.measureText(text);
    const h = Number(font.match(/(\d+)px/)?.[1] ?? 18) + padY * 2;
    const w = Math.min(this.width - 64, metrics.width + padX * 2);
    const x = centerX - w / 2;
    const y = centerY - h / 2;
    this.panel(x, y, w, h, fill, border);
    ctx.fillStyle = border.includes("201, 168, 76") ? THEME.gold : THEME.text;
    ctx.textAlign = "center";
    drawCenteredFittedText(ctx, text, centerX, centerY + h * 0.18, w - padX * 2);
    ctx.textAlign = "left";
    ctx.restore();
  }

  private panelBorder(kind: "gold" | "subtle" | "zone" = "subtle") {
    if (kind === "gold") {
      return "rgba(201, 168, 76, 0.58)";
    }
    if (kind === "zone") {
      return "rgba(83, 72, 56, 0.52)";
    }
    return "rgba(83, 72, 56, 0.66)";
  }

  private roundRect(x: number, y: number, w: number, h: number, r: number) {
    const ctx = this.ctx;
    const radius = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.arcTo(x + w, y, x + w, y + h, radius);
    ctx.arcTo(x + w, y + h, x, y + h, radius);
    ctx.arcTo(x, y + h, x, y, radius);
    ctx.arcTo(x, y, x + w, y, radius);
    ctx.closePath();
  }

  private drawHeader() {
    const ctx = this.ctx;
    const topH = Math.max(58, this.height * 0.08);
    this.panel(0, 0, this.width, topH, "rgba(18, 14, 22, 0.68)", "rgba(83, 72, 56, 0.7)");
    this.drawPlayerHeaderPips("P1", this.width * 0.02, topH * 0.14, this.width * 0.28, topH * 0.72, "left");
    this.drawPlayerHeaderPips("P2", this.width * 0.70, topH * 0.14, this.width * 0.28, topH * 0.72, "right");
    ctx.fillStyle = THEME.text;
    ctx.font = `700 ${Math.round(topH * 0.35)}px "Ringbound Display", Georgia, serif`;
    ctx.textAlign = "center";
    ctx.fillText(`${this.playerLabel(this.currentPlayer)} - ${this.playPhase}`, this.width / 2, topH * 0.62);
    ctx.textAlign = "left";
  }

  private drawPlayerHeaderPips(player: Player, x: number, y: number, w: number, h: number, align: "left" | "right") {
    const ctx = this.ctx;
    const now = performance.now();
    const wounds = this.wounds[player];
    if (wounds > this.lastWounds[player]) {
      this.woundFlashUntil[player] = now + 280;
    }
    this.lastWounds[player] = wounds;
    const labelW = Math.min(Math.max(112, w * 0.34), w * 0.46);
    const r = Math.max(4, h * 0.12);
    const pipGap = r * 2.8;
    const pipsW = r * 2 + (WOUND_LIMIT - 1) * pipGap;
    const gutter = Math.max(10, w * 0.03);
    const labelX = align === "left" ? x : x + w - labelW;
    const pipsStartX = align === "left" ? x + labelW + gutter + r : x + w - labelW - gutter - pipsW + r;

    ctx.fillStyle = THEME.text;
    ctx.font = `14px "Ringbound Body", Georgia, serif`;
    if (align === "right") {
      ctx.textAlign = "right";
      drawFittedText(ctx, this.playerLabel(player), labelX + labelW, y + h * 0.32, labelW);
    } else {
      drawFittedText(ctx, this.playerLabel(player), labelX, y + h * 0.32, labelW);
    }
    ctx.fillStyle = THEME.muted;
    if (align === "right") {
      drawFittedText(ctx, `${this.getPlayerRealmHand(player).length}R ${this.getPlayerHeroHand(player).length}H`, labelX + labelW, y + h * 0.76, labelW);
      ctx.textAlign = "left";
    } else {
      drawFittedText(ctx, `${this.getPlayerRealmHand(player).length}R ${this.getPlayerHeroHand(player).length}H`, labelX, y + h * 0.76, labelW);
    }

    const startX = pipsStartX;
    const cy = y + h * 0.32;
    for (let index = 0; index < WOUND_LIMIT; index += 1) {
      const cx = startX + index * r * 2.8;
      ctx.fillStyle = index < wounds ? THEME.ember : "rgba(40, 32, 30, 0.95)";
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = THEME.border;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
    if (wounds > 0 && now < this.woundFlashUntil[player]) {
      const progress = (this.woundFlashUntil[player] - now) / 280;
      const pulseIndex = wounds - 1;
      const cx = startX + pulseIndex * r * 2.8;
      const pulseRadius = r + r * 0.7 * (1 - progress);
      ctx.strokeStyle = `rgba(184, 74, 46, ${Math.max(0.25, progress * 0.75)})`;
      ctx.lineWidth = Math.max(1, r * 0.45);
      ctx.beginPath();
      ctx.arc(cx, cy, pulseRadius, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  private drawSplash() {
    const center = { x: this.width / 2, y: this.height / 2 };
    const centerX = this.width / 2;
    const w = Math.min(320, this.width * 0.28);
    const h = Math.max(40, this.height * 0.065);
    const gap = Math.max(12, this.height * 0.018);
    const musicH = h * 0.82;
    const modes = [
      { label: "Two Players", action: "start", color: THEME.gold },
      { label: "Vs Random AI", action: "start_random_ai", color: SUIT_COLORS["Tidewake Dominion"] ?? THEME.gold },
      { label: "Vs Greedy AI", action: "start_greedy_ai", color: SUIT_COLORS["Verdant Court"] ?? THEME.gold },
      { label: "Vs Strategic AI", action: "start_strategic_ai", color: SUIT_COLORS["Ember Throne"] ?? THEME.gold }
    ];
    const helpH = h * 0.82;
    const buttonStackH = modes.length * h + (modes.length - 1) * gap + gap * 2.2 + musicH + helpH;
    const startY = Math.min(this.height * 0.48, this.height - buttonStackH - Math.max(24, this.height * 0.04));
    const promptY = startY - gap * 3.1;
    const subtitleY = promptY - gap * 5.0;
    const titleY = subtitleY - gap * 6.0;

    this.textBubble(
      "THRONEBOUND",
      center.x,
      titleY,
      `700 ${Math.round(this.height * 0.07)}px "Ringbound Display", Georgia, serif`,
      "rgba(24, 18, 30, 0.8)",
      "rgba(201, 168, 76, 0.72)",
      28,
      18
    );
    this.textBubble(
      "Battle for the Throne",
      center.x,
      subtitleY,
      `700 ${Math.round(this.height * 0.04)}px "Ringbound Display", Georgia, serif`,
      "rgba(20, 16, 24, 0.76)",
      "rgba(83, 72, 56, 0.72)",
      24,
      12
    );
    this.textBubble(
      "Click to start draft",
      center.x,
      promptY,
      `${Math.round(this.height * 0.024)}px "Ringbound Body", Georgia, serif`,
      "rgba(18, 14, 22, 0.75)",
      "rgba(83, 72, 56, 0.74)",
      24,
      14
    );
    modes.forEach((mode, index) => {
      this.drawButton(mode.label, mode.action, centerX - w / 2, startY + index * (h + gap), w, h, mode.color);
    });
    const musicY = startY + modes.length * h + (modes.length - 1) * gap + gap * 1.2;
    this.drawMusicButton(centerX - w / 2, musicY, w, musicH);
    this.drawButton("How to Play", "how_to_play", centerX - w / 2, musicY + musicH + gap * 0.8, w, helpH, THEME.border);
  }

  private drawHowToPlay() {
    const ctx = this.ctx;
    this.addHitbox({ kind: "button", label: "close_how_to_play", x: 0, y: 0, w: this.width, h: this.height, enabled: true });

    ctx.save();
    ctx.fillStyle = "rgba(0, 0, 0, 0.48)";
    ctx.fillRect(0, 0, this.width, this.height);
    ctx.restore();

    const panelW = Math.min(760, this.width * 0.78);
    const panelH = Math.min(520, this.height * 0.76);
    const x = (this.width - panelW) / 2;
    const y = (this.height - panelH) / 2;
    this.panel(x, y, panelW, panelH, "rgba(18, 14, 22, 0.94)", "rgba(201, 168, 76, 0.72)");

    ctx.fillStyle = THEME.gold;
    ctx.font = `700 ${Math.max(26, Math.min(38, panelW * 0.05))}px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, "How to Play", x + 34, y + 52, panelW - 68);

    const lines = [
      "Draft: each player builds a hand of 6 realm cards and 4 hero cards. The opening realm card counts toward the limit.",
      "Attack: the attacker leads with a realm card. Reinforcements must match a rank already on the table unless a hero changes the rule.",
      "Defend: answer with a higher card of the same dominion, or with a crown card. Crown cards beat non-crown attacks.",
      "Take Wound: if you cannot or do not want to defend, take a wound. At 6 wounds, you lose.",
      "Initiative: a successful defense makes the defender the next attacker. Taking a wound lets the attacker keep initiative.",
      "Heroes: hero cards create one-time effects such as healing, cancelling attacks, forcing crown defense, or changing the crown suit.",
      "Endgame: when the realm deck is empty, the game checks empty realm hands, then fewer wounds, then fewer total cards."
    ];

    const textX = x + 38;
    let textY = y + 92;
    const lineH = Math.max(18, Math.min(23, panelH * 0.043));
    ctx.font = `${Math.max(14, Math.min(17, panelW * 0.022))}px "Ringbound Body", Georgia, serif`;
    lines.forEach((line) => {
      ctx.fillStyle = "rgba(201, 168, 76, 0.82)";
      ctx.beginPath();
      ctx.arc(textX + 4, textY - lineH * 0.25, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = THEME.text;
      drawWrappedText(ctx, line, textX + 18, textY, panelW - 94, lineH, 2);
      textY += lineH * 2.25;
    });

    const buttonW = Math.min(180, panelW * 0.32);
    const buttonH = 42;
    this.drawButton("Got It", "close_how_to_play", x + panelW / 2 - buttonW / 2, y + panelH - 64, buttonW, buttonH, THEME.gold);
  }

  private drawGameOver() {
    const centerX = this.width / 2;
    const centerY = this.height / 2;
    this.textBubble(
      "GAME OVER",
      centerX,
      centerY * 0.72,
      `700 ${Math.round(this.height * 0.07)}px "Ringbound Display", Georgia, serif`,
      "rgba(30, 18, 18, 0.8)",
      "rgba(184, 74, 46, 0.72)",
      28,
      18
    );
    this.textBubble(
      `${this.winner ?? "Player"} claims the Throne`,
      centerX,
      centerY * 1.02,
      `700 ${Math.round(this.height * 0.04)}px "Ringbound Display", Georgia, serif`,
      "rgba(22, 18, 28, 0.8)",
      "rgba(201, 168, 76, 0.72)",
      24,
      14
    );
    const reason = this.winReason || this.statusMessage || "Click to return to splash";
    this.textBubble(
      reason,
      centerX,
      centerY * 1.28,
      `${Math.round(this.height * 0.018)}px "Ringbound Body", Georgia, serif`,
      "rgba(18, 14, 22, 0.75)",
      "rgba(83, 72, 56, 0.7)",
      20,
      12
    );
    this.addHitbox({ kind: "button", label: "restart", x: 0, y: 0, w: this.width, h: this.height, enabled: true });
    this.drawMusicButton(centerX - 92, centerY * 1.42, 184, 36);
    this.drawButton("How to Play", "how_to_play", centerX - 92, centerY * 1.42 + 46, 184, 36, THEME.border);
  }

  private drawCenteredPanel(title: string, detail: string) {
    const ctx = this.ctx;
    const w = Math.min(560, this.width - 80);
    const h = 220;
    const x = (this.width - w) / 2;
    const y = (this.height - h) / 2;
    this.panel(x, y, w, h, "rgba(24, 18, 30, 0.86)", "rgba(201, 168, 76, 0.72)");
    ctx.fillStyle = THEME.gold;
    ctx.font = `700 42px "Ringbound Display", Georgia, serif`;
    ctx.textAlign = "center";
    ctx.fillText(ellipsizeText(ctx, title, w - 70), this.width / 2, y + 78);
    ctx.fillStyle = THEME.text;
    ctx.font = `18px "Ringbound Body", Georgia, serif`;
    ctx.textAlign = "left";
    drawWrappedText(ctx, detail, this.width / 2 - w / 2 + 44, y + 122, w - 88, 24, 3);
  }

  private drawDrafting() {
    const ctx = this.ctx;
    const topH = Math.max(58, this.height * 0.08);
    const sideW = this.width * 0.12;
    const centerX = sideW;
    const centerW = this.width - sideW * 2;
    this.textBubble(
      `Drafting: ${this.playerLabel(this.currentDrafter)}`,
      this.width / 2,
      this.height * 0.075,
      `700 ${Math.round(this.height * 0.03)}px "Ringbound Display", Georgia, serif`,
      "rgba(24, 18, 30, 0.77)",
      "rgba(201, 168, 76, 0.68)",
      24,
      14
    );
    this.textBubble(
      `${this.playerLabel("P1")} Draft: ${this.p1Hand.length} realm, ${this.p1Heroes.length} hero`,
      this.width * 0.16,
      this.height * 0.035,
      `${Math.round(this.height * 0.018)}px "Ringbound Body", Georgia, serif`,
      "rgba(18, 14, 22, 0.74)",
      "rgba(83, 72, 56, 0.68)",
      18,
      10
    );
    this.textBubble(
      `${this.playerLabel("P2")} Draft: ${this.p2Hand.length} realm, ${this.p2Heroes.length} hero`,
      this.width * 0.84,
      this.height * 0.035,
      `${Math.round(this.height * 0.018)}px "Ringbound Body", Georgia, serif`,
      "rgba(18, 14, 22, 0.74)",
      "rgba(83, 72, 56, 0.68)",
      18,
      10
    );
    this.textBubble(
      "Draft limit: 6 realm cards and 4 hero cards per player",
      this.width / 2,
      this.height * 0.15,
      `${Math.round(this.height * 0.016)}px "Ringbound Body", Georgia, serif`,
      "rgba(20, 16, 24, 0.74)",
      "rgba(201, 168, 76, 0.52)",
      20,
      10
    );
    this.panel(0, topH, sideW, this.height - topH, "rgba(22, 18, 28, 0.66)", this.panelBorder("subtle"));
    this.panel(centerX + 18, topH + 86, centerW - 36, this.height * 0.29, "rgba(18, 14, 22, 0.62)", this.panelBorder("gold"));
    this.panel(centerX + 18, topH + 126 + this.height * 0.29, centerW - 36, this.height * 0.29, "rgba(18, 14, 22, 0.62)", this.panelBorder("gold"));

    ctx.fillStyle = THEME.gold;
    ctx.font = `700 18px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, "Crown Card", 30, topH + 52, sideW - 48);
    if (this.trumpCard) {
      this.drawCard(this.trumpCard, 28, topH + 74, Math.min(96, sideW - 44), Math.min(144, (sideW - 44) * 1.5), true);
    }
    ctx.fillStyle = THEME.text;
    ctx.font = `13px "Ringbound Body", Georgia, serif`;
    drawFittedText(ctx, `Active: ${this.getEffectiveTrumpSuit() ?? "None"}`, 30, topH + 238, sideW - 48);
    this.drawMusicButton(28, topH + 270, Math.min(116, sideW - 44), 32);
    this.drawButton("How to Play", "how_to_play", 28, topH + 310, Math.min(116, sideW - 44), 32, THEME.border);
    ctx.fillStyle = THEME.muted;

    ctx.fillStyle = THEME.text;
    ctx.font = `17px "Ringbound Body", Georgia, serif`;
    drawFittedText(ctx, `Realm ${this.getPlayerRealmHand(this.currentDrafter).length}/${MAX_REALM_CARDS}`, centerX + 36, topH + 58, 130);
    drawFittedText(ctx, `Heroes ${this.getPlayerHeroHand(this.currentDrafter).length}/${MAX_HERO_CARDS}`, centerX + 180, topH + 58, 130);
    ctx.fillStyle = THEME.gold;
    ctx.font = `700 20px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, "Realm Draft", centerX + 42, topH + 118, centerW - 84);
    drawFittedText(ctx, "Hero Draft", centerX + 42, topH + 158 + this.height * 0.29, centerW - 84);

    const draftCardW = Math.max(64, Math.min(92, centerW / 12));
    this.drawCardRow(this.realmDraft, centerX + 42, topH + 138, "draft-realm", this.canDraftCardType(this.currentDrafter, "realm"), draftCardW, draftCardW * 1.5, undefined, centerW - 84);
    this.drawCardRow(this.heroDraft, centerX + 42, topH + 178 + this.height * 0.29, "draft-hero", this.canDraftCardType(this.currentDrafter, "hero"), draftCardW, draftCardW * 1.5, undefined, centerW - 84);
  }

  private drawDraftSummary(player: Player, x: number, y: number, w: number, h: number) {
    const ctx = this.ctx;
    this.panel(x, y, w, h, "rgba(18, 14, 22, 0.62)", "rgba(83, 72, 56, 0.58)");
    ctx.fillStyle = player === this.currentDrafter ? THEME.gold : THEME.text;
    ctx.font = `700 15px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, player, x + 14, y + 25, w - 28);
    ctx.fillStyle = THEME.text;
    ctx.font = `13px "Ringbound Body", Georgia, serif`;
    drawFittedText(ctx, `${this.getPlayerRealmHand(player).length}/${MAX_REALM_CARDS} realm`, x + 14, y + 50, w - 28);
    drawFittedText(ctx, `${this.getPlayerHeroHand(player).length}/${MAX_HERO_CARDS} hero`, x + 14, y + 68, w - 28);
  }

  private drawPlaying() {
    this.drawOpponentHand();
    this.drawTable();
    this.drawActions();
    this.drawHand();
    this.drawEffectsPanel();
  }

  private drawStatusBand(title: string, detail: string) {
    const ctx = this.ctx;
    const topH = Math.max(58, this.height * 0.08);
    this.panel(18, topH + 10, this.width - 36, 48, "rgba(24, 18, 30, 0.72)", "rgba(201, 168, 76, 0.34)");
    ctx.fillStyle = THEME.gold;
    ctx.font = `700 19px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, title, 34, topH + 41, 138);
    ctx.fillStyle = THEME.text;
    ctx.font = `16px "Ringbound Body", Georgia, serif`;
    drawFittedText(ctx, detail, 190, topH + 41, Math.max(180, this.width - 690));
    ctx.fillStyle = THEME.muted;
    drawFittedText(ctx, `Attacker: ${this.attacker}  Defender: ${this.defender}  Phase: ${this.playPhase}`, this.width - 455, topH + 41, 420);
  }

  private drawFloatingStatus(x: number, y: number, w: number) {
    const ctx = this.ctx;
    const h = 46;
    this.panel(x, y, w, h, "rgba(18, 14, 22, 0.8)", "rgba(201, 168, 76, 0.45)");
    ctx.fillStyle = THEME.text;
    ctx.font = `15px "Ringbound Body", Georgia, serif`;
    drawWrappedText(ctx, this.statusMessage, x + 18, y + 28, w - 36, 18, 2);
  }

  private drawPlayerSummary() {
    const ctx = this.ctx;
    const layout = this.rightPanelLayout();
    const { x, w, summaryY: y, summaryH: h } = layout;
    this.panel(x, y, w, h, "rgba(18, 14, 22, 0.74)", "rgba(83, 72, 56, 0.72)");
    ctx.fillStyle = THEME.gold;
    ctx.font = `700 16px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, "Hands", x + 14, y + 26, w - 28);
    ctx.fillStyle = THEME.text;
    ctx.font = `13px "Ringbound Body", Georgia, serif`;
    drawFittedText(ctx, `P1 ${this.p1Hand.length}R ${this.p1Heroes.length}H`, x + 14, y + 50, w - 28);
    drawFittedText(ctx, `P2 ${this.p2Hand.length}R ${this.p2Heroes.length}H`, x + 14, y + 72, w - 28);
    drawFittedText(ctx, `Deck ${this.realmDeck.length}`, x + 14, y + 94, w - 28);
    ctx.fillStyle = THEME.muted;
    if (h > 124) {
      drawFittedText(ctx, `Discard ${this.discardPile.length}/${this.heroDiscard.length}H`, x + 14, y + 116, w - 28);
    }
  }

  private rightPanelLayout() {
    const topH = Math.max(58, this.height * 0.08);
    const handH = this.height * 0.2;
    const sideW = this.width * 0.12;
    const x = this.width - sideW + 12;
    const w = sideW - 24;
    const startY = topH + 76;
    const bottom = this.height - handH - 18;
    const gap = 10;
    const available = Math.max(300, bottom - startY);
    const summaryH = Math.max(104, Math.min(142, available * 0.3));
    const effectsH = Math.max(106, Math.min(140, available * 0.32));
    const logH = Math.max(84, available - summaryH - effectsH - gap * 2);
    const effectsY = startY + summaryH + gap;
    const logY = effectsY + effectsH + gap;
    return { x, w, summaryY: startY, summaryH, effectsY, effectsH, logY, logH };
  }

  private activeEffectLines() {
    const effects = this.roundEffects;
    const lines: string[] = [];
    const trump = this.getEffectiveTrumpSuit();
    if (effects.trumpDisabled) {
      lines.push("Crown disabled");
    } else if (effects.temporaryTrumpSuit !== null) {
      lines.push(`Crown is ${trump}`);
    }
    if (effects.nazgulActive) {
      lines.push("Defender must use crown");
    }
    if (effects.wormtongueSuit !== null) {
      lines.push(`Cannot play ${effects.wormtongueSuit}`);
    }
    if (effects.legolasBonus > 0) {
      lines.push(`${this.heroName("legolas")} bonus ready`);
    }
    if (effects.balrogActive !== null) {
      lines.push(`${this.heroName("balrog")} wound armed`);
    }
    if (effects.gandalfRanks.length > 0) {
      lines.push(`Must attack rank ${effects.gandalfRanks.join(", ")}`);
    }
    return lines.length > 0 ? lines : ["No active hero effects"];
  }

  private drawEffectsPanel() {
    const ctx = this.ctx;
    const topH = Math.max(58, this.height * 0.08);
    const handH = this.height * 0.2;
    const sideW = this.width * 0.12;
    const x = this.width - sideW;
    const y = topH;
    const w = sideW;
    const h = this.height - topH - handH;
    this.panel(x, y, w, h, "rgba(22, 18, 28, 0.66)", this.panelBorder("subtle"));
    ctx.fillStyle = THEME.gold;
    ctx.font = `700 15px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, "Round Effects", x + w * 0.08, y + h * 0.065, w * 0.84);
    ctx.font = `${Math.max(11, Math.min(13, w * 0.078))}px "Ringbound Body", Georgia, serif`;
    ctx.fillStyle = THEME.text;
    this.activeEffectLines().slice(0, 7).forEach((line, index) => {
      const lineY = y + h * 0.12 + index * h * 0.07;
      ctx.fillStyle = THEME.gold;
      ctx.beginPath();
      ctx.arc(x + w * 0.11, lineY - h * 0.01, Math.max(2, this.width * 0.003), 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = THEME.text;
      drawWrappedText(ctx, line, x + w * 0.18, lineY, w * 0.74, Math.max(13, h * 0.032), 1);
    });

    const dividerY = y + h * 0.48;
    ctx.strokeStyle = "rgba(83, 72, 56, 0.72)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x + w * 0.08, dividerY);
    ctx.lineTo(x + w * 0.92, dividerY);
    ctx.stroke();

    ctx.fillStyle = THEME.gold;
    ctx.font = `700 15px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, "Action Log", x + w * 0.08, dividerY + h * 0.065, w * 0.54);

    const logAreaY = dividerY + h * 0.115;
    const logBottom = y + h - 18;
    const lineH = Math.max(12, Math.min(16, h * 0.034));
    const rowH = lineH * 2.15;
    const visibleCount = Math.max(4, Math.floor((logBottom - logAreaY) / rowH));
    const maxScroll = Math.max(0, this.gameLog.length - visibleCount);
    this.logScroll = Math.min(this.logScroll, maxScroll);
    const buttonSize = Math.max(18, Math.min(24, w * 0.14));
    const buttonGap = Math.max(6, w * 0.04);
    const buttonY = dividerY + h * 0.03;
    const downButtonX = x + w - w * 0.08 - buttonSize;
    const upButtonX = downButtonX - buttonSize - buttonGap;
    this.drawIconButton("up", "log_up", upButtonX, buttonY, buttonSize, buttonSize, this.logScroll < maxScroll);
    this.drawIconButton("down", "log_down", downButtonX, buttonY, buttonSize, buttonSize, this.logScroll > 0);

    if (this.pendingAction?.type === "choose_suit") {
      const mode = this.pendingAction.mode;
      ctx.fillStyle = THEME.text;
      ctx.font = `${Math.max(11, Math.min(13, w * 0.078))}px "Ringbound Body", Georgia, serif`;
      drawFittedText(ctx, mode === "gollum_trump" ? "Choose the crown dominion" : "Choose a dominion", x + w * 0.08, dividerY + h * 0.12, w * 0.84);
      this.allSuits.forEach((suit, index) => {
        this.drawSuitButton(suit, x + w * 0.08, dividerY + h * (0.15 + index * 0.075), w * 0.84);
      });
      return;
    }

    const end = this.gameLog.length - this.logScroll;
    const entries = this.gameLog.slice(Math.max(0, end - visibleCount), end);
    ctx.fillStyle = THEME.text;
    ctx.font = `${Math.max(11, Math.min(12, w * 0.07))}px "Ringbound Body", Georgia, serif`;
    let logY = logAreaY;
    entries.forEach((message) => {
      ctx.fillStyle = "rgba(201, 168, 76, 0.72)";
      ctx.beginPath();
      ctx.arc(x + w * 0.095, logY - lineH * 0.18, 2.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = THEME.text;
      drawWrappedText(ctx, message, x + w * 0.14, logY, w * 0.76, lineH, 2);
      logY += rowH;
    });
  }

  private drawOpponentHand() {
    const opponent = getOpponent(this.currentPlayer);
    const realmCards = this.getPlayerRealmHand(opponent);
    const heroCards = this.getPlayerHeroHand(opponent);
    const total = realmCards.length + heroCards.length;
    if (total === 0) {
      return;
    }
    const topH = Math.max(58, this.height * 0.08);
    const sideW = this.width * 0.12;
    const centerX = sideW;
    const centerW = this.width - sideW * 2;
    const y = topH + 24;
    const ctx = this.ctx;
    ctx.fillStyle = THEME.muted;
    ctx.font = `13px "Ringbound Body", Georgia, serif`;
    const revealed = this.revealedHand?.viewer === this.currentPlayer && this.revealedHand.target === opponent;
    drawFittedText(ctx, revealed ? `Revealed Opponent Realm: ${realmCards.length}` : `Opponent Hand: ${total} card${total === 1 ? "" : "s"}`, centerX + 38, y - 8, centerW - 76);

    const miniH = 48;
    const miniW = miniH / 1.5;
    const gap = 7;
    const cards = revealed ? realmCards : Array.from({ length: total });
    const totalW = cards.length * miniW + Math.max(0, cards.length - 1) * gap;
    let startX = centerX + (centerW - totalW) / 2;
    startX = Math.max(centerX + 120, startX);
    cards.forEach((card, index) => {
      const x = startX + index * (miniW + gap);
      if (revealed && card && typeof card === "object") {
        this.drawCard(card as RealmCard, x, y, miniW, miniH, false);
      } else {
        this.drawCardBack(x, y, miniW, miniH);
      }
    });
  }

  private drawTable() {
    const ctx = this.ctx;
    const topH = Math.max(58, this.height * 0.08);
    const handH = this.height * 0.2;
    const sideW = this.width * 0.12;
    const centerX = sideW;
    const centerW = this.width - sideW * 2;
    const midH = this.height - topH - handH;
    const opponentBandH = Math.max(94, Math.min(126, midH * 0.22));
    const combatY = topH + opponentBandH + midH * 0.035;
    const combatH = Math.max(260, this.height - combatY - handH - 18);
    const zoneX = centerX + centerW * 0.03;
    const zoneW = centerW * 0.94;
    const attackY = combatY + combatH * 0.03;
    const defenseY = combatY + combatH * 0.57;
    const zoneH = combatH * 0.4;
    const cardW = Math.max(64, Math.min(zoneW / 6.4, (handH * 0.74) / 1.5));

    this.drawFloatingStatus(centerX + centerW * 0.26, topH + opponentBandH - 16, centerW * 0.48);
    this.panel(zoneX, attackY, zoneW, zoneH, "rgba(26, 22, 31, 0.58)", this.panelBorder("zone"));
    this.panel(zoneX, defenseY, zoneW, zoneH, "rgba(26, 22, 31, 0.58)", this.panelBorder("zone"));

    ctx.fillStyle = THEME.muted;
    ctx.font = `14px "Ringbound Body", Georgia, serif`;
    this.textBubble("ATTACK ZONE", zoneX + zoneW / 2, attackY + zoneH * 0.11, `14px "Ringbound Body", Georgia, serif`, "rgba(18, 14, 22, 0.68)", "rgba(83, 72, 56, 0.62)", 16, 8);
    this.textBubble("DEFENSE ZONE", zoneX + zoneW / 2, defenseY + zoneH * 0.11, `14px "Ringbound Body", Georgia, serif`, "rgba(18, 14, 22, 0.68)", "rgba(83, 72, 56, 0.62)", 16, 8);

    this.drawZonePlaceholder("Attack cards appear here", zoneX, attackY, zoneW, zoneH, this.tableAttacks.length === 0);
    this.drawZonePlaceholder("Defense cards appear here", zoneX, defenseY, zoneW, zoneH, this.tableDefenses.length === 0);
    this.drawPairGuides(zoneX + zoneW * 0.04, attackY + zoneH * 0.22, defenseY + zoneH * 0.22, cardW, cardW * 1.5, zoneW * 0.92);
    this.drawOverlappedCardRow(this.tableAttacks, zoneX + zoneW * 0.04, attackY + zoneH * 0.22, zoneW * 0.92, "attack", this.pendingAction?.type === "aragorn_return", cardW, cardW * 1.5);
    this.drawOverlappedCardRow(this.tableDefenses, zoneX + zoneW * 0.04, defenseY + zoneH * 0.22, zoneW * 0.92, "noop", false, cardW, cardW * 1.5);
  }

  private drawZonePlaceholder(text: string, x: number, y: number, w: number, h: number, visible: boolean) {
    if (!visible) {
      return;
    }
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = "rgba(122, 111, 94, 0.28)";
    ctx.setLineDash([8, 8]);
    this.roundRect(x + w * 0.33, y + h * 0.28, w * 0.34, h * 0.42, 14);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(122, 111, 94, 0.72)";
    ctx.font = `14px "Ringbound Body", Georgia, serif`;
    ctx.textAlign = "center";
    ctx.fillText(ellipsizeText(ctx, text, w * 0.48), x + w / 2, y + h * 0.52);
    ctx.textAlign = "left";
    ctx.restore();
  }

  private drawPairGuides(x: number, attackY: number, defenseY: number, cardW: number, cardH: number, areaW: number) {
    const ctx = this.ctx;
    const pairs = Math.max(this.tableAttacks.length, this.tableDefenses.length);
    if (pairs === 0) {
      return;
    }
    const spacing = Math.min(cardW * 0.96, (areaW * 0.92) / Math.max(1, pairs - 0.2));
    const totalW = (pairs - 1) * spacing + cardW;
    const startX = x + (areaW - totalW) / 2;
    ctx.save();
    ctx.strokeStyle = "rgba(201, 168, 76, 0.22)";
    ctx.lineWidth = 1;
    for (let index = 0; index < pairs; index += 1) {
      const cx = startX + index * spacing + cardW / 2;
      ctx.beginPath();
      ctx.moveTo(cx, attackY + cardH + 6);
      ctx.lineTo(cx, defenseY - 6);
      ctx.stroke();
    }
    ctx.restore();
  }

  private drawActions() {
    const topH = Math.max(58, this.height * 0.08);
    const handH = this.height * 0.2;
    const sideW = this.width * 0.12;
    const x = sideW * 0.08;
    const y = topH + (this.height - topH - handH) * 0.44;
    this.panel(0, topH, sideW, this.height - topH - handH, "rgba(22, 18, 28, 0.66)", this.panelBorder("subtle"));
    const ctx = this.ctx;
    ctx.fillStyle = THEME.gold;
    ctx.font = `700 14px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, "CROWN SUIT", x + sideW * 0.02, topH + (this.height - topH - handH) * 0.065, sideW * 0.84);
    if (this.trumpCard) {
      const w = sideW * 0.7;
      this.drawCard(this.trumpCard, sideW / 2 - w / 2, topH + (this.height - topH - handH) * 0.11, w, w * 1.5, true);
    }
    this.drawMusicButton(x + sideW * 0.02, topH + (this.height - topH - handH) * 0.56, sideW * 0.84, 34);
    this.drawButton("How to Play", "how_to_play", x + sideW * 0.02, topH + (this.height - topH - handH) * 0.64, sideW * 0.84, 34, THEME.border);

    const centerX = sideW;
    const centerW = this.width - sideW * 2;
    const buttonX = centerX + centerW * 0.77;
    const buttonY = topH + (this.height - topH - handH) * 0.44;
    const buttonW = centerW * 0.19;
    const buttonH = (this.height - topH - handH) * 0.08;
    if (this.playPhase === "DEFEND" && this.pendingAction === null) {
      this.drawButton("Take Wound", "concede", buttonX, buttonY, buttonW, buttonH, THEME.ember);
    }
    if ((this.playPhase === "REINFORCE" || (this.playPhase === "ATTACK" && this.roundEffects.gandalfRanks.length > 0)) && this.pendingAction === null) {
      this.drawButton("End Attack", "end", buttonX, buttonY, buttonW, buttonH, SUIT_COLORS["Tidewake Dominion"] ?? THEME.gold);
    }
    if (this.revealedHand?.viewer === this.currentPlayer) {
      const ctx = this.ctx;
      ctx.fillStyle = THEME.gold;
      ctx.font = `700 14px "Ringbound Display", Georgia, serif`;
      drawFittedText(ctx, `${this.revealedHand.target} revealed`, x, y + 140, sideW - 44);
      this.drawCardRow(this.getPlayerRealmHand(this.revealedHand.target), x, y + 154, "attack", false, 50, 75);
    }
  }

  private drawHand() {
    const hand = [...this.getPlayerRealmHand(this.currentPlayer), ...this.getPlayerHeroHand(this.currentPlayer)];
    const handH = this.height * 0.2;
    const panelY = this.height - handH + 10;
    const y = panelY + 18;
    const ctx = this.ctx;
    this.panel(12, panelY, this.width - 24, handH - 20, "rgba(18, 14, 22, 0.82)", this.panelBorder("subtle"));
    ctx.fillStyle = THEME.gold;
    ctx.font = `700 18px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, "Player Hand", 30, panelY + 18, 180);
    const cardW = Math.max(64, Math.min((this.height * 0.2 * 0.74) / 1.5, (this.width - 120) / 9));
    this.drawOverlappedCardRow(hand, 30, y, this.width - 60, "hand", true, cardW, cardW * 1.5, (card) => this.isCardPlayable(card));
  }

  private drawLog() {
    const ctx = this.ctx;
    const layout = this.rightPanelLayout();
    const { x, w, logY: y, logH: h } = layout;
    this.panel(x, y, w, h, "rgba(18, 14, 22, 0.72)", "rgba(83, 72, 56, 0.72)");
    ctx.fillStyle = THEME.gold;
    ctx.font = `700 15px "Ringbound Display", Georgia, serif`;
    drawFittedText(ctx, "Log", x + 16, y + 26, w - 32);
    ctx.fillStyle = THEME.text;
    ctx.font = `13px "Ringbound Body", Georgia, serif`;
    const maxEntries = Math.max(1, Math.floor((h - 46) / 32));
    this.gameLog.slice(-maxEntries).forEach((message, index) => {
      drawWrappedText(ctx, message, x + 16, y + 52 + index * 32, w - 32, 15, 2);
    });
  }

  private drawCardRow(
    cards: Card[],
    x: number,
    y: number,
    kind: CardHitbox["kind"],
    clickable: boolean,
    cardW = 88,
    cardH = 124,
    playable?: (card: Card) => boolean,
    maxRowW?: number
  ) {
    const gap = Math.max(6, cardW * 0.12);
    const hoveredIndex = cards.findIndex((_, index) => this.hoveredHitbox?.kind === kind && this.hoveredHitbox.index === index);
    const expansion = 1.035;
    const rowW = maxRowW ?? Math.max(0, this.width - x - 32);
    const totalRowW = cards.length > 0 ? cards.length * cardW + Math.max(0, cards.length - 1) * gap : 0;
    const startX = x + Math.max(0, (rowW - totalRowW) / 2);
    const baseXs = cards.map((_, index) => startX + index * (cardW + gap));
    const shiftedXs = this.shiftCardXsForHover(baseXs, cardW, x, rowW, hoveredIndex, expansion);
    cards.forEach((card, index) => {
      const cardX = shiftedXs[index] ?? baseXs[index]!;
      if (cardX + cardW > this.width - 32) {
        return;
      }
      const active = !clickable || (playable ? playable(card) : true);
      const isHovered = this.hoveredHitbox?.kind === kind && this.hoveredHitbox.index === index;
      const drawW = isHovered && active ? cardW * expansion : cardW;
      const drawH = isHovered && active ? cardH * expansion : cardH;
      this.drawCard(card, cardX - (drawW - cardW) / 2, y - (drawH - cardH) / 2, drawW, drawH, active);
      if (clickable) {
        this.addHitbox({ kind, x: cardX, y, w: cardW, h: cardH, index, enabled: active, card });
      } else {
        this.addHitbox({ kind, x: cardX, y, w: cardW, h: cardH, index, enabled: true, card });
      }
    });
  }

  private drawOverlappedCardRow(
    cards: Card[],
    areaX: number,
    areaY: number,
    areaW: number,
    kind: CardHitbox["kind"],
    clickable: boolean,
    cardW: number,
    cardH: number,
    playable?: (card: Card) => boolean
  ) {
    if (cards.length === 0) {
      return;
    }
    const spacing = Math.min(cardW * 0.96, (areaW * 0.92) / Math.max(1, cards.length - 0.2));
    const totalW = (cards.length - 1) * spacing + cardW;
    const startX = areaX + (areaW - totalW) / 2;
    const hoveredIndex = cards.findIndex((_, index) => this.hoveredHitbox?.kind === kind && this.hoveredHitbox.index === index);
    const expansion = 1.035;
    const baseXs = cards.map((_, index) => startX + index * spacing);
    const shiftedXs = this.shiftCardXsForHover(baseXs, cardW, areaX, areaW, hoveredIndex, expansion);
    cards.forEach((card, index) => {
      const cardX = shiftedXs[index] ?? baseXs[index]!;
      const active = !clickable || (playable ? playable(card) : true);
      const isHovered = this.hoveredHitbox?.kind === kind && this.hoveredHitbox.index === index;
      const drawW = isHovered && active ? cardW * expansion : cardW;
      const drawH = isHovered && active ? cardH * expansion : cardH;
      this.drawCard(card, cardX - (drawW - cardW) / 2, areaY - (drawH - cardH) / 2, drawW, drawH, active);
      if (clickable) {
        this.addHitbox({ kind, x: cardX, y: areaY, w: cardW, h: cardH, index, enabled: active, card });
      } else {
        this.addHitbox({ kind, x: cardX, y: areaY, w: cardW, h: cardH, index, enabled: true, card });
      }
    });
  }

  private shiftCardXsForHover(baseXs: number[], cardW: number, areaX: number, areaW: number, hoveredIndex: number, expansion: number) {
    if (hoveredIndex < 0 || hoveredIndex >= baseXs.length) {
      return baseXs;
    }
    const push = Math.max(6, cardW * (expansion - 1) * 2.8);
    const shifted = baseXs.map((cardX, index) => {
      if (index < hoveredIndex) {
        return cardX - push;
      }
      if (index > hoveredIndex) {
        return cardX + push;
      }
      return cardX;
    });
    const hoverExtra = (cardW * expansion - cardW) / 2;
    const minX = Math.min(...shifted, shifted[hoveredIndex]! - hoverExtra);
    const maxX = Math.max(...shifted.map((cardX, index) => cardX + (index === hoveredIndex ? cardW * expansion : cardW)));
    let correction = 0;
    if (minX < areaX) {
      correction = areaX - minX;
    } else if (maxX > areaX + areaW) {
      correction = areaX + areaW - maxX;
    }
    return shifted.map((cardX) => cardX + correction);
  }

  private drawCard(card: Card, x: number, y: number, w: number, h: number, active: boolean) {
    const ctx = this.ctx;
    if (isHero(card) && card.id === "boromir_guard") {
      this.drawAutoDefenseToken(card, x, y, w, h, active);
      return;
    }

    const isRealmCard = isRealm(card);
    const suitColor = isRealmCard ? SUIT_COLORS[card.suit] ?? THEME.gold : card.faction === "Shadow" ? THEME.ember : THEME.gold;
    const assetImage = this.getCardImage(card);
    if (assetImage?.complete && assetImage.naturalWidth > 0) {
      this.drawCardAsset(assetImage, x, y, w, h, active, suitColor);
      return;
    }

    ctx.save();
    if (active) {
      ctx.shadowColor = rgba(suitColor, 0.4);
      ctx.shadowBlur = 16;
    }
    ctx.fillStyle = THEME.surface;
    this.roundRect(x, y, w, h, w * 0.09);
    ctx.fill();
    this.strokeCardBorder(x, y, w, h, suitColor, active);
    ctx.restore();

    ctx.save();
    this.roundRect(x, y, w, h, w * 0.09);
    ctx.clip();

    ctx.fillStyle = isRealmCard ? "rgba(232, 223, 200, 0.07)" : "rgba(201, 168, 76, 0.08)";
    this.roundRect(x + w * 0.08, y + h * 0.08, w * 0.84, h * 0.18, w * 0.04);
    ctx.fill();

    if (!active) {
      this.applyDisabledOverlay(x, y, w, h);
    }

    ctx.fillStyle = isRealmCard ? THEME.muted : suitColor;
    ctx.font = `700 ${Math.max(10, w * 0.13)}px "Ringbound Body", Georgia, serif`;
    if (isRealmCard) {
      drawFittedText(ctx, card.suit.toUpperCase(), x + w * 0.08, y + h * 0.18, w * 0.56);
      ctx.fillStyle = suitColor;
      ctx.font = `700 ${Math.max(24, w * 0.46)}px "Ringbound Display", Georgia, serif`;
      ctx.textAlign = "center";
      ctx.fillText(String(card.rank), x + w * 0.5, y + h * 0.62);
      ctx.textAlign = "left";
      this.drawSuitMark(card.suit, x + w * 0.82, y + h * 0.17, w * 0.12, suitColor);
    } else {
      ctx.fillStyle = THEME.text;
      ctx.font = `700 ${Math.max(12, w * 0.15)}px "Ringbound Body", Georgia, serif`;
      drawWrappedText(ctx, card.name, x + w * 0.08, y + h * 0.18, w * 0.78, h * 0.09, 2);
      ctx.fillStyle = suitColor;
      ctx.font = `${Math.max(10, w * 0.12)}px "Ringbound Body", Georgia, serif`;
      drawFittedText(ctx, card.faction, x + w * 0.08, y + h * 0.32, w * 0.62);
      this.drawFactionMark(card.faction, x + w * 0.84, y + h * 0.24, w * 0.11, suitColor);
      ctx.fillStyle = THEME.text;
      ctx.font = `${Math.max(9, w * 0.105)}px "Ringbound Body", Georgia, serif`;
      drawWrappedText(ctx, card.power, x + w * 0.08, y + h * 0.48, w * 0.84, h * 0.09, 5);
    }
    ctx.restore();
    this.strokeCardBorder(x, y, w, h, suitColor, active);
  }

  private drawAutoDefenseToken(card: HeroCard, x: number, y: number, w: number, h: number, active: boolean) {
    const ctx = this.ctx;
    const accent = THEME.gold;
    ctx.save();
    if (active) {
      ctx.shadowColor = rgba(accent, 0.38);
      ctx.shadowBlur = 14;
    }
    this.roundRect(x, y, w, h, w * 0.09);
    ctx.fillStyle = "rgba(20, 16, 24, 0.92)";
    ctx.fill();
    this.strokeCardBorder(x, y, w, h, accent, active);

    const shieldX = x + w * 0.5;
    const shieldY = y + h * 0.36;
    const shieldW = w * 0.48;
    const shieldH = h * 0.33;
    ctx.beginPath();
    ctx.moveTo(shieldX, shieldY - shieldH * 0.5);
    ctx.lineTo(shieldX + shieldW * 0.42, shieldY - shieldH * 0.26);
    ctx.lineTo(shieldX + shieldW * 0.32, shieldY + shieldH * 0.32);
    ctx.quadraticCurveTo(shieldX, shieldY + shieldH * 0.58, shieldX - shieldW * 0.32, shieldY + shieldH * 0.32);
    ctx.lineTo(shieldX - shieldW * 0.42, shieldY - shieldH * 0.26);
    ctx.closePath();
    ctx.fillStyle = "rgba(201, 168, 76, 0.18)";
    ctx.fill();
    ctx.strokeStyle = accent;
    ctx.lineWidth = Math.max(2, w * 0.04);
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(shieldX, shieldY - shieldH * 0.05, Math.max(4, w * 0.08), 0, Math.PI * 2);
    ctx.strokeStyle = THEME.ember;
    ctx.lineWidth = Math.max(2, w * 0.032);
    ctx.stroke();

    ctx.fillStyle = THEME.text;
    ctx.textAlign = "center";
    ctx.font = `700 ${Math.max(13, w * 0.16)}px "Ringbound Display", Georgia, serif`;
    drawCenteredFittedText(ctx, card.name, x + w * 0.5, y + h * 0.16, w * 0.78);
    ctx.fillStyle = accent;
    ctx.font = `700 ${Math.max(10, w * 0.105)}px "Ringbound Body", Georgia, serif`;
    drawCenteredFittedText(ctx, "AUTO-DEFENSE", x + w * 0.5, y + h * 0.75, w * 0.82);
    ctx.fillStyle = THEME.muted;
    ctx.font = `${Math.max(9, w * 0.09)}px "Ringbound Body", Georgia, serif`;
    drawCenteredFittedText(ctx, "attack blocked", x + w * 0.5, y + h * 0.86, w * 0.78);
    ctx.textAlign = "left";

    if (!active) {
      this.applyDisabledOverlay(x, y, w, h);
    }
    ctx.restore();
  }

  private getCardImage(card: Card) {
    const group = isHero(card) ? "heroes" : "realm";
    const imageName = card.image;
    const imageStem = imageName.replace(/\.[^.]+$/, "");
    const assetUrl =
      CARD_ASSET_URLS[`../../output/card_placeholders/${group}/${imageStem}.png`] ??
      CARD_ASSET_URLS[`../../output/card_placeholders/${group}/${imageStem}.svg`];
    if (!assetUrl) {
      return null;
    }
    let image = this.cardImageCache.get(assetUrl);
    if (!image) {
      image = new Image();
      image.src = assetUrl;
      this.cardImageCache.set(assetUrl, image);
    }
    return image;
  }

  private drawCardAsset(image: HTMLImageElement, x: number, y: number, w: number, h: number, active: boolean, accent: string) {
    const ctx = this.ctx;
    ctx.save();
    if (active) {
      ctx.shadowColor = rgba(accent, 0.4);
      ctx.shadowBlur = 16;
    }
    this.roundRect(x, y, w, h, w * 0.09);
    ctx.clip();
    ctx.drawImage(image, x, y, w, h);
    ctx.restore();

    if (!active) {
      this.applyDisabledOverlay(x, y, w, h);
    }
    this.strokeCardBorder(x, y, w, h, accent, active);
  }

  private strokeCardBorder(x: number, y: number, w: number, h: number, accent: string, active: boolean) {
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = accent;
    ctx.lineWidth = Math.max(1.5, w * 0.032);
    this.roundRect(x, y, w, h, w * 0.09);
    ctx.stroke();
    if (active) {
      ctx.strokeStyle = accent;
      ctx.lineWidth = Math.max(2, w * 0.045);
      this.roundRect(x + w * 0.018, y + w * 0.018, w - w * 0.036, h - w * 0.036, w * 0.075);
      ctx.stroke();
    }
    ctx.restore();
  }

  private applyDisabledOverlay(x: number, y: number, w: number, h: number) {
    const ctx = this.ctx;
    ctx.save();
    this.roundRect(x, y, w, h, w * 0.09);
    ctx.clip();
    ctx.fillStyle = THEME.disabled;
    ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = "rgba(150, 145, 135, 0.3)";
    ctx.lineWidth = Math.max(1, w * 0.015);
    const step = Math.max(4, w * 0.08);
    for (let lineX = x - h; lineX < x + w; lineX += step) {
      ctx.beginPath();
      ctx.moveTo(lineX, y);
      ctx.lineTo(lineX + h, y + h);
      ctx.stroke();
    }
    ctx.restore();
  }

  private drawSuitMark(suit: string, cx: number, cy: number, size: number, color: string) {
    const ctx = this.ctx;
    ctx.fillStyle = color;
    if (suit === "Verdant Court") {
      ctx.beginPath();
      ctx.ellipse(cx - size * 0.16, cy, size * 0.7, size * 0.38, -0.68, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.ellipse(cx + size * 0.25, cy - size * 0.05, size * 0.5, size * 0.3, 0.62, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = THEME.surface;
      ctx.lineWidth = Math.max(1, size * 0.12);
      ctx.beginPath();
      ctx.moveTo(cx - size * 0.6, cy + size * 0.45);
      ctx.quadraticCurveTo(cx, cy + size * 0.05, cx + size * 0.6, cy - size * 0.35);
      ctx.stroke();
    } else if (suit === "Ember Throne") {
      ctx.beginPath();
      ctx.moveTo(cx, cy - size);
      ctx.bezierCurveTo(cx + size * 0.78, cy - size * 0.15, cx + size * 0.42, cy + size, cx, cy + size);
      ctx.bezierCurveTo(cx - size * 0.62, cy + size * 0.58, cx - size * 0.5, cy - size * 0.05, cx, cy - size);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = THEME.surface;
      ctx.beginPath();
      ctx.moveTo(cx + size * 0.03, cy - size * 0.35);
      ctx.bezierCurveTo(cx + size * 0.34, cy + size * 0.12, cx + size * 0.16, cy + size * 0.58, cx - size * 0.04, cy + size * 0.58);
      ctx.bezierCurveTo(cx - size * 0.28, cy + size * 0.34, cx - size * 0.16, cy, cx + size * 0.03, cy - size * 0.35);
      ctx.closePath();
      ctx.fill();
    } else if (suit === "Tidewake Dominion") {
      ctx.beginPath();
      ctx.moveTo(cx - size, cy + size * 0.25);
      ctx.bezierCurveTo(cx - size * 0.5, cy - size * 0.35, cx, cy - size * 0.35, cx + size * 0.48, cy + size * 0.12);
      ctx.bezierCurveTo(cx + size * 0.7, cy + size * 0.32, cx + size * 0.9, cy + size * 0.26, cx + size, cy + size * 0.12);
      ctx.lineTo(cx + size, cy + size * 0.72);
      ctx.lineTo(cx - size, cy + size * 0.72);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = THEME.surface;
      ctx.lineWidth = Math.max(1, size * 0.16);
      ctx.beginPath();
      ctx.moveTo(cx - size * 0.72, cy + size * 0.52);
      ctx.bezierCurveTo(cx - size * 0.2, cy + size * 0.2, cx + size * 0.25, cy + size * 0.82, cx + size * 0.78, cy + size * 0.42);
      ctx.stroke();
    } else if (suit === "Obsidian Veil") {
      ctx.beginPath();
      ctx.arc(cx, cy, size, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalCompositeOperation = "destination-out";
      ctx.beginPath();
      ctx.arc(cx + size * 0.38, cy - size * 0.18, size * 0.82, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalCompositeOperation = "source-over";
    } else {
      ctx.beginPath();
      ctx.moveTo(cx - size, cy);
      ctx.lineTo(cx - size * 0.3, cy - size * 0.65);
      ctx.lineTo(cx + size * 0.75, cy - size * 0.25);
      ctx.lineTo(cx + size, cy + size * 0.2);
      ctx.lineTo(cx - size * 0.25, cy + size * 0.6);
      ctx.closePath();
      ctx.fill();
    }
  }

  private drawFactionMark(faction: string, cx: number, cy: number, size: number, color: string) {
    const ctx = this.ctx;
    ctx.fillStyle = color;
    if (faction === "Fellowship") {
      ctx.beginPath();
      ctx.moveTo(cx, cy - size);
      ctx.lineTo(cx + size, cy);
      ctx.lineTo(cx, cy + size);
      ctx.lineTo(cx - size, cy);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = THEME.surface;
      ctx.beginPath();
      ctx.arc(cx, cy, size * 0.32, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.beginPath();
      ctx.arc(cx, cy, size, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = THEME.surface;
      ctx.lineWidth = Math.max(2, size * 0.28);
      ctx.beginPath();
      ctx.arc(cx, cy, size * 0.56, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  private drawCardBack(x: number, y: number, w: number, h: number) {
    const ctx = this.ctx;
    ctx.save();
    ctx.fillStyle = THEME.surface;
    ctx.strokeStyle = THEME.gold;
    ctx.lineWidth = Math.max(1, w * 0.05);
    this.roundRect(x, y, w, h, w * 0.09);
    ctx.fill();
    ctx.stroke();
    ctx.strokeStyle = "rgba(83, 72, 56, 0.8)";
    ctx.lineWidth = Math.max(1, w * 0.025);
    this.roundRect(x + w * 0.16, y + h * 0.14, w * 0.68, h * 0.72, w * 0.04);
    ctx.stroke();
    ctx.strokeStyle = THEME.ember;
    ctx.lineWidth = Math.max(1, w * 0.06);
    ctx.beginPath();
    ctx.arc(x + w * 0.5, y + h * 0.5, w * 0.17, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = THEME.gold;
    ctx.beginPath();
    ctx.arc(x + w * 0.5, y + h * 0.5, w * 0.07, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  private drawHoveredCardPreview() {
    const anchor = this.hoveredHitbox;
    const card = anchor?.card;
    if (!anchor || !card || this.mouseX < 0 || this.mouseY < 0) {
      return;
    }
    const scale = 2.05;
    let w = Math.min(230, anchor.w * scale);
    let h = w * 1.5;
    const margin = 14;
    if (h > this.height - margin * 2) {
      h = this.height - margin * 2;
      w = h / 1.5;
    }
    let x = anchor.x + anchor.w / 2 - w / 2;
    let y = anchor.y + anchor.h / 2 - h / 2;
    x = Math.max(margin, Math.min(this.width - w - margin, x));
    y = Math.max(margin, Math.min(this.height - h - margin, y));

    const ctx = this.ctx;
    ctx.save();
    ctx.shadowColor = "rgba(0, 0, 0, 0.55)";
    ctx.shadowBlur = 18;
    ctx.shadowOffsetY = 8;
    this.panel(x - w * 0.04, y - h * 0.04, w * 1.08, h * 1.08, "rgba(10, 8, 12, 0.43)", "rgba(201, 168, 76, 0.32)");
    ctx.restore();
    this.drawCard(card, x, y, w, h, true);
  }

  private drawCustomCursor() {
    if (!this.hoveredHitbox || this.mouseX < 0 || this.mouseY < 0) {
      return;
    }
    const ctx = this.ctx;
    const radius = Math.max(5, this.height * 0.008);
    ctx.save();
    ctx.strokeStyle = THEME.gold;
    ctx.lineWidth = Math.max(1, radius * 0.35);
    ctx.beginPath();
    ctx.arc(this.mouseX, this.mouseY, radius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(this.mouseX - radius * 2, this.mouseY);
    ctx.lineTo(this.mouseX + radius * 2, this.mouseY);
    ctx.moveTo(this.mouseX, this.mouseY - radius * 2);
    ctx.lineTo(this.mouseX, this.mouseY + radius * 2);
    ctx.stroke();
    ctx.restore();
  }

  private cardHint(card: RealmCard) {
    if (this.playPhase === "DEFEND") {
      return this.canDefendWithCard(card, this.getCurrentAttackCard()) ? "Playable defense." : "Needs higher matching dominion or valid crown.";
    }
    return this.canAttackWithCard(card) ? "Playable attack." : "Must match a rank already on the table.";
  }

  private drawButton(label: string, action: string, x: number, y: number, w: number, h: number, color = THEME.gold) {
    const ctx = this.ctx;
    const isHovered = this.hoveredHitbox?.kind === "button" && this.hoveredHitbox.label === action && this.hoveredHitbox.x === x && this.hoveredHitbox.y === y;
    ctx.save();
    if (isHovered) {
      ctx.shadowColor = "rgba(224, 195, 95, 0.38)";
      ctx.shadowBlur = 14;
    }
    ctx.fillStyle = rgba(color, isHovered ? 0.82 : 0.68);
    this.roundRect(x, y, w, h, Math.max(1, h * 0.24));
    ctx.fill();
    ctx.strokeStyle = "rgba(232, 223, 200, 0.58)";
    ctx.lineWidth = Math.max(1, h * 0.08);
    ctx.stroke();
    ctx.restore();
    ctx.fillStyle = THEME.text;
    ctx.font = `700 15px "Ringbound Body", Georgia, serif`;
    ctx.textAlign = "center";
    ctx.fillText(ellipsizeText(ctx, label, w - 18), x + w / 2, y + h / 2 + 5);
    ctx.textAlign = "left";
    this.addHitbox({ kind: "button", label: action, x, y, w, h, enabled: true });
  }

  private drawMusicButton(x: number, y: number, w: number, h: number) {
    const label = this.musicEnabled ? "Music On" : "Music Off";
    const color = this.musicEnabled ? THEME.gold : THEME.border;
    this.drawButton(label, "music_toggle", x, y, w, h, color);
  }

  private drawIconButton(direction: "up" | "down", action: string, x: number, y: number, w: number, h: number, enabled: boolean) {
    const ctx = this.ctx;
    const isHovered = enabled && this.hoveredHitbox?.kind === "button" && this.hoveredHitbox.label === action;
    ctx.save();
    ctx.fillStyle = enabled ? rgba(THEME.gold, isHovered ? 0.72 : 0.58) : "rgba(83, 72, 56, 0.45)";
    this.roundRect(x, y, w, h, Math.max(1, h * 0.2));
    ctx.fill();
    ctx.strokeStyle = "rgba(232, 223, 200, 0.45)";
    ctx.lineWidth = Math.max(1, h * 0.08);
    ctx.stroke();
    const cx = x + w / 2;
    const cy = y + h / 2;
    const offset = Math.max(3, h * 0.18);
    const points =
      direction === "up"
        ? [
            [cx, cy - offset],
            [cx - offset, cy + offset],
            [cx + offset, cy + offset]
          ]
        : [
            [cx, cy + offset],
            [cx - offset, cy - offset],
            [cx + offset, cy - offset]
          ];
    ctx.fillStyle = enabled ? THEME.text : THEME.muted;
    ctx.beginPath();
    ctx.moveTo(points[0]![0], points[0]![1]);
    ctx.lineTo(points[1]![0], points[1]![1]);
    ctx.lineTo(points[2]![0], points[2]![1]);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
    this.addHitbox({ kind: "button", label: action, x, y, w, h, enabled });
  }

  private drawSuitButton(suit: string, x: number, y: number, w = 104) {
    const ctx = this.ctx;
    const color = SUIT_COLORS[suit] ?? THEME.gold;
    const isHovered = this.hoveredHitbox?.kind === "suit" && this.hoveredHitbox.suit === suit;
    ctx.fillStyle = rgba(color, isHovered ? 0.82 : 0.68);
    this.roundRect(x, y, w, 36, 9);
    ctx.fill();
    ctx.strokeStyle = "rgba(232, 223, 200, 0.58)";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = THEME.text;
    ctx.font = `700 14px "Ringbound Body", Georgia, serif`;
    ctx.textAlign = "center";
    ctx.fillText(ellipsizeText(ctx, suit, w - 16), x + w / 2, y + 23);
    ctx.textAlign = "left";
    this.addHitbox({ kind: "suit", suit, x, y, w, h: 36 });
  }
}
