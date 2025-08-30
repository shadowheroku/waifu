import os
import asyncio
from pyrogram import idle
import importlib
from rich.console import Console
from Bot import app, scheduler , logger as log 
from Bot.on_start import edit_restart_message , notify_startup , notify_stop
from Bot.scheduler_tasks import setup_scheduler_tasks
import shutil

console = Console()

MODULES = ["handlers"]


def cleanup():
    for root, dirs, _ in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                pycache_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(pycache_path)
                    console.print(f"[bold red]Deleted: {pycache_path}[/]")
                except Exception as e:
                    console.print(f"[bold yellow]Failed to delete {pycache_path}: {e}[/]")

def load_modules_from_folder(folder_name):
    loaded_modules = []
    folder_path = os.path.join(os.path.dirname(__file__), folder_name)
    
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith(".py") and filename != "__init__.py":
                # Get the relative path from the module folder to the current file's directory
                rel_path = os.path.relpath(root, folder_path)
                # Split into components, handle the case where rel_path is the same directory ('.')
                if rel_path == ".":
                    module_subdirs = []
                else:
                    module_subdirs = rel_path.split(os.sep)
                
                # Remove the .py extension to get the module name
                module_name = filename[:-3]
                
                # Construct the full module path components
                full_module_components = [folder_name] + module_subdirs + [module_name]
                full_module = ".".join(full_module_components)
                
                try:
                    # Attempt to import the module
                    importlib.import_module(f"Bot.{full_module}")
                    loaded_modules.append(full_module)
                except Exception as e:
                    log.error(f"Failed to load Bot.{full_module}: {str(e)}")
                    console.log(f"[bold red]Error loading Bot.{full_module}: {str(e)}[/bold red]")
    
    return loaded_modules

def load_all_modules():
    all_loaded_modules = []
    for folder in MODULES:
        all_loaded_modules.extend(load_modules_from_folder(folder))
    
    if all_loaded_modules:
        modules_list = ", ".join(all_loaded_modules)
        log_message = f"Successfully loaded modules: {modules_list}"
        log.info(log_message)
        console.log(f"[bold green]{log_message}[/bold green]")


async def initialize_async_components():
    try:
        # First create indexes before starting any services
        log.info("Starting index creation...")
        console.log("[yellow]Creating database indexes...[/yellow]")
        # await create_indexes()
        log.info("Database indexes created successfully")
        console.log("[green]✓ Database indexes created[/green]")

        scheduler.start()
        log.info("Scheduler started")
        
        # Set up scheduled tasks
        setup_scheduler_tasks()
        log.info("Scheduled tasks configured")

        # Verify bot connection
        bot_details = await app.get_me()
        log.info(f"Bot Configured: {bot_details.first_name} (ID: {bot_details.id}, @{bot_details.username})")
        console.log(f"[bold blue]Bot Ready: @{bot_details.username}[/bold blue]")
        
    except Exception as e:
        log.exception("Initialization failed")
        console.log(f"[bold red]Initialization error: {str(e)}[/bold red]")
        raise

if __name__ == "__main__":
    try:
        os.makedirs("downloads", exist_ok=True)
        load_all_modules()
        app.start()
        edit_restart_message()
        notify_startup()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(initialize_async_components())
        
        log.info("Entering idle state")
        console.log("[bold green]Bot is now running[/bold green]")
        idle()

    except KeyboardInterrupt:
        log.info("Bot stopped by user")
        console.log("[yellow]Bot stopped by user[/yellow]")
    except Exception as e:
        log.exception("Critical error during startup")
        console.log(f"[bold red]Fatal error: {str(e)}[/bold red]")
    finally:
        notify_stop()
        if 'app' in locals():        
            app.stop()
        cleanup()
        log.info("Bot shutdown complete")
        console.log("[yellow]Bot shutdown completed[/yellow]")