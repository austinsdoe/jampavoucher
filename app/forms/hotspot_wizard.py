from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired

class SelectRouterForm(FlaskForm):
    router_id = SelectField("Select Router", coerce=int, validators=[DataRequired()])

class AddressPoolForm(FlaskForm):
    pool_name = StringField("Pool Name", validators=[DataRequired()])
    pool_range = StringField("IP Range (e.g. 192.168.10.100-192.168.10.200)", validators=[DataRequired()])

class AssignIPForm(FlaskForm):
    interface = StringField("Interface Name (e.g. ether1)", validators=[DataRequired()])
    hotspot_ip = StringField("Hotspot IP (CIDR format e.g. 192.168.10.1/24)", validators=[DataRequired()])

class ServerProfileForm(FlaskForm):
    profile_name = StringField("Server Profile Name", validators=[DataRequired()])
    dns_name = StringField("DNS Name (e.g. wifi.cafe.local)", validators=[DataRequired()])
    rate_limit = StringField("Rate Limit (e.g. 1M/3M)", default="")

class HotspotServerForm(FlaskForm):
    # No new inputs, values carried from previous steps
    pass

class UserProfileForm(FlaskForm):
    user_profile_name = StringField("User Profile Name", validators=[DataRequired()])
    shared_users = IntegerField("Number of Devices (shared-users)", default=1)
    user_rate_limit = StringField("Rate Limit (e.g. 1M/3M)", validators=[DataRequired()])

class VoucherUploadForm(FlaskForm):
    upload_all = BooleanField("Upload All Single Vouchers")
    batch_id = SelectField("Select Batch", coerce=int, choices=[])
