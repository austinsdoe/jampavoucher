from app.extensions import db

from .user import User
from .router import MikroTikRouter  # Corrected class name
from .voucher import Voucher
from .voucher_batch import VoucherBatch
from .user_usage import UserUsage
from .payment import Payment
from .plan import Plan  # ✅ Ensure Plan is included
from .ip_change_log import IPChangeLog

__all__ = [
    'db',
    'User',
    'MikroTikRouter',
    'Voucher',
    'VoucherBatch',
    'UserUsage',
    'Payment',  # ✅ Fixed comma
    'Plan',
    'IPChangeLog',  # ✅ Fixed comma
]
