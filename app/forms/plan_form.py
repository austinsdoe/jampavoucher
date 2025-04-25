from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class PlanForm(FlaskForm):
    name = StringField("Plan Name", validators=[DataRequired()])
    bandwidth_limit_mb = IntegerField("Bandwidth Limit (MB)", validators=[DataRequired()])
    duration_days = IntegerField("Duration (Days)", validators=[DataRequired()])
    price = FloatField("Price (LRD)", validators=[DataRequired()])
    rate_limit = StringField("Rate Limit (e.g. 1M/1M)")  # ✅ Added
    description = TextAreaField("Description")
    submit = SubmitField("Save Plan")
