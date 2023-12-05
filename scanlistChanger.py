import paramiko
import threading

# Login credentials
botUsername = ''
botPassword = ''
defaultUsername = ''
defaultPassword = ''
# Script parameters
accessPointIP = '10.1.25.26'
scanList = "default"


# Read credentials from file
def read_credentials():
    global botUsername, botPassword, defaultUsername, defaultPassword
    with open('.venv/credentials.txt', 'r') as f:
        botUsername = f.readline().strip()
        botPassword = f.readline().strip()
        defaultUsername = f.readline().strip()
        defaultPassword = f.readline().strip()


def get_wireless_clients(accessPointIP):
    # Start the ssh client that connects to the access point
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Try different credentials
    try:
        ssh.connect(accessPointIP, username='dlbot', password='0Fb4EEewAxbQWm7i', port=22)
    except paramiko.ssh_exception.AuthenticationException:
        ssh.connect(accessPointIP, username='admin', password='Bemow456', port=22)
    except:
        print('Could not connect to access point: ' + accessPointIP)
        ssh.close()
        exit()

    # Get the list of wireless clients
    stdin, stdout, stderr = ssh.exec_command('foreach x in=[/interface/wireless/registration-table/find] do={:put [/interface/wireless/registration-table/get $x mac-address]}')
    registration = set([o.strip() for o in stdout.readlines()])
    # Get the list of neighbors as ip, mac pairs
    stdin, stdout, stderr = ssh.exec_command('foreach x in=[/ip/neighbor/find where interface~"wlan1"] do={:put ([/ip/neighbor/get $x address], [/ip/neighbor/get $x mac-address])}')
    neigbors = [o.strip().split(';') for o in stdout.readlines()]
    ssh.close()
    # Get the list of wireless clients' ip addresses which are both in the registration table and in the list of neighbors
    wirelessClients = [n[0] for n in neigbors if n[1] in registration]
    print('Wireless clients:\n' + '\n'.join(wirelessClients))
    print('----------------------------------------')
    return wirelessClients


def change_scanlist(ip, scanList):
    # Start the ssh client that connects to the specified host
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Try different credentials
    try:
        ssh.connect(ip, username='dlbot', password='0Fb4EEewAxbQWm7i', port=22, timeout=10)
    except paramiko.ssh_exception.AuthenticationException:
        ssh.connect(ip, username='admin', password='Bemow456', port=22, timeout=10)
    except:
        print('Could not connect to ' + ip)
        ssh.close()
        return
    # Change the scan-list of the wireless interface
    ssh.exec_command(f'/interface/wireless/set wlan1 scan-list={scanList}')
    ssh.close()
    print('Changed scan-list of ' + ip + ' to ' + scanList)


# Read credentials from file
read_credentials()

# Get list of wireless clients
wirelessClients = get_wireless_clients(accessPointIP)

# Change scan-list of each wireless client in parallel
threads = []
for ip in wirelessClients:
    thread = threading.Thread(target=change_scanlist, args=(ip,scanList))
    thread.start()
    threads.append(thread)

# Wait for all threads to finish
for thread in threads:
    thread.join(1)