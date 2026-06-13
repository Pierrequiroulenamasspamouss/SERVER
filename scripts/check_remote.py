import paramiko
import sys

def check_remote_path():
    hostname = "192.168.1.5"
    username = "pierre"
    password = "hacking4fun"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname, username=username, password=password, timeout=10)
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)
        
    stdin, stdout, stderr = ssh.exec_command("ls -la /opt/minions; ls -la /opt/minions/data")
    print("STDOUT:")
    print(stdout.read().decode())
    print("STDERR:")
    print(stderr.read().decode())
    ssh.close()

if __name__ == "__main__":
    check_remote_path()
