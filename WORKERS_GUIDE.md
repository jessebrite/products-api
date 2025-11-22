"""
FastAPI Background Tasks Workers Guide

This guide explains how to use background tasks in your FastAPI application.
Background tasks are functions that run AFTER the response is sent to the client,
allowing long-running operations without blocking the user's request.
"""

# ============================================================================
# TABLE OF CONTENTS
# ============================================================================

"""
1. Overview & Architecture
2. Available Background Tasks
3. How Background Tasks Work
4. Using Background Tasks in Routes
5. Common Patterns & Examples
6. Error Handling
7. Monitoring & Debugging
8. Best Practices
9. Limitations & Considerations
10. Future Enhancements (Celery, RQ, etc.)
"""

# ============================================================================
# 1. OVERVIEW & ARCHITECTURE
# ============================================================================

"""
WHAT ARE BACKGROUND TASKS?
==========================
Background tasks are asynchronous operations that run after your API 
endpoint returns a response. They're perfect for:

✅ Sending emails (welcome, notifications, confirmations)
✅ Logging user actions (audit trail, analytics)
✅ Processing data (transformations, calculations)
✅ Triggering notifications (SMS, push notifications)
✅ Database cleanup (archiving, optimization)
✅ External API calls (webhooks, integrations)

ARCHITECTURE
============
        Client Request
              |
              v
        [Endpoint Handler]
              |
        [Create Response]
              |
      [Send Response] ──> Client receives response immediately ✓
              |
              v
    [Background Tasks Queue]
              |
     [Task 1] [Task 2] [Task 3]  ← Run concurrently, independently
              |
        [Tasks Complete]
              (Client doesn't wait for this)

KEY BENEFITS
============
✓ Fast API responses (tasks don't block)
✓ Better user experience (no waiting)
✓ Reliable execution (FastAPI manages task lifecycle)
✓ Easy to implement (built into FastAPI)
✓ No external services needed (Celery, Redis not required)

LIMITATIONS
===========
✗ Limited to single server (not distributed)
✗ Tasks lost if server restarts (no persistence)
✗ No built-in retry mechanism
✗ No task scheduling (use APScheduler for that)
✗ Not suitable for very heavy processing
"""

# ============================================================================
# 2. AVAILABLE BACKGROUND TASKS
# ============================================================================

"""
Located in: src/tasks/worker.py

EMAIL TASKS
===========
• send_welcome_email(email, username)
  → Send welcome email to newly registered user
  → TODO: Integrate with SendGrid/AWS SES/SMTP

• send_item_notification(recipient_email, recipient_username, item_title, notification_type)
  → Send notifications about item activity
  → Types: "created", "updated", "completed", "deleted"

• send_batch_email(recipient_list, subject, body)
  → Send email to multiple recipients
  → TODO: Integrate with batch email service

LOGGING TASKS
=============
• log_user_action(username, action, details=None)
  → Log user actions for audit trail
  → Actions: REGISTER, LOGIN, CREATE_ITEM, UPDATE_ITEM, DELETE_ITEM
  → TODO: Store in audit_logs table or external logging service

PROCESSING TASKS
================
• process_item_completion(item_id, username, item_title)
  → Process item completion (awards, badges, streaks, etc.)
  → TODO: Add achievement/statistics logic

MAINTENANCE TASKS
=================
• cleanup_old_data()
  → Clean up old/deleted data
  → TODO: Implement cleanup logic
"""

# ============================================================================
# 3. HOW BACKGROUND TASKS WORK
# ============================================================================

"""
STEP-BY-STEP FLOW
==================

1. CLIENT MAKES REQUEST
   POST /api/v1/auth/register
   {"username": "john", "email": "john@example.com", "password": "secret"}

2. ENDPOINT HANDLER EXECUTES
   - Validate request
   - Create database objects
   - Commit to database
   
3. BACKGROUND TASKS ADDED TO QUEUE
   background_tasks.add_task(send_welcome_email, "john@example.com", "john")
   background_tasks.add_task(log_user_action, "john", "REGISTER", "email: john@example.com")
   
4. RESPONSE SENT TO CLIENT
   HTTP 200 OK
   {"id": 1, "username": "john", ...}
   ← Client receives response IMMEDIATELY
   
5. BACKGROUND TASKS EXECUTE
   [After response is sent]
   - send_welcome_email runs
   - log_user_action runs
   - Both run independently, user doesn't wait

EXECUTION ORDER
================
- Tasks execute sequentially by default
- Can add multiple tasks to queue
- Each task is independent
- If one task fails, others continue

CONTEXT LIMITATIONS
====================
! Background tasks run OUTSIDE request context
! Cannot use db session from request
! Need to create their own database sessions if needed
! Limited access to request-specific data
→ Solution: Pass all needed data as function parameters
"""

