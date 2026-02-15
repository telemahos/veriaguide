# Deployment Guide

This project uses a custom script to synchronize local development changes to the production VPS.

## Prerequisites

*   SSH Access to the VPS (`kostass@veriaguide.gr`).
*   SSH Key configured (or password access).

## Sync Script: `sync_to_vps.sh`

The script is located in the root directory: `./sync_to_vps.sh`

### Usage

Run the script from the project root:

```bash
./sync_to_vps.sh
```

or with arguments:

```bash
./sync_to_vps.sh [USER] [HOST] [PORT]
# Example:
./sync_to_vps.sh kostass veriaguide.gr 2013
```

### Sync Modes

The script offers different modes to handle permissions:

1.  **Sync Files (Standard)**: Attempts a direct `rsync`. Use this only if your SSH user owns the destination files.
2.  **Check Permissions**: Lists file ownership on the server for troubleshooting.
3.  **Sync via Sudo Staging (Recommended)**:
    *   Uploads files to a temporary folder (`~/veriaguide_sync_tmp`).
    *   Uses `sudo` to move them to the final destination (`/home/veriaguide.gr/public_html`).
    *   **Use this mode** if you encounter "Permission denied" errors.

### Post-Sync Actions

After file transfer, the script allows you to reload services on the VPS:

*   **Reload Frontend**: Rebuilds the Python/Next.js container (Required for code changes).
*   **Reload WordPress**: Restarts the WP container.
*   **Clear Redis Cache**: Flushes the Redis cache.

## Configuration

*   **Excluded Files**: See `rsync_exclude.txt` for a list of files that are NOT synced (e.g., `.git`, `node_modules`, `mysql-data`).
