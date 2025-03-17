import subprocess
import re
from pyvis.network import Network

def get_network_devices():
    result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
    devices = []
    arp_output = result.stdout

    pattern = re.compile(r'\? \((\d+\.\d+\.\d+\.\d+)\) at ((?:[\da-f]{1,2}:){5}[\da-f]{1,2}|incomplete)', re.IGNORECASE)
    for line in arp_output.splitlines():
        match = pattern.search(line)
        if match:
            ip, mac = match.groups()
            devices.append({"ip": ip, "mac": mac if mac != 'incomplete' else 'N/A'})
    return devices, arp_output

def create_network_map(devices, arp_output):
    net = Network(height='600px', width='100%', bgcolor='#222222', font_color='white')

    net.add_node('Router', label='Router', color='red')

    for device in devices:
        label = f"IP: {device['ip']}\nMAC: {device['mac']}"
        net.add_node(device['ip'], label=label, color='blue')
        net.add_edge('Router', device['ip'])

    net.save_graph('network_map.html')

    with open('network_map.html', 'r+') as f:
        content = f.read()
        f.seek(0)
        f.write(f"""
        <div style='height:500px; width:40%; background-color:#222222;'>
            {content}
        </div>
        """)
        f.truncate()#белый блок главный по ширине

if __name__ == "__main__":
    devices, arp_output = get_network_devices()
    if devices:
        create_network_map(devices, arp_output)
        print("Карта успешно создана: network_map.html")
    else:
        print("Устройства в сети не найдены.")