# ============================================================================
# 4. USING BACKGROUND TASKS IN ROUTES
# ============================================================================

"""
BASIC PATTERN
=============

from fastapi import BackgroundTasks
from src.tasks import send_welcome_email

@app.post("/auth/register")
async def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    # Create user in database
    db_user = User(...)
    db.add(db_user)
    db.commit()
    
    # Add background task
    background_tasks.add_task(send_welcome_email, user.email, user.username)
    
    # Return response - client gets this immediately
    return db_user
    # Tasks run AFTER this return


MULTIPLE TASKS
===============

@app.post("/items")
async def create_item(
    item: ItemCreate,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    # Create item
    db_item = Item(...)
    db.add(db_item)
    db.commit()
    
    # Add MULTIPLE background tasks
    background_tasks.add_task(
        send_item_notification, 
        user.email, username, item.title, "created"
    )
    background_tasks.add_task(
        log_user_action,
        username, "CREATE_ITEM", f"title: {item.title}"
    )
    
    return db_item
    # Both tasks run after response


TASK WITH ARGUMENTS
====================

# Simple parameters
background_tasks.add_task(log_user_action, username, "LOGIN")

# Named parameters
background_tasks.add_task(
    send_item_notification,
    recipient_email=user.email,
    recipient_username=username,
    item_title=item.title,
    notification_type="created"
)

# Mixed positional and keyword
background_tasks.add_task(
    send_welcome_email,
    user.email,
    username
)
"""

# ============================================================================
# 5. COMMON PATTERNS & EXAMPLES
# ============================================================================

"""
PATTERN 1: User Registration with Welcome Email
================================================

@router.post("/register", response_model=UserResponse)
async def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    # Validate and create user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send welcome email in background
    background_tasks.add_task(send_welcome_email, user.email, user.username)
    
    # Client gets response immediately
    return db_user
    # Email sends while client is parsing response


PATTERN 2: Action Logging & Audit Trail
========================================

@router.post("/items", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    user = db.query(User).filter(User.username == username).first()
    
    # Create item
    db_item = Item(
        title=item.title,
        description=item.description,
        owner_id=user.id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Log action for audit trail
    background_tasks.add_task(
        log_user_action,
        username,
        "CREATE_ITEM",
        f"item_id: {db_item.id}, title: {item.title}"
    )
    
    return db_item
    # Action logged after response sent


PATTERN 3: Conditional Processing
==================================

@router.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    item = db.query(Item).filter(Item.id == item_id).first()
    was_completed = item.is_completed
    
    # Update item
    if item_update.is_completed is not None:
        item.is_completed = item_update.is_completed
    db.commit()
    
    # Only trigger completion task if just marked as completed
    if not was_completed and item.is_completed:
        background_tasks.add_task(
            process_item_completion,
            item_id,
            username,
            item.title
        )
    
    return item


PATTERN 4: Batch Notifications
=======================================

@router.post("/send-newsletter")
async def send_newsletter(
    newsletter: NewsletterCreate,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    # Get all subscribers
    subscribers = db.query(User).filter(User.is_subscribed == True).all()
    recipient_emails = [s.email for s in subscribers]
    
    # Queue batch email
    background_tasks.add_task(
        send_batch_email,
        recipient_emails,
        newsletter.subject,
        newsletter.body
    )
    
    return {"status": "Newsletter queued for sending"}
    # Emails send to all subscribers in background
"""

# ============================================================================
# 6. ERROR HANDLING
# ============================================================================

