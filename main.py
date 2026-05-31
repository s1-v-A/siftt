import os
import time
import random
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="AeroDrop Engine")

vault_database = {}

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

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


static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/assets", StaticFiles(directory=static_dir), name="static")

@app.get("/{catchall:path}")
async def serve_frontend(catchall: str):
    """
    Catches any URL path typed into the browser bar and safely hands 
    over our single-page index.html interface file.
    """
    return FileResponse(os.path.join(static_dir, "index.html"))



from fastapi import UploadFile, File, HTTPException



# file upload route

@app.post("/api/rooms/{room_code}/upload")
async def upload_file_to_room(room_code: str, file: UploadFile = File(...)):
    """
    Accepts a raw binary file stream, saves it to the local Linux storage folder,
    and attaches the file metadata to the active RAM room.
    """
    if room_code not in vault_database:
        raise HTTPException(status_code=404, detail="Target room does not exist or has expired.")
    
    safe_filename = f"{room_code}_{file.filename}"
    file_save_path = os.path.join(STORAGE_DIR, safe_filename)
    
    with open(file_save_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    vault_database[room_code]["files"].append(file.filename)
    
    return {
        "status": "success",
        "filename": file.filename,
        "message": f"File successfully anchored to room {room_code}"
    }

