import paramiko
import os
import sys

def load_env():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#") and "=" in line:
                    key, value = line.strip().split("=", 1)
                    os.environ[key.strip()] = value.strip()

def upload_and_run():
    load_env()
    hostname = os.getenv("SSH_HOST")
    username = os.getenv("SSH_USER")
    password = os.getenv("SSH_PASSWORD")
    
    if not hostname or not username or not password:
        print("Error: SSH credentials not found in .env file.")
        sys.exit(1)
        
    local_file = "data/definitions.json"
    remote_file = "/opt/minions/definitions.json"
    
    print("Connecting to ssh...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname, username=username, password=password, timeout=10)
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)
        
    print("Uploading definitions.json to remote server...")
    sftp = ssh.open_sftp()
    try:
        sftp.put(local_file, remote_file)
        print("Upload successful.")
    except Exception as e:
        print(f"Failed to upload: {e}")
    finally:
        sftp.close()
        
    print("Restarting minions service on remote server...")
    stdin, stdout, stderr = ssh.exec_command(f"echo '{password}' | sudo -S systemctl restart minions")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()
    print("Done.")

if __name__ == "__main__":
    upload_and_run()
