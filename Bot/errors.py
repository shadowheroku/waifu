from functools import wraps
import asyncio
import traceback
from pyrogram.errors import *
from pyrogram.types import Message, InlineQuery, CallbackQuery
from Bot.config import ERRORS 
from Bot import logger as log , app
from cachetools import TTLCache, LRUCache

# Cache to prevent error spam
ERROR_CACHE = TTLCache(maxsize=1000, ttl=60)  # Cache errors for 60 seconds
# Cache for tracking error frequency by chat/user
ERROR_FREQUENCY = LRUCache(maxsize=5000)  # Track error frequency
FLOOD_WAIT_BACKOFF = 1.5  # Exponential backoff multiplier for repeated flood waits
MAX_RETRY_ATTEMPTS = 3  # Maximum number of retry attempts for flood wait
ERROR_REPORT_THRESHOLD = 5  # Number of errors before throttling reports for a chat/user

# Semaphore to limit concurrent error logging
_ERROR_LOG_SEMAPHORE = asyncio.Semaphore(5)

async def log_error(client, error_message, update, chat_id=None, user_id=None):
    """
    Log errors to the configured log channel with rate limiting to prevent spam.
    
    Args:
        client: The Pyrogram client
        error_message: The error message to log
        update: The update that caused the error
        chat_id: Optional chat ID where the error occurred
        user_id: Optional user ID who triggered the error
    """
    try:
        # Create a unique error key to prevent spam
        error_key = f"{error_message}:{chat_id or 0}:{user_id or 0}"
        
        # Check if this exact error was recently logged
        if error_key in ERROR_CACHE:
            # Update count but don't log again
            ERROR_CACHE[error_key] += 1
            return
        
        # Add to cache
        ERROR_CACHE[error_key] = 1
        
        # Track error frequency by chat/user
        frequency_key = f"{chat_id or 0}:{user_id or 0}"
        current_count = ERROR_FREQUENCY.get(frequency_key, 0) + 1
        ERROR_FREQUENCY[frequency_key] = current_count
        
        # If this chat/user has too many errors, throttle reporting
        if current_count > ERROR_REPORT_THRESHOLD:
            # Only log every Nth error after threshold
            if current_count % ERROR_REPORT_THRESHOLD != 0:
                return
        
        # Get update information
        update_type = type(update).__name__
        update_info = ""
        
        if isinstance(update, Message):
            chat_id = chat_id or update.chat.id
            user_id = user_id or (update.from_user.id if update.from_user else None)
            update_info = f"Message ID: {update.id} | Chat ID: {chat_id}"
            if user_id:
                update_info += f" | User ID: {user_id}"
            if update.text:
                update_info += f" | Text: {update.text[:100]}"
        
        elif isinstance(update, CallbackQuery):
            chat_id = chat_id or (update.message.chat.id if update.message else None)
            user_id = user_id or update.from_user.id
            update_info = f"Callback Query ID: {update.id}"
            if chat_id:
                update_info += f" | Chat ID: {chat_id}"
            update_info += f" | User ID: {user_id}"
            if update.data:
                update_info += f" | Data: {update.data}"
        
        elif isinstance(update, InlineQuery):
            user_id = user_id or update.from_user.id
            update_info = f"Inline Query ID: {update.id} | User ID: {user_id}"
            if update.query:
                update_info += f" | Query: {update.query}"
        
        # Format the error message
        log_message = (
            f"⚠️ **Error Report**\n\n"
            f"**Error Type:** {error_message.split(':', 1)[0] if ':' in error_message else 'Error'}\n"
            f"**Details:** `{error_message}`\n"
            f"**Update Type:** {update_type}\n"
            f"**Info:** {update_info}"
        )
        
        # Log to console
        log.error(f"Error: {error_message} | {update_info}")
        
        # # Send to log channel if configured, with concurrency control
        # if ERRORS:
        #     async with _ERROR_LOG_SEMAPHORE:
        #         await app.send_message(
        #             chat_id=ERRORS,
        #             text=log_message,
        #             disable_notification=True
        #         )
    except Exception as e:
        # If error logging itself fails, just log to console
        log.error(f"Error while logging error: {e}")

