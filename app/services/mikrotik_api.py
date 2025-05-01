from routeros_api import RouterOsApiPool
from routeros_api.exceptions import RouterOsApiConnectionError
import socket
import traceback
from ipaddress import IPv4Network
import os

class MikroTikAPI:
    def __init__(self, ip, username, password, port=8728):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.api = None

    def ensure_connection(self):
        if not self.api:
            raise ValueError("❌ MikroTik API not connected. Please call connect() before using this method.")

    def handle_error(self, action, error):
        print(f"\n[❌] MikroTik API Error during '{action}' on {self.ip}: {error}")
        traceback.print_exc()

    def log_action(self, action, metadata=None):
        print(f"[AUDIT] {action} on {self.ip} | Data: {metadata or {}}")

    def ping(self, timeout=1):
        try:
            with socket.create_connection((self.ip, self.port), timeout=timeout):
                self.log_action("ping success")
                return True
        except Exception as e:
            self.handle_error("ping", e)
            self.log_action("ping failed")
            return False

    def connect(self, router_record=None):
        from app import db

        def save_mode(router, mode, version):
            if router:
                router.login_mode = mode
                router.routeros_version = version
                db.session.commit()

        try:
            api_pool = RouterOsApiPool(
                self.ip,
                username=self.username,
                password=self.password,
                port=self.port,
                use_ssl=False
            )
            self.api = api_pool.get_api()
            version = self.api.get_resource("/system/resource").get()[0].get("version", "unknown")
            save_mode(router_record, "secure", version)
            self.log_action("connect success (secure)", {"version": version})
            return self.api
        except Exception as e:
            if "invalid user name or password" in str(e).lower():
                print("[⚠️] Secure login failed — retrying with plaintext login (RouterOS v6 fallback)...")
                try:
                    api_pool = RouterOsApiPool(
                        self.ip,
                        username=self.username,
                        password=self.password,
                        port=self.port,
                        use_ssl=False,
                        plaintext_login=True
                    )
                    self.api = api_pool.get_api()
                    version = self.api.get_resource("/system/resource").get()[0].get("version", "unknown")
                    save_mode(router_record, "plaintext", version)
                    self.log_action("connect success (plaintext fallback)", {"version": version})
                    return self.api
                except Exception as e2:
                    self.handle_error("plaintext fallback", e2)
            else:
                self.handle_error("connect", e)
        return None

    @staticmethod
    def check_router_connection(ip, username, password, port=8728):
        try:
            api_pool = RouterOsApiPool(ip, username=username, password=password, port=port)
            api = api_pool.get_api()
            api_pool.disconnect()
            return True
        except Exception as e:
            if "invalid user name or password" in str(e).lower():
                try:
                    api_pool = RouterOsApiPool(ip, username=username, password=password, port=port, plaintext_login=True)
                    api = api_pool.get_api()
                    api_pool.disconnect()
                    return True
                except Exception as e2:
                    print(f"[❌] Fallback failed: {e2}")
                    traceback.print_exc()
                    return False
            print(f"[❌] Unexpected error checking connection to {ip}: {e}")
            traceback.print_exc()
            return False

    def assign_ip_to_interface(self, interface, address, netmask="255.255.255.0"):
        self.ensure_connection()
        try:
            network = IPv4Network(address, strict=False)
            cidr_address = f"{network.network_address}/{network.prefixlen}"
            ip_resource = self.api.get_resource("/ip/address")

            for entry in ip_resource.get():
                if entry.get("interface") == interface:
                    ip_resource.remove(id=entry.get(".id") or entry.get("id"))
                    self.log_action("remove_old_ip", {"interface": interface, "ip": entry.get("address")})

            ip_resource.add(address=cidr_address, interface=interface)
            self.log_action("assign_ip", {"interface": interface, "ip": cidr_address})
        except Exception as e:
            self.handle_error("assign_ip_to_interface", e)

    def add_static_binding(self, address, mac_address, interface, comment=None):
        self.ensure_connection()
        params = {
            "address": address,
            "mac-address": mac_address,
            "interface": interface
        }
        if comment:
            params["comment"] = comment
        return self.api.get_resource("/ip/arp").add(**params)

    def add_static_lease(self, mac_address, address, comment=None):
        self.ensure_connection()
        params = {
            "mac-address": mac_address,
            "address": address,
            "disabled": "no"
        }
        if comment:
            params["comment"] = comment
        return self.api.get_resource("/ip/dhcp-server/lease").add(**params)

    def create_simple_queue(self, name, target, max_limit="2M/2M"):
        self.ensure_connection()
        try:
            queue = self.api.get_resource("/queue/simple")
            queue.add(name=name, target=target, max_limit=max_limit)
            self.log_action("create_simple_queue", {"name": name, "limit": max_limit})
        except Exception as e:
            self.handle_error("create_simple_queue", e)

    def get_uptime(self):
        self.ensure_connection()
        try:
            resource = self.api.get_resource("/system/resource")
            uptime = resource.get()[0].get("uptime", "Unknown")
            self.log_action("get_uptime", {"uptime": uptime})
            return uptime
        except Exception as e:
            self.handle_error("get_uptime", e)
            return "N/A"

    def upload_vouchers(self, vouchers, server="guest-hotspot"):
        self.ensure_connection()
        try:
            user_res = self.api.get_resource("/ip/hotspot/user")
            for v in vouchers:
                if not user_res.get(name=str(v.code)):
                    params = {
                        "name": str(v.code),
                        "password": "",
                        "server": str(server),
                        "comment": f"Voucher for plan {v.plan.name if v.plan else 'N/A'}"
                    }
                    if v.plan and v.plan.mikrotik_profile:
                        params["profile"] = str(v.plan.mikrotik_profile)
                    if v.plan and v.plan.bandwidth_limit_mb:
                        params["limit-bytes-total"] = str(int(v.plan.bandwidth_limit_mb * 1024 * 1024))
                    if v.plan and v.plan.duration_days:
                        params["limit-uptime"] = f"{int(v.plan.duration_days)}d"
                    user_res.add(**params)
            self.log_action("upload_vouchers", {"count": len(vouchers)})
        except Exception as e:
            self.handle_error("upload_vouchers", e)

    def get_voucher_usage(self, mac_address):
        try:
            self.ensure_connection()
            hotspot_users = self.api.get_resource("/ip/hotspot/user").get()
            active_users = self.api.get_resource("/ip/hotspot/active").get()
            for user in active_users:
                if user.get("mac-address") == mac_address:
                    return {
                        "uptime": user.get("uptime"),
                        "bytes-in": int(user.get("bytes-in", 0)),
                        "bytes-out": int(user.get("bytes-out", 0)),
                        "total-bytes": int(user.get("bytes-in", 0)) + int(user.get("bytes-out", 0))
                    }
            for user in hotspot_users:
                if user.get("mac-address") == mac_address:
                    return {
                        "limit-bytes-total": int(user.get("limit-bytes-total", 0)),
                        "bytes-in": int(user.get("bytes-in", 0)),
                        "bytes-out": int(user.get("bytes-out", 0)),
                        "total-bytes": int(user.get("bytes-in", 0)) + int(user.get("bytes-out", 0))
                    }
            return None
        except Exception as e:
            self.handle_error("get_voucher_usage", e)
            return None

    def disconnect_user(self, username):
        try:
            self.ensure_connection()
            active_users = self.api.get_resource("/ip/hotspot/active")
            users = active_users.get()
            for user in users:
                if user.get("user") == username:
                    active_users.remove(id=user[".id"])
                    self.log_action("disconnect_user", {"username": username})
                    return True
            self.log_action("disconnect_user", {"username": username, "status": "not found"})
            return False
        except Exception as e:
            self.handle_error("disconnect_user", e)
            return False

    def activate_hotspot_user(self, username, mac=None, server="guest-hotspot", limit_bytes_total=None, limit_uptime=None):
        self.ensure_connection()
        try:
            user_resource = self.api.get_resource("/ip/hotspot/user")
            user_data = {
                "name": username,
                "password": username,
                "server": server,
                "profile": "default",
            }
            if limit_bytes_total:
                user_data["limit-bytes-total"] = str(limit_bytes_total)
            if limit_uptime:
                user_data["limit-uptime"] = limit_uptime
            if mac and isinstance(mac, str) and mac.lower() != "none" and mac.strip() != "":
                user_data["mac-address"] = mac

            user_resource.add(**user_data)
            print(f"[✅] Hotspot user created: {username}")
        except Exception as e:
            print(f"[❌] Failed to create hotspot user {username}: {e}")

    def enable_or_create_user(self, username, password=None, profile="default", server="guest-hotspot",
                              limit_bytes_total=None, limit_uptime=None, mac=None):
        self.ensure_connection()
        password = password or username
        user_resource = self.api.get_resource("/ip/hotspot/user")
        try:
            existing = user_resource.get(name=username)
            if existing:
                user_id = existing[0][".id"]
                user_resource.set(id=user_id, disabled="no")
                print(f"[✅] Re-enabled existing user: {username}")
                return
            user_data = {
                "name": username,
                "password": password,
                "server": server,
                "profile": profile,
                "disabled": "no"
            }
            if limit_bytes_total:
                user_data["limit-bytes-total"] = str(limit_bytes_total)
            if limit_uptime:
                user_data["limit-uptime"] = limit_uptime
            if mac and mac.strip().lower() != "none":
                user_data["mac-address"] = mac

            user_resource.add(**user_data)
            print(f"[✅] Created and enabled new user: {username}")
        except Exception as e:
            self.handle_error("enable_or_create_user", e)

    def force_active_login(self, username, ip_address, mac_address=None):
        self.ensure_connection()
        login_data = {
            "user": username,
            "address": ip_address,
        }
        if mac_address:
            login_data["mac-address"] = mac_address

        try:
            result = self.api.get_resource("/ip/hotspot/active/login").add(**login_data)
            self.log_action("force_active_login", {"user": username, "ip": ip_address, "mac": mac_address})
            return result
        except Exception as e:
            self.handle_error("force_active_login", e)
            return None
