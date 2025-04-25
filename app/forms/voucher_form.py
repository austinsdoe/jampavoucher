from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models.plan import Plan
from app.models.router import MikroTikRouter


# ─────────────────────────────────────────────
# 🎟️ Form: Create a Single Voucher
# ─────────────────────────────────────────────
class SingleVoucherForm(FlaskForm):
    """Form for creating a single voucher (offline or admin-created)."""

    code = StringField(
        label="Voucher Code (Optional)",
        validators=[
            Length(max=50, message="Code must be under 50 characters.")
        ],
        render_kw={"placeholder": "Auto-generate if left blank"}
    )

    router_id = SelectField(
        label="Router",
        coerce=int,
        validators=[DataRequired(message="Please select a router.")]
    )

    plan_id = SelectField(
        label="Plan",
        coerce=int,
        validators=[DataRequired(message="Please select a plan.")]
    )

    submit = SubmitField("🎟️ Create Voucher")

    def set_router_choices(self):
        """Populate router choices from DB."""
        routers = MikroTikRouter.query.order_by(MikroTikRouter.name).all()
        self.router_id.choices = [(r.id, r.name) for r in routers]

    def set_plan_choices(self):
        """Populate plan choices from DB."""
        plans = Plan.query.order_by(Plan.bandwidth_limit_mb).all()
        self.plan_id.choices = [(p.id, f"{p.name} ({p.bandwidth_limit_mb}MB / {p.duration_days}d)") for p in plans]


# ─────────────────────────────────────────────
# 📦 Form: Create a Batch of Vouchers
# ─────────────────────────────────────────────
class VoucherBatchForm(FlaskForm):
    """
    Admin form to create a batch of vouchers for a specific router.
    Supports both predefined plans and custom bandwidth/duration values.
    """

    router_id = SelectField(
        label="Router",
        coerce=int,
        validators=[DataRequired(message="Please select a router.")]
    )

    plan_id = SelectField(
        label="Plan",
        coerce=str,
        validators=[DataRequired(message="Please select a plan.")]
    )

    custom_bandwidth = IntegerField(
        label="Custom Bandwidth (MB)",
        validators=[
            Optional(),
            NumberRange(min=1, max=50000, message="Must be between 1 and 50000 MB.")
        ],
        render_kw={"placeholder": "e.g. 2000"}
    )

    custom_duration = IntegerField(
        label="Custom Duration (Days)",
        default=3,
        validators=[
            Optional(),
            NumberRange(min=1, max=365, message="Must be between 1 and 365 days.")
        ],
        render_kw={"placeholder": "e.g. 7"}
    )

    quantity = IntegerField(
        label="Quantity",
        default=500,
        validators=[
            DataRequired(message="Enter the number of vouchers."),
            NumberRange(min=1, max=1000, message="Choose between 1 and 1000.")
        ]
    )

    submit = SubmitField("📦 Generate Batch")

    def set_plan_choices(self):
        plans = Plan.query.order_by(Plan.bandwidth_limit_mb.asc()).all()
        self.plan_id.choices = [
            (str(plan.id), f"{plan.name} ({plan.bandwidth_limit_mb}MB / {plan.duration_days}d)") for plan in plans
        ]
        self.plan_id.choices.append(("custom", "➕ Custom Plan"))

    def set_router_choices(self):
        routers = MikroTikRouter.query.order_by(MikroTikRouter.name.asc()).all()
        self.router_id.choices = [(r.id, r.name) for r in routers]
