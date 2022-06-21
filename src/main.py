from fastapi import FastAPI, BackgroundTasks
import uvicorn
from decibel import Decibel
from remocon import Remocon

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.post("/monitor")
async def monitor(background_tasks: BackgroundTasks):
    decibel = Decibel()
    def callback(pre,cur):
        print("pre:{:.3f} cur:{:.3f}".format(pre,cur))
    background_tasks.add_task(decibel.monitor,callback)
    

@app.post("/record/{name}")
async def record(name):
    r = Remocon()
    r.record(name)


@app.post("/play/{name}")
async def play(name):
    r = Remocon()
    r.play(name)

@app.get("/decibel")
async def get_decibel():
    decibel = Decibel()
    return {"Db":"{:.3f}".format(decibel.get_decibel())}


if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0", port=8000, log_level="info")

