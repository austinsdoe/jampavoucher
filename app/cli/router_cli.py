import click
from flask.cli import with_appcontext
from app.models import MikroTikRouter
from app.services.mikrotik_api import MikroTikAPI

@click.command("sync-routers")
@with_appcontext
def sync_routers_command():
    """Sync MikroTik routers with their respective data."""
    routers = MikroTikRouter.query.all()
    for router in routers:
        try:
            # Initialize the MikroTik API with router details
            api = MikroTikAPI(router.ip_address, router.api_username, router.api_password, router.api_port)
            
            # Try to connect to the router and perform syncing operations
            if api.connect():
                print(f"[✅] Successfully synced router: {router.name}")
                # You can add additional router sync logic here as needed
            else:
                print(f"[❌] Failed to sync router: {router.name}")
        except Exception as e:
            print(f"[⚠️] Error syncing router {router.name}: {e}")
