import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.mikrotik_api import MikroTikAPI

def main():
    router_ip = input("Router IP: ")
    username = input("Username: ")
    password = input("Password: ")
    port = int(input("API Port [default 8728]: ") or "8728")

    # Connect to MikroTik
    api = MikroTikAPI(ip=router_ip, username=username, password=password, port=port)
    if not api.connect():
        return

    # Create IP Pool
    pool_name = "cli_pool"
    pool_range = "192.168.99.10-192.168.99.100"
    api.create_ip_pool(pool_name, pool_range)

    # Create Hotspot Profile
    profile_name = "cli_profile"
    hotspot_address = "192.168.99.1"
    dns_name = "cli.local"
    rate_limit = "1M/1M"
    api.create_hotspot_profile(profile_name, hotspot_address, dns_name, rate_limit)

    # Create Hotspot Server
    interface = "ether2"
    api.create_hotspot_server(interface, profile_name, pool_name)

    # Optionally create user profile
    api.create_user_profile(name="cli_user", shared_users=1, rate_limit="1M/1M")

    print("\n✅ All hotspot setup steps executed. Check your MikroTik.")

if __name__ == "__main__":
    main()
