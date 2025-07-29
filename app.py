from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import databases
import sqlalchemy

# Database setup
DATABASE_URL = "sqlite:///copypasta.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Table definition
copypasta = sqlalchemy.Table(
    "copypasta",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("text", sqlalchemy.Text),
)

engine = sqlalchemy.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def home():
    query = copypasta.select().order_by(copypasta.c.id.desc())
    rows = await database.fetch_all(query)

    notes_html = ""
    for row in rows:
        notes_html += f"""
        <div style='border:1px solid #ccc; padding:10px; margin-bottom:10px; border-radius:5px;'>
            <p style="white-space: pre-wrap;">{row['text']}</p>
            <form method="post" action="/delete/{row['id']}" style="display:inline;">
                <button type="submit" style="background:red;color:white;border:none;padding:5px 10px;border-radius:3px;">Delete</button>
            </form>
        </div>
        """

    return f"""
    <html>
        <head><title>Notice Board</title></head>
        <body style="font-family: Arial; max-width: 600px; margin: 30px auto;">
            <h1>Notice Board</h1>
            <form method="post">
                <textarea name="text" rows="4" style="width: 100%; font-size: 16px;"></textarea><br><br>
                <button type="submit" style="padding: 10px 20px; font-size: 16px;">Save</button>
            </form>
            <h2>All Notes:</h2>
            {notes_html if notes_html else "<p>No notes yet.</p>"}
        </body>
    </html>
    """

@app.post("/", response_class=HTMLResponse)
async def save_text(text: str = Form(...)):
    if text.strip():  # Only save non-empty notes
        query = copypasta.insert().values(text=text)
        await database.execute(query)
    return RedirectResponse("/", status_code=303)

@app.post("/delete/{note_id}", response_class=HTMLResponse)
async def delete_text(note_id: int):
    query = copypasta.delete().where(copypasta.c.id == note_id)
    await database.execute(query)
    return RedirectResponse("/", status_code=303)
