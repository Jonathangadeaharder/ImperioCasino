// Define the server address
const serverAddress = 'http://127.0.0.1:5000';

// Function to parse query parameters
function getQueryParams() {
	const params = {};
	const queryString = window.location.search.substring(1);
	const regex = /([^&=]+)=([^&]*)/g;
	let match;
	while (match = regex.exec(queryString)) {
		params[decodeURIComponent(match[1])] = decodeURIComponent(match[2]);
	}
	return params;
}

// Extract token and username from URL
const queryParams = getQueryParams();
const token = queryParams.token;
const username = queryParams.username;

// Initialize variables
var currentChipBalance = null;
var currentWager = 0;
var dealerGameBoard = $("#dealer");
var playerGameBoard = $("#user-hand");
var playerSplitGameBoard = $("#user-split-hand");
var dealerHandTotalDisplay = $(".dealer-hand-total");
var playerHandTotalDisplay = $(".hand-total");
var playerSplitHandTotalDisplay = $(".split-hand-total");
var dealerHandTotal = 0;
var playerHandTotal = 0;
var playerSplitHandTotal = 0;

// Get initial coin balance
$(document).ready(function() {
	getCoins();
});

// Function to get coins from the server
function getCoins() {
	if (!token) {
		console.error('Token not found in URL');
		return;
	}

	fetch(`${serverAddress}/getCoins`, {
		method: 'GET',
		headers: {
			'Authorization': 'Bearer ' + token,
			'Content-Type': 'application/json'
		}
	})
		.then(response => response.json())
		.then(data => {
			console.log('Coins:', data.coins);
			currentChipBalance = data.coins;
			updateVisibleChipBalances();
		})
		.catch(error => {
			console.error('Error fetching coins:', error);
			Materialize.toast("Error fetching your coin balance.", 2000);
		});
}

// Update chip totals displayed to user throughout the game
function updateVisibleChipBalances() {
	$(".current-wager").text(currentWager);
	$(".current-chip-balance").text(currentChipBalance);
}

// Function to select a wager
function selectWager(amount) {
	if (currentChipBalance === null) {
		Materialize.toast("Fetching your coin balance, please wait...", 1000);
		return;
	}

	if (currentChipBalance < amount) {
		Materialize.toast("You don't have enough coins to select that bet", 2000);
		return;
	}

	currentWager = amount;
	updateVisibleChipBalances();
}

// Event listeners for wager selection
$("#chip-10").click(function() { selectWager(10); });
$("#chip-25").click(function() { selectWager(25); });
$("#chip-50").click(function() { selectWager(50); });
$("#chip-100").click(function() { selectWager(100); });

// Start a new game
var startButton = $("#start-game-button");
startButton.click(startGame);

function startGame() {
	if (currentChipBalance === null) {
		Materialize.toast("Fetching your coin balance, please wait...", 1000);
		return;
	}

	if (currentWager === 0) {
		Materialize.toast("You must select a bet to play", 1000);
		return;
	}

	if (currentChipBalance < currentWager) {
		Materialize.toast("You don't have enough coins to place that bet", 2000);
		return;
	}

	fetch(`${serverAddress}/blackjack/start`, {
		method: 'POST',
		headers: {
			'Authorization': 'Bearer ' + token,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ wager: currentWager })
	})
		.then(response => response.json())
		.then(gameState => {
			if (gameState.message) {
				Materialize.toast(gameState.message, 2000);
			} else {
				console.log(gameState)
				currentChipBalance = gameState.player_coins;
				updateVisibleChipBalances();
				$("#welcome").hide();
				$("#game-over").hide();
				$(".brand-logo").text("ImperioJack");
				$("#game-board").show("fade", 1000);
				updateGameBoard(gameState);
			}
		})
		.catch(error => {
			console.error('Error starting game:', error);
			Materialize.toast("Error starting game.", 2000);
		});
}

// Action buttons
var hitButton = $("#hit-button");
var standButton = $("#stand-button");
var doubleDownButton = $("#double-down-button");
var splitButton = $(".split-button");

hitButton.click(function() { sendAction('hit'); });
standButton.click(function() { sendAction('stand'); });
doubleDownButton.click(function() { sendAction('double'); });
splitButton.click(function() { sendAction('split'); });

