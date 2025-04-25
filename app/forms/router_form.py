from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField
from wtforms.validators import DataRequired, IPAddress, Optional, Length, NumberRange

class RouterForm(FlaskForm):
    """
    Form for adding or editing MikroTik routers.
    """

    name = StringField(
        label="Router Name",
        validators=[
            DataRequired(message="Router name is required."),
            Length(min=2, max=50, message="Name must be between 2 and 50 characters.")
        ],
        render_kw={"placeholder": "e.g. Main Gateway"}
    )

    ip_address = StringField(
        label="IP Address",
        validators=[
            DataRequired(message="IP address is required."),
            IPAddress(message="Enter a valid IP address.")
        ],
        render_kw={"placeholder": "e.g. 192.168.88.1"}
    )

    api_port = IntegerField(
        label="API Port",
        validators=[
            DataRequired(message="API port is required."),
            NumberRange(min=1, max=65535, message="Enter a valid port number.")
        ],
        render_kw={"placeholder": "e.g. 8728"}
    )

    api_username = StringField(
        label="API Username",
        validators=[
            DataRequired(message="API username is required."),
            Length(min=3, max=50, message="Username must be between 3 and 50 characters.")
        ],
        render_kw={"placeholder": "e.g. admin"}
    )

    api_password = PasswordField(
        label="API Password",
        validators=[
            DataRequired(message="API password is required."),
            Length(min=3, max=50, message="Password must be between 3 and 50 characters.")
        ],
        render_kw={
            "placeholder": "••••••••",
            "type": "password",
            "autocomplete": "new-password"
        }
    )

    interface = StringField(
        label="Default Interface",
        validators=[Optional()],
        render_kw={"placeholder": "e.g. ether1"}
    )

    location = StringField(
        label="Location (Optional)",
        validators=[Optional()],
        render_kw={"placeholder": "e.g. Monrovia HQ"}
    )

    submit = SubmitField("💾 Save Router")
