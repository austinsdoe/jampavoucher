from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.forms.plan_form import PlanForm
from app.models import db, Plan, MikroTikRouter
from app.decorators import role_required
from app.services.mikrotik_api import MikroTikAPI
from app.utils.security import decrypt  # ✅ required for _api_password

plan_bp = Blueprint("plans", __name__, url_prefix="/admin")


@plan_bp.route("/plans")
@login_required
@role_required("admin", "staff")
def list_plans():
    plans = Plan.query.order_by(Plan.created_at.desc()).all()
    return render_template("admin/plan_list.html", plans=plans)


@plan_bp.route("/plans/create", methods=["GET", "POST"])
@login_required
@role_required("admin", "staff")
def create_plan():
    form = PlanForm()
    if form.validate_on_submit():
        new_plan = Plan(
            name=form.name.data,
            bandwidth_limit_mb=form.bandwidth_limit_mb.data,
            duration_days=form.duration_days.data,
            price=form.price.data,
            description=form.description.data,
            rate_limit=form.rate_limit.data
        )
        db.session.add(new_plan)
        db.session.commit()

        _sync_plan_to_routers(new_plan)

        flash("✅ Plan created and profile synced!", "success")
        return redirect(url_for("admin.plans.list_plans"))
    return render_template("admin/create_plan.html", form=form)


@plan_bp.route("/plans/edit/<int:plan_id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "staff")
def edit_plan(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    form = PlanForm(obj=plan)
    if form.validate_on_submit():
        form.populate_obj(plan)
        db.session.commit()

        _sync_plan_to_routers(plan)

        flash("✅ Plan updated and profile synced!", "success")
        return redirect(url_for("admin.plans.list_plans"))
    return render_template("admin/edit_plan.html", form=form, plan=plan)


@plan_bp.route("/plans/delete/<int:plan_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_plan(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    db.session.delete(plan)
    db.session.commit()
    flash("🗑️ Plan deleted successfully.", "info")
    return redirect(url_for("admin.plans.list_plans"))


# 🔁 Sync plan to MikroTik routers
def _sync_plan_to_routers(plan):
    routers = MikroTikRouter.query.all()
    for router in routers:
        try:
            api = MikroTikAPI(
                ip=router.ip_address,
                username=router.api_username,
                password=decrypt(router._api_password),
                port=router.api_port
            )
            if api.connect(router):
                api.create_user_profile(name=plan.name, rate_limit=plan.rate_limit)
                print(f"[✅] Synced plan '{plan.name}' to {router.name}")
            else:
                print(f"[❌] Could not connect to {router.name}")
        except Exception as e:
            print(f"[⚠️] Failed to sync to {router.name}: {e}")
