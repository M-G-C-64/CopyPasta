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
        <div class="note">
            <p id="note-{row['id']}" class="note-text">{row['text']}</p>
            <div class="note-actions">
                <form method="post" action="/delete/{row['id']}" style="display:inline;">
                    <button type="submit" class="delete-btn">🗑️ Delete</button>
                </form>
                <button type="button" onclick="copyText('note-{row['id']}')" class="copy-btn">📋 Copy</button>
            </div>
        </div>
        """

    return f"""
    <html>
        <head>
            <title>Notice Board</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    max-width: 650px;
                    margin: 20px auto;
                    padding: 10px;
                    background: #121212;
                    color: #e0e0e0;
                }}
                h1 {{
                    text-align: center;
                    color: #f4f4f4;
                }}
                h2 {{
                    margin-top: 20px;
                    border-bottom: 1px solid #333;
                    padding-bottom: 5px;
                    color: #bbb;
                }}
                textarea {{
                    width: 100%;
                    font-size: 16px;
                    padding: 10px;
                    border-radius: 6px;
                    border: none;
                    background: #1e1e1e;
                    color: #f4f4f4;
                    box-sizing: border-box;
                }}
                button {{
                    font-size: 14px;
                    padding: 8px 14px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-weight: bold;
                }}
                .save-btn {{
                    background: #0077ff;
                    color: white;
                    width: 100%;
                    font-size: 16px;
                    margin-top: 8px;
                }}
                .note {{
                    border: 1px solid #333;
                    padding: 12px;
                    margin-bottom: 12px;
                    border-radius: 8px;
                    background: #1e1e1e;
                    box-shadow: 0px 2px 5px rgba(0,0,0,0.4);
                }}
                .note-text {{
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    margin-bottom: 10px;
                }}
                .note-actions {{
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }}
                .delete-btn {{
                    background: #e63946;
                    color: white;
                }}
                .copy-btn {{
                    background: #2a9d8f;
                    color: white;
                }}
                /* Mobile tweaks */
                @media (max-width: 480px) {{
                    button {{
                        flex: 1;
                        font-size: 13px;
                    }}
                }}
                /* Toast message */
                #toast {{
                    visibility: hidden;
                    min-width: 200px;
                    margin-left: -100px;
                    background-color: #333;
                    color: #fff;
                    text-align: center;
                    border-radius: 4px;
                    padding: 10px;
                    position: fixed;
                    z-index: 1;
                    left: 50%;
                    bottom: 30px;
                    font-size: 14px;
                    opacity: 0;
                    transition: opacity 0.5s, visibility 0.5s;
                }}
                #toast.show {{
                    visibility: visible;
                    opacity: 1;
                }}
            </style>
        </head>
        <body>
            <h1>📝 Notice Board</h1>
            <form method="post">
                <textarea name="text" rows="4" placeholder="Write a note..."></textarea><br>
                <button type="submit" class="save-btn">💾 Save</button>
            </form>
            <h2>All Notes</h2>
            {notes_html if notes_html else "<p style='color:#777;'>No notes yet.</p>"}
            <div id="toast">Copied to clipboard!</div>
            <script>
                function copyText(elementId) {{
                    const text = document.getElementById(elementId).innerText;
                    navigator.clipboard.writeText(text).then(() => {{
                        showToast();
                    }});
                }}
                function showToast() {{
                    const toast = document.getElementById("toast");
                    toast.className = "show";
                    setTimeout(() => {{ toast.className = toast.className.replace("show", ""); }}, 2000);
                }}
            </script>
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