def capture_and_handle_error(func):
    """
    Decorator to handle errors in Pyrogram handlers.
    Provides automatic retry for flood waits and logs other errors.
    """
    @wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        # Extract chat_id and user_id for better error tracking
        chat_id = None
        user_id = None
        
        if isinstance(update, Message):
            chat_id = update.chat.id
            user_id = update.from_user.id if update.from_user else None
        elif isinstance(update, CallbackQuery):
            chat_id = update.message.chat.id if update.message else None
            user_id = update.from_user.id
        elif isinstance(update, InlineQuery):
            user_id = update.from_user.id
        
        # Track retry attempts for flood wait
        retry_count = 0
        wait_time = 0
        
        while retry_count <= MAX_RETRY_ATTEMPTS:
            try:
                # Call the actual function
                return await func(client, update, *args, **kwargs)
            
            except FloodWait as e:
                # Apply exponential backoff for repeated flood waits
                wait_time = e.value
                if retry_count > 0:
                    wait_time *= (FLOOD_WAIT_BACKOFF ** retry_count)
                
                log.warning(f"Flood wait for {wait_time:.2f} seconds (attempt {retry_count+1}/{MAX_RETRY_ATTEMPTS+1}).")
                
                # Log flood wait to error channel if it's significant
                if e.value > 10:
                    await log_error(
                        client, 
                        f"FloodWait: {e.value} seconds (attempt {retry_count+1}/{MAX_RETRY_ATTEMPTS+1})", 
                        update, 
                        chat_id, 
                        user_id
                    )
                
                # Wait and then retry
                await asyncio.sleep(wait_time)
                retry_count += 1
                
                # If this was the last attempt, log the failure
                if retry_count > MAX_RETRY_ATTEMPTS:
                    await log_error(
                        client, 
                        f"Max FloodWait retries exceeded ({MAX_RETRY_ATTEMPTS+1} attempts)", 
                        update, 
                        chat_id, 
                        user_id
                    )
            
            except BadRequest as e:
                log.error(f"Bad request error: {e}")
                await log_error(client, f"BadRequest: {str(e)}", update, chat_id, user_id)
                break
                
            except Forbidden as e:
                log.error(f"Forbidden error: {e}")
                await log_error(client, f"Forbidden: {str(e)}", update, chat_id, user_id)
                break
                
            except InternalServerError as e:
                log.error(f"Internal server error: {e}")
                await log_error(client, f"InternalServerError: {str(e)}", update, chat_id, user_id)
                # For server errors, we might want to retry once
                if retry_count == 0:
                    await asyncio.sleep(2)
                    retry_count += 1
                else:
                    break
                    
            except PeerIdInvalid as e:
                log.error(f"Peer ID invalid: {e}")
                await log_error(client, f"PeerIdInvalid: {str(e)}", update, chat_id, user_id)
                break
                
            except TimeoutError as e:
                log.error(f"Timeout error: {e}")
                await log_error(client, f"TimeoutError: {str(e)}", update, chat_id, user_id)
                # For timeout errors, we might want to retry once
                if retry_count == 0:
                    await asyncio.sleep(2)
                    retry_count += 1
                else:
                    break
                    
            except RPCError as e:
                # Generic handler for other RPC errors
                log.error(f"RPC error: {e}")
                await log_error(client, f"RPCError: {str(e)}", update, chat_id, user_id)
                break
                
            except Exception as e:
                # Catch all other exceptions
                error_traceback = traceback.format_exc()
                log.error(f"Unexpected error: {e}\n{error_traceback}")
                await log_error(client, f"UnexpectedError: {str(e)}", update, chat_id, user_id)
                break
    
    return wrapper

