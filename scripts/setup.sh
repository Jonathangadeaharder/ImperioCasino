#!/usr/bin/env bash
set -euo pipefail

PB_DIR="$(dirname "$0")/../pocketbase"
PB_BIN="$PB_DIR/pocketbase"
PB_DATA="$PB_DIR/pb_data"
PB_URL="http://127.0.0.1:8090"

if [ "$(uname -s)" = "Darwin" ]; then
    if [ "$(uname -m)" = "arm64" ]; then
        PB_URL_DL="https://github.com/pocketbase/pocketbase/releases/download/v0.22.0/pocketbase_0.22.0_darwin_arm64.zip"
    else
        PB_URL_DL="https://github.com/pocketbase/pocketbase/releases/download/v0.22.0/pocketbase_0.22.0_darwin_amd64.zip"
    fi
elif [ "$(uname -s)" = "Linux" ]; then
    PB_URL_DL="https://github.com/pocketbase/pocketbase/releases/download/v0.22.0/pocketbase_0.22.0_linux_amd64.zip"
else
    echo "Unsupported OS"; exit 1
fi

if [ ! -f "$PB_BIN" ]; then
    echo "Downloading PocketBase..."
    mkdir -p "$PB_DIR"
    curl -L "$PB_URL_DL" -o /tmp/pb.zip
    unzip -o /tmp/pb.zip -d "$PB_DIR/"
    chmod +x "$PB_BIN"
    rm /tmp/pb.zip
fi

if [ ! -d "$PB_DATA" ]; then
    echo "Starting PocketBase to initialize..."
    "$PB_BIN" serve --dir="$PB_DATA" --http="127.0.0.1:8090" &
    PB_PID=$!
    sleep 2

    echo "Creating admin..."
    curl -s -X POST "$PB_URL/api/admins" \
        -H "Content-Type: application/json" \
        -d '{"email":"admin@imperiocasino.com","password":"changeme123!","passwordConfirm":"changeme123!"}' > /dev/null

    TOKEN=$(curl -s "$PB_URL/api/admins/auth-with-password" \
        -H "Content-Type: application/json" \
        -d '{"identity":"admin@imperiocasino.com","password":"changeme123!"}' | \
        python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

    echo "Adding coins field to users..."
    curl -s -X PATCH "$PB_URL/api/collections/_pb_users_auth_" \
        -H "Authorization: $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
        "schema": [
            {"system":false,"id":"users_name","name":"name","type":"text","required":false,"presentable":false,"unique":false,"options":{"min":null,"max":null,"pattern":""}},
            {"system":false,"id":"users_avatar","name":"avatar","type":"file","required":false,"presentable":false,"unique":false,"options":{"mimeTypes":["image/jpeg","image/png","image/svg+xml","image/gif","image/webp"],"thumbs":null,"maxSelect":1,"maxSize":5242880,"protected":false}},
            {"system":false,"id":"coins","name":"coins","type":"number","required":false,"presentable":true,"unique":false,"options":{"min":0,"max":null,"noDecimal":true}}
        ]
    }' > /dev/null

    echo "Creating blackjack_games collection..."
    curl -s -X POST "$PB_URL/api/collections" \
        -H "Authorization: $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
        "name": "blackjack_games",
        "type": "base",
        "schema": [
            {"name":"user","type":"relation","required":true,"options":{"collectionId":"_pb_users_auth_","maxSelect":1}},
            {"name":"deck","type":"text","required":true},
            {"name":"dealer_hand","type":"text","required":true},
            {"name":"player_hand","type":"text","required":true},
            {"name":"player_second_hand","type":"text","required":false},
            {"name":"player_coins","type":"number","required":true,"options":{"noDecimal":true}},
            {"name":"current_wager","type":"number","required":true,"options":{"noDecimal":true}},
            {"name":"game_over","type":"bool","required":true},
            {"name":"message","type":"text","required":false},
            {"name":"player_stood","type":"bool","required":true},
            {"name":"double_down","type":"bool","required":true},
            {"name":"split","type":"bool","required":true},
            {"name":"current_hand","type":"text","required":true},
            {"name":"dealer_value","type":"number","required":true,"options":{"noDecimal":true}}
        ],
        "listRule": "user = @request.auth.id",
        "viewRule": "user = @request.auth.id",
        "createRule": "user = @request.auth.id",
        "updateRule": "user = @request.auth.id",
        "deleteRule": null
    }' > /dev/null

    kill $PB_PID 2>/dev/null
    echo "Setup complete. Run 'pnpm dev' to start."
fi