function sendAction(action) {
	fetch(`${serverAddress}/blackjack/action`, {
		method: 'POST',
		headers: {
			'Authorization': 'Bearer ' + token,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ action: action })
	})
		.then(response => response.json())
		.then(gameState => {
			if (gameState.message) {
				Materialize.toast(gameState.message, 2000);
			}
			currentChipBalance = gameState.player_coins;
			updateVisibleChipBalances();
			updateGameBoard(gameState);
		})
		.catch(error => {
			console.error(`Error performing action ${action}:`, error);
			Materialize.toast(`Error performing action ${action}.`, 2000);
		});
}

function capitalizeFirstLetter(val) {
	if (val === undefined || val === null) {
		return 'Unknown';
	}
	if (!isNaN(val) || /^\d+$/.test(val)) {
		return val;
	}
	return String(val).charAt(0).toUpperCase() + String(val).slice(1);
}
// Update the game board
function updateGameBoard(gameState) {
	// Clear current hands
	dealerGameBoard.empty();
	playerGameBoard.empty();
	playerSplitGameBoard.empty();

	// Reset totals
	dealerHandTotal = 0;
	playerHandTotal = 0;
	playerSplitHandTotal = 0;

	// Helper function to get card image URL
	function getCardImageUrl(card) {
		const suit = card.suit ? capitalizeFirstLetter(card.suit) : 'Unknown';
		const name = card.name ? capitalizeFirstLetter(card.name) : 'Unknown';
		return `img/${suit}-${name}.png`;
	}

	// Update dealer's hand
	gameState.dealer_hand.forEach((card, index) => {
		console.log("Dealer card:", card);
		console.log("Dealer card suit:", card.suit);
		console.log("Dealer card name:", card.name);
		let cardImage = $("<img>").attr("class", "card").attr("src", getCardImageUrl(card));
		cardImage.attr("id", `dealer-card-${index}`);
		cardImage.appendTo(dealerGameBoard);

		dealerHandTotal += card.value;
	});

	// Update player's hand
	gameState.player_hand.forEach((card, index) => {
		console.log("Player card:", card);
		console.log("Player card suit:", card.suit);
		console.log("Player card name:", card.name);
		let cardImage = $("<img>").attr("class", "card").attr("src", getCardImageUrl(card));
		cardImage.attr("id", `player-card-${index}`);
		cardImage.appendTo(playerGameBoard);

		playerHandTotal += card.value;
	});

	// Update split hand if applicable
	if (gameState.split && gameState.player_second_hand) {
		gameState.player_second_hand.forEach((card, index) => {
			console.log("Split card:", card);
			console.log("Split card suit:", card.suit);
			console.log("Split card name:", card.name);
			let cardImage = $("<img>").attr("class", "card").attr("src", getCardImageUrl(card));
			cardImage.attr("id", `playerSplit-card-${index}`);
			cardImage.appendTo(playerSplitGameBoard);

			playerSplitHandTotal += card.value;
		});
		$(playerSplitGameBoard).show();
		$(".split-hand-total").show();
	} else {
		$(playerSplitGameBoard).hide();
		$(".split-hand-total").hide();
	}

	// Update hand totals displayed
	updateVisibleHandTotals();

	// Enable or disable action buttons based on the game state
	if (gameState.game_over) {
		hitButton.prop('disabled', true);
		standButton.prop('disabled', true);
		doubleDownButton.prop('disabled', true);
		splitButton.prop('disabled', true);
		setTimeout(function() {
			announceWinner(gameState);
		}, 2000); // 2000 milliseconds = 2 seconds
	} else {
		hitButton.prop('disabled', false);
		standButton.prop('disabled', false);
		doubleDownButton.prop('disabled', !gameState.can_double_down);
		splitButton.prop('disabled', !gameState.can_split);
	}
}
// Update hand totals displayed
function updateVisibleHandTotals() {
	$(playerHandTotalDisplay).text(playerHandTotal);
	$(playerSplitHandTotalDisplay).text(playerSplitHandTotal);
	$(".dealer-hand-total").text(dealerHandTotal);
}

// Announce winner
function announceWinner(gameState) {
	$("#game-board").hide();
	$("#game-over").show("drop", 500);
	$("#game-outcome").text(gameState.message);
}

// Play again
var playAgainButton = $(".new-game-button");
playAgainButton.click(newGame);

function newGame() {
	currentWager = 0;
	updateVisibleChipBalances();
	$("#game-over").hide();
	$("#welcome").show();
}

// Reset game
$("#reset-game").click(resetGame);

function resetGame() {
	// Implement reset game logic if needed
	currentWager = 0;
	currentChipBalance = null;
	getCoins();
	$("#game-over").hide();
	$("#game-board").hide();
	$("#welcome").show();
}
