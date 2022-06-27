from math import floor
from time import sleep
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from decibel import Decibel
from remocon import Remocon

app = FastAPI()
app.state.__setattr__(key="is_active",value=False)



@app.post("/start")
async def start(background_tasks: BackgroundTasks):
    app.state.__setattr__(key="is_active",value=True)
    sec = 0.5
    def loop():
        decibel = Decibel()
        remocon = Remocon()
        pre_db = decibel.get_decibel()
        pre_db_level = round(round(pre_db*2,-1)/10)
        sleep(sec)
        count = 0
        while app.state.__getattr__(key="is_active"):
            cur_db = decibel.get_decibel()
            cur_db_level = round(round(cur_db*2,-1)/10)
            print("{:.3f},{}".format(cur_db,cur_db_level))
            sleep(sec)
            margin = cur_db_level - pre_db_level
            if margin > 0 and count < 3:
                count  += 1
                continue
            if margin > 0:
                for i in range(margin*2):
                    remocon.play("volume_up")
                    print("up")
                    sleep(0.1)
            if margin < 0:
                for i in range(-margin*2):
                    remocon.play("volume_down")
                    print("down")
                    sleep(0.1)
            count = 0    
            pre_db_level = cur_db_level
            
    background_tasks.add_task(loop)
    
    
    
@app.post("/stop")
async def stop():
    app.state.__setattr__(key="is_active",value=False)
    


@app.post("/record", status_code=201)
async def record(name: str):
    r = Remocon()
    r.record(name)
    return {"status": 201, "name": name }


@app.post("/play", status_code=200)
async def play(name: str):
    r = Remocon()
    r.play(name)
    return {"status": 200, "name": name }


@app.post("/decibel")
async def get_decibel():
    decibel = Decibel()
    return {"{:.3f}".format(decibel.get_decibel())}


if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0", port=8000, log_level="info")

