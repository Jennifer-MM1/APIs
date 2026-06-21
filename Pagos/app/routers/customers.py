from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.utils.exceptions import CustomerNotFoundException, ConflictException
from app.services.gateway_factory import get_gateway
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
):
    """Registra un nuevo cliente en el sistema de pagos.

    Opcionalmente lo registra también en las pasarelas configuradas.
    """
    # Verificar que no exista un cliente con ese email
    existing = db.query(Customer).filter(Customer.email == data.email).first()
    if existing:
        raise ConflictException(f"Ya existe un cliente con email: {data.email}")

    # Crear el cliente local
    customer = Customer(
        email=data.email,
        full_name=data.full_name,
        phone=data.phone,
    )

    # Registrar en cada gateway configurado
    available_gateways = settings.get_available_gateways()

    for gw_name in available_gateways:
        try:
            gw = get_gateway(gw_name)
            result = gw.create_customer(
                email=data.email,
                full_name=data.full_name,
                phone=data.phone,
            )
            if result.success and result.gateway_id:
                if gw_name == "stripe":
                    customer.stripe_customer_id = result.gateway_id
                elif gw_name == "paypal":
                    customer.paypal_customer_id = result.gateway_id
                elif gw_name == "mercadopago":
                    customer.mercadopago_customer_id = result.gateway_id
        except Exception:
            # Si falla el registro en una pasarela, continuamos con las demás
            pass

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/", response_model=list[CustomerResponse])
def list_customers(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Lista todos los clientes registrados."""
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    """Obtiene el detalle de un cliente por su ID."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise CustomerNotFoundException(customer_id)
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza los datos de un cliente."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise CustomerNotFoundException(customer_id)

    # Verificar email duplicado si se está cambiando
    if data.email and data.email != customer.email:
        existing = db.query(Customer).filter(Customer.email == data.email).first()
        if existing:
            raise ConflictException(f"Ya existe un cliente con email: {data.email}")

    # Actualizar campos proporcionados
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer
