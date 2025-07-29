from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get('/')
def home():
    return HTMLResponse("""<h1> Hello world this is ganesh, testing</h1>
                        <br>
                        <p>testing a long ass paragraph<p>""")