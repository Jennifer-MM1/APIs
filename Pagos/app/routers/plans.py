from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies import get_db, require_admin
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from app.utils.exceptions import PlanNotFoundException
from app.services.gateway_factory import get_gateway
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
):
    """Crea un nuevo plan de suscripción.

    Automáticamente lo sincroniza con las pasarelas configuradas.
    """
    plan = Plan(
        name=data.name,
        description=data.description,
        amount=data.amount,
        currency=data.currency.value,
        interval=data.interval.value,
        interval_count=data.interval_count,
    )

    # Sincronizar con cada gateway configurado
    available_gateways = settings.get_available_gateways()

    for gw_name in available_gateways:
        try:
            gw = get_gateway(gw_name)
            result = gw.create_plan(
                name=data.name,
                amount=data.amount,
                currency=data.currency.value,
                interval=data.interval.value,
                interval_count=data.interval_count,
            )
            if result.success and result.gateway_id:
                if gw_name == "stripe":
                    plan.stripe_price_id = result.gateway_id
                elif gw_name == "paypal":
                    plan.paypal_plan_id = result.gateway_id
                elif gw_name == "mercadopago":
                    plan.mercadopago_plan_id = result.gateway_id
        except Exception:
            pass  # Si falla una pasarela, continuamos

    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/", response_model=list[PlanResponse])
def list_plans(
    active_only: bool = True,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Lista los planes de suscripción disponibles."""
    query = db.query(Plan)
    if active_only:
        query = query.filter(Plan.is_active == True)
    plans = query.offset(skip).limit(limit).all()
    return plans


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    """Obtiene el detalle de un plan por su ID."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise PlanNotFoundException(plan_id)
    return plan


@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    data: PlanUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza un plan de suscripción (solo datos locales)."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise PlanNotFoundException(plan_id)

    update_data = data.model_dump(exclude_unset=True)

    # Convertir enums a strings si están presentes
    if "currency" in update_data and update_data["currency"]:
        update_data["currency"] = update_data["currency"].value
    if "interval" in update_data and update_data["interval"]:
        update_data["interval"] = update_data["interval"].value

    for field, value in update_data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{plan_id}", response_model=PlanResponse)
def deactivate_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    """Desactiva un plan (soft delete). Las suscripciones existentes no se afectan."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise PlanNotFoundException(plan_id)

    plan.is_active = False
    db.commit()
    db.refresh(plan)
    return plan
