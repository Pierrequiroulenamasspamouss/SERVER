#!/usr/bin/env python3
"""
Connects to the Pi via SSH and:
1. Clears any stored git credentials for root that block public repo cloning
2. Rewrites ~/update-latest.sh with a working git clone (no auth env vars, clean credential helper)
"""
import os, sys, paramiko
from pathlib import Path

# ── credentials ───────────────────────────────────────────────────────────────
env_path = Path(__file__).parent.parent / ".env"
creds = {}
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()

HOST = creds.get("SSH_HOST", "192.168.1.5")
USER = creds.get("SSH_USER", "pierre")
PASS = creds.get("SSH_PASSWORD", "hacking4fun")

# ── new update-latest.sh content ──────────────────────────────────────────────
SCRIPT = r"""#!/bin/bash
set -e

########################################
# CONFIGURATION
########################################
GITHUB_USER="Pierrequiroulenamasspamouss"
REPO_NAME="Unity"
BRANCH="master"
SERVER_DIR="SERVER"
TARGET_DIR="/opt/minions"
SERVICE_NAME="minions"
FALLBACK_USER="pierre"

REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

########################################
# PRECHECKS
########################################
command -v git >/dev/null 2>&1 || {
  echo "Installing git..."
  sudo apt-get update -y && sudo apt-get install -y git
}

command -v rsync >/dev/null 2>&1 || {
  echo "Installing rsync..."
  sudo apt-get update -y && sudo apt-get install -y rsync
}

########################################
# DETECT SERVICE USER
########################################
SERVICE_USER=$(systemctl show "$SERVICE_NAME" --property=User --value 2>/dev/null)

if [ -z "$SERVICE_USER" ]; then
  SERVICE_USER="$FALLBACK_USER"
fi

echo "Using service user: $SERVICE_USER"

########################################
# CREATE STAGING
########################################
STAGING_DIR=$(mktemp -d)
echo "Using staging directory: $STAGING_DIR"

cleanup() {
  rm -rf "$STAGING_DIR"
}
trap cleanup EXIT

########################################
# STOP SERVICE
########################################
echo "Stopping service..."
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true

########################################
# CLONE REPO (public — no credentials needed)
########################################
echo "Cloning repository..."
# Wipe any cached GitHub credentials for the root user so git doesn't
# try to authenticate against a public repo and fail.
printf "protocol=https\nhost=github.com\n" | git credential reject 2>/dev/null || true

git \
  -c credential.helper="" \
  -c http.extraHeader="" \
  clone \
  --branch "$BRANCH" --single-branch --depth 1 \
  "$REPO_URL" "$STAGING_DIR/repo"

if [ ! -d "$STAGING_DIR/repo/$SERVER_DIR" ]; then
  echo "Error: $SERVER_DIR directory not found in repo!"
  exit 1
fi

########################################
# BACKUP IMPORTANT DATA
########################################
echo "Backing up persistent data..."
mkdir -p "$STAGING_DIR/backup"

cp -f "$TARGET_DIR"/*.sqlite "$STAGING_DIR/backup/" 2>/dev/null || true
cp -f "$TARGET_DIR"/*.env    "$STAGING_DIR/backup/" 2>/dev/null || true
cp -r "$TARGET_DIR/player_data" "$STAGING_DIR/backup/" 2>/dev/null || true

########################################
# UPDATE FILES
########################################
echo "Updating files..."

rsync -av --delete \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='*.sqlite' \
  --exclude='*.env' \
  --exclude='player_data' \
  "$STAGING_DIR/repo/$SERVER_DIR/" "$TARGET_DIR/"

########################################
# RESTORE BACKUPS
########################################
echo "Restoring persistent data..."

cp -f "$STAGING_DIR/backup"/*.sqlite "$TARGET_DIR/" 2>/dev/null || true
cp -f "$STAGING_DIR/backup"/*.env    "$TARGET_DIR/" 2>/dev/null || true

if [ -d "$STAGING_DIR/backup/player_data" ]; then
  rm -rf "$TARGET_DIR/player_data"
  cp -r "$STAGING_DIR/backup/player_data" "$TARGET_DIR/"
fi

########################################
# PERMISSIONS
########################################
echo "Setting permissions..."

chown -R "$SERVICE_USER:$SERVICE_USER" "$TARGET_DIR"
find "$TARGET_DIR" -type d -exec chmod 775 {} \;
find "$TARGET_DIR" -type f -exec chmod 664 {} \;
find "$TARGET_DIR" -name "*.sqlite" -exec chmod 664 {} \;

########################################
# START SERVICE
########################################
echo "Starting service..."
sudo systemctl start "$SERVICE_NAME" 2>/dev/null || sudo service "$SERVICE_NAME" start

########################################
# DONE
########################################
echo "✅ Update completed successfully"
"""

def run(client, cmd, sudo_pass=None):
    if sudo_pass:
        cmd = f"echo '{sudo_pass}' | sudo -S bash -c {repr(cmd)}"
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(out, end="")
    if err: print("[stderr]", err, end="")
    return stdout.channel.recv_exit_status()

def main():
    print(f"Connecting to {USER}@{HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    print("Connected.")

    # 1. Write the new script via /tmp then sudo move into place
    print("Writing new update-latest.sh ...")
    sftp = client.open_sftp()
    with sftp.open("/tmp/update-latest.sh", "w") as f:
        f.write(SCRIPT)
    sftp.close()

    run(client, f"echo '{PASS}' | sudo -S mv /tmp/update-latest.sh /home/pierre/update-latest.sh && sudo chmod +x /home/pierre/update-latest.sh && sudo chown pierre:pierre /home/pierre/update-latest.sh")

    # 3. Clear root's git credential store (the real culprit)
    print("Clearing root git credential store...")
    run(client,
        "sudo bash -c 'printf \"protocol=https\\nhost=github.com\\n\" | git credential reject 2>/dev/null; "
        "rm -f /root/.git-credentials; "
        "git config --global --unset credential.helper 2>/dev/null || true'",
        sudo_pass=PASS)

    # 4. Quick sanity test: clone the repo as root with the new invocation
    print("\nRunning quick clone test as root...")
    rc = run(client,
        "sudo bash -c '"
        "git -c credential.helper=\"\" -c http.extraHeader=\"\" "
        "clone --depth 1 --single-branch --branch master "
        "https://github.com/Pierrequiroulenamasspamouss/Unity.git "
        "/tmp/clone_test && echo OK && rm -rf /tmp/clone_test"
        "'",
        sudo_pass=PASS)
    if rc == 0:
        print("\n✅ Clone works! update-latest.sh is ready to run.")
    else:
        print("\n❌ Clone still failing — check output above.")

    client.close()

if __name__ == "__main__":
    main()
