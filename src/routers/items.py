"""Item CRUD routes."""

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core import get_current_user
from core.middleware import limiter
from database import get_db
from exceptions.exceptions import NotFoundException
from models import Item, User
from schemas import ItemCreate, ItemResponse, ItemUpdate
from tasks import log_user_action, process_item_completion, send_item_notification

router = APIRouter(prefix="/items", tags=["Items"])


async def get_item_for_user(
    item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Item:
    """Get an item by ID for the current user, or raise 404."""
    stmt = select(Item).where(Item.id == item_id, Item.owner_id == user.id)
    item = db.scalars(stmt).first()
    if not item:
        raise NotFoundException(detail="Item not found")
    return item


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("50/minute")
async def create_item(
    request: Request,
    item: ItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Item:
    """
    Create a new item

    - **title**: Item title
    - **description**: Optional item description

    Background tasks:
    - Send notification
    - Log action
    """
    db_item = Item(title=item.title, description=item.description, owner_id=user.id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Add background tasks
    background_tasks.add_task(
        send_item_notification, user.email, user.username, item.title, "created"
    )
    background_tasks.add_task(
        log_user_action, user.username, "CREATE_ITEM", f"title: {item.title}"
    )

    return db_item


@router.get("", response_model=list[ItemResponse])
@limiter.limit("50/minute")
async def get_items(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Item]:
    """Get all items for the current user."""
    stmt = select(Item).where(Item.owner_id == user.id)
    return db.execute(stmt).scalars().all()


@router.get("/{item_id}", response_model=ItemResponse)
@limiter.limit("50/minute")
async def get_item(request: Request, item: Item = Depends(get_item_for_user)) -> Item:
    """Get a specific item by ID"""
    return item


@router.put("/{item_id}", response_model=ItemResponse)
@limiter.limit("50/minute")
async def update_item(
    request: Request,
    item_update: ItemUpdate,
    item: Item = Depends(get_item_for_user),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Item:
    """
    Update an item

    - **item_id**: Item ID to update
    - **title**: new title (optional)
    - **description**: new description (optional)
    - **is_completed**: completion status (optional)

    Background tasks:
    - Send notification if item completed
    - Log action
    """
    was_completed: bool = item.is_completed

    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    # Add background tasks
    background_tasks.add_task(
        send_item_notification, user.email, user.username, item.title, "updated"
    )

    # If item was just marked as completed, run completion processing
    if not was_completed and item.is_completed:
        background_tasks.add_task(
            process_item_completion, item.id, user.username, item.title
        )

    background_tasks.add_task(
        log_user_action,
        user.username,
        "UPDATE_ITEM",
        f"item_id: {item.id}, completed: {item.is_completed}",
    )

    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")
async def delete_item(
    request: Request,
    item: Item = Depends(get_item_for_user),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> None:
    """
    Delete an item by ID

    - **item_id**: Item ID to delete

    Background tasks:
    - Send notification
    - Log action
    """
    item_title = item.title
    item_id = item.id
    db.delete(item)
    db.commit()

    # Add background tasks
    background_tasks.add_task(
        send_item_notification, user.email, user.username, item_title, "deleted"
    )
    background_tasks.add_task(
        log_user_action,
        user.username,
        "DELETE_ITEM",
        f"item_id: {item_id}, title: {item_title}",
    )

    return None
