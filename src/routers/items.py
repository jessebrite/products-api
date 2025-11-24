"""Item CRUD routes."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Item, User
from schemas import ItemCreate, ItemResponse, ItemUpdate
from security import get_current_user
from tasks import log_user_action, process_item_completion, send_item_notification

router = APIRouter(prefix="/items", tags=["Items"])


async def get_item_for_user(
    item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Item:
    """Get an item by ID for the current user, or raise 404."""
    item = db.query(Item).filter(Item.id == item_id, Item.owner_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Create a new item.

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
async def get_items(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all items for the current user."""
    return db.query(Item).filter(Item.owner_id == user.id).all()


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item: Item = Depends(get_item_for_user)):
    """Get a specific item by ID."""
    return item


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_update: ItemUpdate,
    item: Item = Depends(get_item_for_user),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Update an item.

    - **item_id**: Item ID to update
    - **title**: Optional new title
    - **description**: Optional new description
    - **is_completed**: Optional completion status

    Background tasks:
    - Send notification if item completed
    - Log action
    """
    was_completed = item.is_completed

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
async def delete_item(
    item: Item = Depends(get_item_for_user),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Delete an item by ID.

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
