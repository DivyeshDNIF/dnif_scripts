import subprocess
import re

# ANSI escape codes for colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Function to run a command and return the output
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"{RED}Error running command '{command}': {e.stderr}{RESET}"

# Function to parse the output of ifconfig to extract device names and IP addresses
def parse_ifconfig(output):
    interfaces = []
    pattern = re.compile(r'(\S+): flags.*\n.*inet (\d+\.\d+\.\d+\.\d+)', re.MULTILINE)

    for match in pattern.findall(output):
        interface_name, ip_address = match
        interfaces.append(f"Device: {interface_name}, IP: {ip_address}")
    
    return interfaces

# Function to calculate total storage from df -h output
def calculate_total_storage(output):
    total_size = 0.0
    for line in output.splitlines()[1:]:
        try:
            size = line.split()[1]
            if 'G' in size:
                total_size += float(size.strip('G'))
            elif 'T' in size:
                total_size += float(size.strip('T')) * 1024  # Convert TB to GB
            elif 'M' in size:
                total_size += float(size.strip('M')) / 1024  # Convert MB to GB
        except (IndexError, ValueError):
            continue
    return total_size

# Function to get root directory storage from df -h output
def get_root_storage(output):
    for line in output.splitlines():
        if line.endswith(" /"):
            return line
    return "Root directory not found."

# Function to check telnet connection status
def check_telnet_connection(host, port, server_type):
    command = f"echo '' | telnet {host} {port}"
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
        if "Connected" in result.stdout or "Escape character" in result.stdout:
            return f"{GREEN}Connected to {server_type} ({host}:{port}){RESET}"
        else:
            return f"{RED}Connection to {server_type} ({host}:{port}) failed{RESET}"
    except subprocess.CalledProcessError:
        return f"{RED}Connection to {server_type} ({host}:{port}) failed{RESET}"
    except subprocess.TimeoutExpired:
        return f"{RED}Connection to {server_type} ({host}:{port}) timed out{RESET}"

# Function to get total memory size from free -h output
def get_total_memory(output):
    for line in output.splitlines():
        if "Mem:" in line:
            return line.split()[1]
    return "Memory information not found."

# Function to get unique rota values from lsblk output
def get_unique_rota_values(output):
    rota_values = set()
    for line in output.splitlines()[1:]:
        parts = line.split()
        if parts:
            rota_values.add(parts[1])
    return rota_values

# Function to run wget and check success or failure
def run_wget(link):
    try:
        result = subprocess.run(f"wget -q --spider {link}", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return f"{GREEN}Successfully reached: {link}{RESET}"
    except subprocess.CalledProcessError as e:
        return f"{RED}Failed to reach: {link}. Error: {e.stderr}{RESET}"

# Function to check and install 'policycoreutils' if sestatus is missing
def check_and_install_policycoreutils():
    result = subprocess.run("which sestatus", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        print(f"{RED}sestatus command not found. Installing policycoreutils...{RESET}")
        install_output = run_command("sudo apt install policycoreutils -y")
        print(install_output)
        return run_command("sestatus")
    else:
        return run_command("sestatus")

# Function to check status output and color it based on active or inactive/failed/disabled status
def check_status(output):
    if any(state in output for state in ["inactive", "failed", "disabled"]):
        return f"{RED}{output}{RESET}"
    else:
        return f"{GREEN}{output}{RESET}"

# Ask for Core, AD, and DN IPs
core_ip = input("Please enter the Core IP: ")
ad_ip = input("Please enter the AD IP: ")
dn_ip = input("Please enter the DN IP: ")

# List of commands to run (excluding ifconfig and df -h, which are handled separately)
commands = [
    "hostname",
    "nproc",
    "timedatectl",
    "hostnamectl || cat /etc/os-release",
    "umask",
    "python3 --version",
    "env | grep -i proxy || cat /etc/environment"
]

# List of links to download
links = [
    "http://www.docker.com",
    "https://www.docker.io",
    "http://download.docker.com",
    "https://raw.githubusercontent.com",
    "https://www.github.com",
    "https://registry-1.docker.io",
    "http://archive.ubuntu.com"
]

# 1. Special handling for ifconfig to show only device name and IP address
print(f"{YELLOW}Running command: ifconfig{RESET}")
ifconfig_output = run_command("ifconfig")
parsed_ifconfig = parse_ifconfig(ifconfig_output)

print("Network Interfaces and IP Addresses:")
for interface in parsed_ifconfig:
    print(interface)
print("-" * 50)

# 2. First df -h command: Total storage
print(f"{YELLOW}Running command: df -h (Total Storage){RESET}")
df_output = run_command("df -h")
total_storage = calculate_total_storage(df_output)
print(f"Total Storage: {total_storage:.2f} GB")
print("-" * 50)

# 3. Second df -h command: Root directory storage
print(f"{YELLOW}Running command: df -h (Root Directory){RESET}")
root_storage = get_root_storage(df_output)
print("Root Directory Storage:\n", root_storage)
print("-" * 50)

# 4. Get total memory size
print(f"{YELLOW}Running command: free -h (Total Memory){RESET}")
free_output = run_command("free -h")
total_memory = get_total_memory(free_output)
print(f"Total Memory: {total_memory}")
print("-" * 50)

# 5. Get unique rota values from lsblk
print(f"{YELLOW}Running command: lsblk -d -o name,rota{RESET}")
lsblk_output = run_command("lsblk -d -o name,rota")
unique_rota_values = get_unique_rota_values(lsblk_output)
print("Unique Rota Values (1 = HDD, 0 = SSD):")
for rota in unique_rota_values:
    print(f"{rota}")
print("-" * 50)

# 6. Running other commands
for cmd in commands:
    print(f"{YELLOW}Running command: {cmd}{RESET}")
    output = run_command(cmd)
    print(output)
    print("-" * 50)

# 7. Print ufw status and highlight active/inactive
print(f"{YELLOW}Running command: ufw status{RESET}")
ufw_output = run_command("ufw status")
colored_ufw_output = check_status(ufw_output)
print(colored_ufw_output)
print("-" * 50)

# 8. Print sestatus and highlight active/inactive
print(f"{YELLOW}Running command: sestatus{RESET}")
sestatus_output = check_and_install_policycoreutils()
colored_sestatus_output = check_status(sestatus_output)
print(colored_sestatus_output)
print("-" * 50)

# 9. Check wget for each link
for link in links:
    print(f"{YELLOW}Running command: wget {link}{RESET}")
    print(run_wget(link))
    print("-" * 50)

# 10. Check telnet connection for Core, AD, and DN with specific server type labels
telnet_ports = [1443, 8086, 7426, 8765]
for ip, server_type in [(core_ip, "Core"), (ad_ip, "AD"), (dn_ip, "DN")]:
    for port in telnet_ports:
        print(f"{YELLOW}Running command: telnet for {server_type} {ip} {port}{RESET}")
        print(check_telnet_connection(ip, port, server_type))
        print("-" * 50)

