"""Item CRUD routes."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from models import User, Item
from schemas import ItemCreate, ItemUpdate, ItemResponse
from core import get_current_user
from tasks import send_item_notification, log_user_action, process_item_completion

router = APIRouter(prefix="/items", tags=["Items"])


@router.post("", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    username: str = Depends(get_current_user),
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
    user = db.query(User).filter(User.username == username).first()
    db_item = Item(
        title=item.title, description=item.description, owner_id=user.id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Add background tasks
    background_tasks.add_task(
        send_item_notification, user.email, username, item.title, "created"
    )
    background_tasks.add_task(
        log_user_action, username, "CREATE_ITEM", f"title: {item.title}"
    )
    
    return db_item


@router.get("", response_model=list[ItemResponse])
async def get_items(
    username: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all items for the current user."""
    user = db.query(User).filter(User.username == username).first()
    items = db.query(Item).filter(Item.owner_id == user.id).all()
    return items


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific item by ID."""
    user = db.query(User).filter(User.username == username).first()
    item = db.query(Item).filter(
        Item.id == item_id, Item.owner_id == user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    username: str = Depends(get_current_user),
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
    user = db.query(User).filter(User.username == username).first()
    item = db.query(Item).filter(
        Item.id == item_id, Item.owner_id == user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    was_completed = item.is_completed
    
    if item_update.title:
        item.title = item_update.title
    if item_update.description:
        item.description = item_update.description
    if item_update.is_completed is not None:
        item.is_completed = item_update.is_completed

    db.commit()
    db.refresh(item)
    
    # Add background tasks
    background_tasks.add_task(
        send_item_notification, user.email, username, item.title, "updated"
    )
    
    # If item was just marked as completed, run completion processing
    if not was_completed and item.is_completed:
        background_tasks.add_task(
            process_item_completion, item_id, username, item.title
        )
    
    background_tasks.add_task(
        log_user_action, username, "UPDATE_ITEM", f"item_id: {item_id}, completed: {item.is_completed}"
    )
    
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Delete an item by ID.
    
    Background tasks:
    - Send notification
    - Log action
    """
    user = db.query(User).filter(User.username == username).first()
    item = db.query(Item).filter(
        Item.id == item_id, Item.owner_id == user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item_title = item.title
    db.delete(item)
    db.commit()
    
    # Add background tasks
    background_tasks.add_task(
        send_item_notification, user.email, username, item_title, "deleted"
    )
    background_tasks.add_task(
        log_user_action, username, "DELETE_ITEM", f"item_id: {item_id}, title: {item_title}"
    )
    
    return None
