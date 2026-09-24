#!/bin/bash

# Configuration
LOCAL_DIR="./"
REMOTE_DIR="$WP_DOCUMENT_ROOT"
TMP_REMOTE_DIR="veriaguide_sync_tmp" # Relative to user home
EXCLUDE_FILE="rsync_exclude.txt"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}VeriaGuide VPS Sync Tool${NC}"
echo "--------------------------------"

# Check for VPS details
if [ -z "$1" ]; then
    read -p "Enter VPS User (e.g., ***REMOVED***): " VPS_USER
else
    VPS_USER=$1
fi

if [ -z "$2" ]; then
    read -p "Enter VPS Host (IP or domain): " VPS_HOST
else
    VPS_HOST=$2
fi

if [ -z "$3" ]; then
    read -p "Enter SSH Port (default: 22): " VPS_PORT
    VPS_PORT=${VPS_PORT:-22}
else
    VPS_PORT=$3
fi

TARGET="$VPS_USER@$VPS_HOST"
SSH_CMD="ssh -p $VPS_PORT"

# Clean up known_hosts quietly
ssh-keygen -R "[$VPS_HOST]:$VPS_PORT" &>/dev/null

echo -e "\n${YELLOW}Checking connection to $TARGET...${NC}"
if $SSH_CMD -q -o BatchMode=yes -o ConnectTimeout=5 "$TARGET" exit 2>/dev/null; then
    echo -e "${GREEN}Connection successful!${NC}"
else
    echo -e "${YELLOW}Verification failed. Connection might still work if you enter password later.${NC}"
fi

echo -e "\n${YELLOW}Operation Menu:${NC}"
echo "1. Sync Files (Standard) - Use if you have write access"
echo "2. Check Remote Permissions (View Only)"
echo "3. Sync via Sudo Staging (Use if Option 1 fails / Permission Denied)"
echo "4. Exit"

read -p "Select action (1-4): " START_ACTION

# Standard Rsync Options
RSYNC_OPTS=(-avz --update --progress --exclude-from="$EXCLUDE_FILE")

if [ "$START_ACTION" == "2" ]; then
    echo -e "\n${YELLOW}Checking permissions on '$REMOTE_DIR'...${NC}"
    $SSH_CMD -t "$TARGET" "ls -la $REMOTE_DIR | head -n 20"
    exit 0
elif [ "$START_ACTION" == "4" ]; then
    exit 0
fi

# --- OPTION 3: STAGING STRATEGY ---
if [ "$START_ACTION" == "3" ]; then
    echo -e "\n${YELLOW}=== Sudo Staging Mode ===${NC}"
    echo "1. Uploading files to temporary folder (~/$TMP_REMOTE_DIR)..."
    
    # 1. Upload to tmp folder in user home
    rsync -e "$SSH_CMD" "${RSYNC_OPTS[@]}" "$LOCAL_DIR" "$TARGET:$TMP_REMOTE_DIR/"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Upload to temp folder failed.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Upload complete.${NC}"
    echo -e "\n2. Moving files to final destination using sudo..."
    echo -e "${YELLOW}You will be asked for your VPS password now to grant sudo rights.${NC}"
    
    # 2. Move files using sudo inside an interactive ssh session
    # We use rsync locally on the server to merge directories
    REMOTE_SCRIPT="
        echo '-> Applying updates...';
        sudo rsync -av --update $TMP_REMOTE_DIR/ $REMOTE_DIR/;
        echo '-> Cleaning up temp files...';
        rm -rf $TMP_REMOTE_DIR;
        echo '-> Fixing ownership to www-data...';
        sudo chown -R www-data:www-data $REMOTE_DIR;
        echo '-> Done!';
    "
    
    $SSH_CMD -t "$TARGET" "$REMOTE_SCRIPT"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Sync and move completed successfully.${NC}"
    else
        echo -e "${RED}Failed to move files. Check sudo password.${NC}"
        exit 1
    fi

# --- OPTION 1: STANDARD DIRECT SYNC ---
elif [ "$START_ACTION" == "1" ]; then
    echo -e "\n${YELLOW}Performing DRY RUN (No files will be changed)...${NC}"
    rsync -n -e "$SSH_CMD" "${RSYNC_OPTS[@]}" "$LOCAL_DIR" "$TARGET:$REMOTE_DIR/"

    if [ $? -ne 0 ]; then
         echo -e "${RED}Dry run failed!${NC}"
         echo "If this is a permission error, try Option 3 (Sync via Sudo Staging)."
         exit 1
    fi

    echo -e "\n${YELLOW}Review the list above.${NC}"
    read -p "Do you want to proceed with the actual upload? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborted.${NC}"
        exit 1
    fi

    echo -e "\n${YELLOW}Syncing files...${NC}"
    rsync -e "$SSH_CMD" "${RSYNC_OPTS[@]}" "$LOCAL_DIR" "$TARGET:$REMOTE_DIR/"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Sync failed.${NC}"
        exit 1
    else
        echo -e "${GREEN}Sync completed successfully.${NC}"
    fi
fi

# 3. Reload Services
echo -e "\n${YELLOW}Post-Sync Actions (Run on VPS):${NC}"
echo "1. Reload Frontend (Rebuild container)"
echo "2. Reload WordPress (Restart LiteSpeed)"
echo "3. Clear Redis Cache"
echo "4. Exit"

read -p "Select an option (1-4): " ACTION

# Determine prefix based on mode
CMD_PREFIX=""
if [ "$START_ACTION" == "3" ]; then CMD_PREFIX="sudo"; fi

case $ACTION in
    1)
        echo -e "${YELLOW}Rebuilding Frontend container...${NC}"
        $SSH_CMD -t "$TARGET" "cd $REMOTE_DIR && $CMD_PREFIX docker compose -f docker-compose.vps.yml up --build -d frontend"
        ;;
    2)
        echo -e "${YELLOW}Restarting LiteSpeed (WordPress runs natively on the VPS)...${NC}"
        $SSH_CMD -t "$TARGET" "$CMD_PREFIX /usr/local/lsws/bin/lswsctrl restart"
        ;;
    3)
        echo -e "${YELLOW}Clearing Redis Cache...${NC}"
        $SSH_CMD -t "$TARGET" "cd $REMOTE_DIR && $CMD_PREFIX docker compose -f docker-compose.vps.yml exec redis redis-cli FLUSHALL"
        ;;
    *)
        echo "Exiting."
        ;;
esac

echo -e "${GREEN}Done!${NC}"
