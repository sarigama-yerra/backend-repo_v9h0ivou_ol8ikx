import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve uploaded files
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.post("/api/upload")
async def upload_files(
    spec: Optional[UploadFile] = File(default=None, description="H.A.R.M.O.N.I. spec file"),
    csv: Optional[UploadFile] = File(default=None, description="P1–P9 breed vectors CSV"),
):
    if not spec and not csv:
        raise HTTPException(status_code=400, detail="No files provided. Send 'spec' and/or 'csv'.")

    saved = {}

    async def _save(file: UploadFile, label: str):
        # Sanitize filename
        original_name = os.path.basename(file.filename or label)
        name_without_spaces = original_name.replace(" ", "_")
        # Prefix to avoid collisions
        target_name = f"{label}__{name_without_spaces}"
        target_path = os.path.join(UPLOAD_DIR, target_name)
        contents = await file.read()
        with open(target_path, "wb") as f:
            f.write(contents)
        return {
            "filename": original_name,
            "stored_as": target_name,
            "size": len(contents),
            "url": f"/files/{target_name}",
        }

    if spec:
        saved["spec"] = await _save(spec, "spec")
    if csv:
        saved["csv"] = await _save(csv, "csv")

    return {"status": "ok", "files": saved}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
