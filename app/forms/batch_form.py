# app/forms/batch_form.py

from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional
from app.models.plan import Plan
from app.models.router import MikroTikRouter  # Rename to Router if using Router elsewhere


class VoucherBatchForm(FlaskForm):
    """
    Admin/Staff form to generate a batch of vouchers for a selected router and plan.
    Supports both predefined and custom plans.
    """

    # Constants
    MAX_MB = 50000
    MAX_DAYS = 365
    MAX_PRICE = 999
    MAX_QUANTITY = 1000

    # ────── Router Selection ──────
    router_id = SelectField(
        "Router",
        coerce=int,
        validators=[DataRequired(message="Please select a router.")]
    )

    # ────── Plan Selection ──────
    plan_id = SelectField(
        "Plan",
        coerce=str,
        validators=[DataRequired(message="Please select a plan.")]
    )

    # ────── Custom Plan Inputs ──────
    custom_bandwidth = IntegerField(
        "Custom Bandwidth (MB)",
        validators=[Optional(), NumberRange(min=1, max=MAX_MB)],
        render_kw={"placeholder": f"1 - {MAX_MB} MB"}
    )

    custom_duration = IntegerField(
        "Custom Duration (Days)",
        validators=[Optional(), NumberRange(min=1, max=MAX_DAYS)],
        render_kw={"placeholder": f"1 - {MAX_DAYS} days"}
    )

    custom_price = DecimalField(
        "Custom Price ($)",
        validators=[Optional(), NumberRange(min=0, max=MAX_PRICE)],
        render_kw={"placeholder": f"0.00 - {MAX_PRICE:.2f}"}
    )

    # ────── Quantity ──────
    quantity = IntegerField(
        "Quantity",
        default=500,
        validators=[
            DataRequired(message="Please enter quantity."),
            NumberRange(min=1, max=MAX_QUANTITY, message=f"Must be between 1 and {MAX_QUANTITY}")
        ]
    )

    # ────── Submit Button ──────
    submit = SubmitField("📦 Create Batch")

    # ────── Helper Methods ──────
    def set_plan_choices(self):
        """
        Populate the plan dropdown from database and add a custom plan option.
        """
        plans = Plan.query.order_by(Plan.bandwidth_limit_mb.asc()).all()
        self.plan_id.choices = [
            (str(plan.id), f"{plan.name} ({plan.bandwidth_limit_mb}MB / {plan.duration_days}d)")
            for plan in plans
        ]
        self.plan_id.choices.append(("custom", "➕ Custom Plan"))

    def set_router_choices(self):
        """
        Populate the router dropdown from available MikroTik routers.
        """
        routers = MikroTikRouter.query.order_by(MikroTikRouter.name.asc()).all()
        self.router_id.choices = [(router.id, router.name) for router in routers]