"""
BACKGROUND TASK FAILURES
=========================

Background tasks can fail silently! Always wrap them with error handling.

Current Implementation (in worker.py):
✓ Each task has try-except blocks
✓ Errors are logged
✓ Task failures don't crash the API
✓ Other tasks continue if one fails


EXAMPLE ERROR HANDLING
======================

def send_welcome_email(email: str, username: str) -> None:
    try:
        # Send email
        send_email(email, template="welcome", data={"username": username})
        logger.info(f"Welcome email sent to {email}")
    except SMTPException as e:
        logger.error(f"SMTP error sending to {email}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending to {email}: {e}")


MONITORING TASK FAILURES
=========================

1. Check application logs
   tail -f logs/app.log
   
2. Look for ERROR level entries
   [ERROR] Failed to send welcome email to ...
   
3. Monitor success rate
   - Count successful vs failed tasks
   - Set alerts for high failure rates
   
4. Store failed tasks for retry
   - Save to "failed_tasks" table
   - Retry failed tasks periodically


WHAT HAPPENS IF TASK FAILS?
============================
✓ Error is logged
✓ API continues normally
✓ Client doesn't know/care
✓ Other tasks still run
✗ Email/notification not sent
✗ Action not logged
✗ No automatic retry

BEST PRACTICE: Add health checks to monitor task execution
"""

# ============================================================================
# 7. MONITORING & DEBUGGING
# ============================================================================

"""
HOW TO DEBUG BACKGROUND TASKS
=============================

1. CONSOLE OUTPUT
   └─ Each task prints to console (for development)
      stdout: "📧 [TASK] Welcome email sent..."
      
2. LOGGING
   └─ Tasks log to logger (for production)
      from logging import getLogger
      logger = getLogger("tasks")
      logger.info("Task executed")
      
3. CHECK TASK COMPLETION
   └─ If API response is fast, tasks might still be running
   └─ Check logs/console after response received
   
4. ADD PRINT STATEMENTS
   └─ Temporary debug prints in worker.py:
      print(f"DEBUG: Task running with args: {args}")

EXAMPLE DEBUG SESSION
====================

1. Start server with logging:
   uvicorn src.main:app --reload --log-level debug

2. Make request:
   POST /api/v1/auth/register

3. Check console for task output:
   📧 [TASK] Welcome email sent to user@example.com
   📝 [AUDIT] User 'john' performed action 'REGISTER'

4. If tasks don't appear:
   - Check they were added: background_tasks.add_task(...)
   - Check function parameters match
   - Check for exceptions in task code


MONITORING IN PRODUCTION
========================

1. Set up centralized logging (ELK Stack, Datadog, etc.)
2. Monitor task success/failure rates
3. Set alerts for task failures
4. Track task execution time
5. Monitor for stuck/hanging tasks
"""

# ============================================================================
# 8. BEST PRACTICES
# ============================================================================

"""
✅ DO:

1. Pass all data as function parameters
   ✓ background_tasks.add_task(func, arg1, arg2, arg3)
   ✗ Don't rely on closures or global state

2. Keep tasks fast
   ✓ Email: < 1 second
   ✓ Logging: < 100ms
   ✓ Simple processing: < 500ms
   ✗ Don't do heavy computations in tasks

3. Use try-except in tasks
   ✓ Handle errors gracefully
   ✓ Log failures
   ✗ Don't let tasks crash silently

4. Log task execution
   ✓ Log when task starts
   ✓ Log when task completes
   ✓ Log any errors
   ✗ Don't assume tasks ran successfully

5. Make tasks idempotent
   ✓ Can run multiple times without side effects
   ✓ Example: Sending notification with same ID twice = OK
   ✗ Example: Incrementing counter without checking = BAD

6. Document task parameters
   ✓ Clear docstrings explaining what each parameter is
   ✗ Cryptic parameter names


❌ DON'T:

1. Use request context in tasks
   ✗ background_tasks.add_task(func, request=request)
   ✗ request context not available in task
   ✓ Pass specific values instead

2. Access db session from request
   ✗ db = request.state.db  # Don't do this
   ✓ Pass data you need as parameters

3. Assume tasks completed
   ✗ Don't assume email was sent immediately
   ✗ User gets response before email leaves
   ✓ Check logs to verify task completion

4. Use for heavy processing
   ✗ Don't use for: ML inference, image processing, data export
   ✓ Use for: Lightweight tasks (emails, logging, notifications)

5. Long-running tasks
   ✗ Task timeout: varies by server (usually 30-300 seconds)
   ✗ Long tasks may not complete
   ✓ Keep tasks under 10 seconds

6. Store task state
   ✗ Don't store task state in memory
   ✓ Store in database if you need to track
"""

# ============================================================================
# 9. LIMITATIONS & CONSIDERATIONS
# ============================================================================

