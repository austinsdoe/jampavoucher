from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class StaffForm(FlaskForm):
    """Form for creating or editing Staff/Admin user accounts."""

    username = StringField(
        label="Username",
        validators=[
            DataRequired(message="Username is required."),
            Length(min=3, max=30, message="Username must be between 3 and 30 characters.")
        ],
        render_kw={"placeholder": "Enter username"}
    )

    password = PasswordField(
        label="Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=6, message="Password must be at least 6 characters.")
        ],
        render_kw={
            "placeholder": "Enter a secure password",
            "autocomplete": "new-password",
            "type": "password"
        }
    )

    role = SelectField(
        label="Role",
        choices=[
            ("admin", "Administrator"),
            ("staff", "Staff Member")
        ],
        validators=[DataRequired(message="Please select a role.")],
        render_kw={"class": "form-select"}
    )

    submit = SubmitField("Create Account")
