#!/bin/bash

# Define paths and commands
BLACKJACK_PATH="./blackjack-master"
CHERRY_CHARM_PATH="./cherry-charm"
ROULETTE_PATH="./roulette"
SESSION_MANAGEMENT_PATH="./session_management"

FLASK_COMMAND="flask run"
CHERRY_CHARM_COMMAND="yarn dev"

# Function to start a server in a new screen session
start_server() {
    local path="$1"
    local command="$2"
    local session_name="$3"

    # Check if the screen session already exists
    if screen -list | grep -q "$session_name"; then
        echo "Screen session '$session_name' already exists. Skipping..."
    else
        echo "Starting $session_name server..."
        screen -dmS "$session_name" bash -c "cd $path && $command"
        echo "$session_name server started in screen session '$session_name'."
    fi
}

# Start servers with shorter screen session names
start_server "$BLACKJACK_PATH" "$FLASK_COMMAND" "bj"
start_server "$CHERRY_CHARM_PATH" "$CHERRY_CHARM_COMMAND" "cc"
start_server "$ROULETTE_PATH" "$FLASK_COMMAND" "rt"
start_server "$SESSION_MANAGEMENT_PATH" "$FLASK_COMMAND" "sm"

echo "All servers started with short screen session names."
echo "Use 'screen -list' to view active sessions."
echo "Attach to a session using 'screen -r <session_name>'."
