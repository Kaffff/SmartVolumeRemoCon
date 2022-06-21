from fastapi import FastAPI
import uvicorn
from decibel import Decibel

app = FastAPI()
db_monitor = Decibel()


@app.get("/")
async def root():
    return {"message": "Hello World!"}



@app.post("/record/{name}")
async def record(name):
    print(name)


@app.post("/exec/{name}")
async def exec_name(name):
    print(name)

@app.get("/decibel")
async def get_decibel():
    return {"db": db_monitor.get_decibel()}




if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0", port=8000, log_level="info")