"""
SINGLE SERVER LIMITATION
=========================
Background tasks only work on the server that receives the request.
If you scale to multiple servers, each handles its own tasks.

Example:
Server 1: Receives request → Runs tasks → Response sent
Server 2: Receives request → Runs tasks → Response sent

If task depends on Server 1 context → Problem!
Solution: Use distributed task queue (Celery, RQ)


TASK PERSISTENCE
================
Tasks are lost if:
✗ Server stops/restarts
✗ Server crashes during task execution
✗ Network interruption

For critical tasks, consider:
✓ Celery + Redis (persistent task queue)
✓ Store task state in database
✓ Implement retry logic


NO BUILT-IN RETRY
=================
If task fails → No automatic retry
Solution:
✓ Wrap task with retry logic
✓ Store failed tasks in database
✓ Implement periodic retry job
✓ Use Celery for automatic retries


NO BUILT-IN SCHEDULING
======================
Background tasks run immediately after response.
For scheduled tasks (daily, weekly):
✓ Use APScheduler
✓ Use Celery Beat
✓ Use cron jobs


EXECUTION TIME CONSTRAINTS
==========================
Each task should complete within:
- Development: No hard limit (but keep < 5 minutes)
- Production: Depends on server config (typically 30-300 seconds)

If tasks regularly exceed time limit:
✓ Break into smaller tasks
✓ Use distributed task queue (Celery)
✓ Use async processing


DEBUGGING DIFFICULTY
====================
Harder to debug than synchronous code:
- Errors don't block the response
- Stack traces appear in logs, not response
- Timing issues from async execution
- Task order not guaranteed across servers

Solution: Good logging and monitoring
"""

# ============================================================================
# 10. FUTURE ENHANCEMENTS
# ============================================================================

"""
UPGRADE PATH: WHEN TO USE CELERY
==================================

Current (FastAPI Background Tasks):
✓ Simple use case
✓ Single server
✓ Non-critical tasks
✓ No external dependencies

Upgrade to Celery when:
✗ Multiple servers (need distributed task queue)
✗ Long-running tasks (> 1 minute)
✗ Scheduled tasks needed
✗ Task persistence required
✗ High reliability needed
✗ Task monitoring needed

CELERY + REDIS SETUP
====================
# Install
pip install celery redis

# src/celery_app.py
from celery import Celery

celery_app = Celery(
    "myapp",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def send_welcome_email_task(email: str, username: str):
    send_welcome_email(email, username)

# In route
from src.celery_app import send_welcome_email_task

@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Create user
    db_user = User(...)
    db.add(db_user)
    db.commit()
    
    # Queue Celery task (persisted in Redis)
    send_welcome_email_task.delay(user.email, user.username)
    
    return db_user


ASYNC WORKER PATTERN
====================
# For heavy async operations
import asyncio

async def process_large_file_async(file_path: str):
    # Heavy async I/O
    data = await read_file_async(file_path)
    processed = await process_async(data)
    await save_results_async(processed)

@router.post("/process")
async def upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    # Save file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    
    # Queue async processing
    background_tasks.add_task(
        asyncio.run,
        process_large_file_async(file_path)
    )
    
    return {"status": "File processing started"}


MONITORING WITH DATADOG/NEWRELIC
================================
Track:
- Task execution time
- Task success/failure rate
- Task queue depth
- Worker availability

Set up alerts for:
- High failure rate
- Long task execution time
- Worker health issues
"""

# ============================================================================
# QUICK REFERENCE
# ============================================================================

"""
IMPORT
======
from fastapi import BackgroundTasks
from src.tasks import send_welcome_email, log_user_action

USE IN ROUTE
============
@router.post("/endpoint")
async def my_endpoint(
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    # Do work
    
    # Add task
    background_tasks.add_task(send_welcome_email, "user@example.com", "john")
    
    # Return response
    return {"status": "ok"}

AVAILABLE TASKS
===============
from src.tasks import (
    send_welcome_email,
    log_user_action,
    send_item_notification,
    process_item_completion,
    send_batch_email,
    cleanup_old_data,
)

COMMON PATTERNS
===============
# Single task
background_tasks.add_task(func, arg1, arg2)

# Multiple tasks
background_tasks.add_task(func1, arg1)
background_tasks.add_task(func2, arg2)

# Conditional
if condition:
    background_tasks.add_task(func, arg)

# With keyword args
background_tasks.add_task(
    send_item_notification,
    recipient_email=user.email,
    recipient_username=username,
    item_title=item.title,
    notification_type="created"
)

DEBUGGING
=========
# Check console output (development)
# Check logs (production)
# Add print statements to worker.py
# Monitor task execution in logs
# Use logging module for persistent logs
"""

print(__doc__)
