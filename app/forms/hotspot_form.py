from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError, Optional
import ipaddress

class HotspotSetupForm(FlaskForm):
    router_id = SelectField("Router", coerce=int, validators=[DataRequired()])
    pool_name = StringField("IP Pool Name", validators=[DataRequired(), Length(max=64)])
    pool_range = StringField("IP Range (e.g., 192.168.88.10-192.168.88.254)", validators=[DataRequired()])
    interface = StringField("Interface Name", validators=[DataRequired()])
    profile_name = StringField("Hotspot Profile Name", validators=[DataRequired()])
    hotspot_address = StringField("Hotspot Address (e.g., 192.168.88.1)", validators=[DataRequired()])
    dns_name = StringField("DNS Name (e.g., hotspot.local)", validators=[DataRequired()])
    smtp_server = StringField("SMTP Server (Optional)", validators=[Optional(), Length(max=128)])
    html_directory = StringField("HTML Directory (e.g., hotspot)", validators=[Optional(), Length(max=128)])
    rate_limit = StringField("Rate Limit (e.g., 2M/2M)", validators=[Optional(), Length(max=64)])
    submit = SubmitField("Setup Hotspot")

    def validate_pool_range(self, field):
        value = field.data.strip()
        if '-' not in value:
            raise ValidationError("Range must be in the format: startIP-endIP")

        try:
            start_ip, end_ip = value.split('-')
            ip_start = ipaddress.IPv4Address(start_ip.strip())
            ip_end = ipaddress.IPv4Address(end_ip.strip())

            if ip_start >= ip_end:
                raise ValidationError("Start IP must be less than End IP.")
        except Exception as e:
            raise ValidationError(f"Invalid IP range: {e}")

    def validate_hotspot_address(self, field):
        try:
            ipaddress.IPv4Address(field.data.strip())
        except Exception:
            raise ValidationError("Invalid IP address format.")
