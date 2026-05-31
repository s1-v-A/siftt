import os
import time
import random
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="AeroDrop Engine")

vault_database = {}

def generate_room_code(length: int = 5) -> str:   #adding room code generator
    """
    Generates a unique, uppercase alphanumeric string.
    We exclude confusing characters like 'O', '0', 'I', and '1'.
    """
    
    allowed_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    
    while True:
        code = "".join(random.choice(allowed_chars) for _ in range(length))
        
        if code not in vault_database:
            return code
        

# api layer

@app.post("/api/rooms/create")

async def create_room():
    """Initializes a brand new, empty transfer room in our RAM database."""
    room_code = generate_room_code()
    
    vault_database[room_code] = {
        "files": [],
        "created_at": time.time()
    }
    
    return {
        "status": "success",
        "room_code": room_code
    }



# Determine the absolute path to static files folder on system
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Mount the asset folder so the browser can download CSS or JS files
app.mount("/assets", StaticFiles(directory=static_dir), name="static")

# Fallback Route: Serve our plain HTML file for any room URL path
@app.get("/{catchall:path}")
async def serve_frontend(catchall: str):
    """
    Catches any URL path typed into the browser bar and safely hands 
    over our single-page index.html interface file.
    """
    return FileResponse(os.path.join(static_dir, "index.html"))

