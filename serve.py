from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from src.bitcoin_interface import BitcoinInterface, BitcoinNetwork
from src.box import Box
import threading
from src.add import add
from src.cache import Cache

async def lifespan(app: FastAPI):
    bitcoin_interface = BitcoinInterface(network=BitcoinNetwork.REGTEST, silent=True)
    bitcoin_interface.remove_bitcoin_directory()
    bitcoin_interface.kill_process_using_port(18443)
    bitcoind_thread = threading.Thread(target=bitcoin_interface.start_bitcoind)
    bitcoind_thread.start()
    yield
    bitcoin_interface.stop_bitcoind()
    bitcoind_thread.join()

app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/add/", status_code=status.HTTP_201_CREATED)
def add_box(box: Box) -> str:
    return add(box)

@app.put("/update/{box_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_box(box_id: str, box: Box):
    return status.HTTP_501_NOT_IMPLEMENTED
    updated_box = update(box_id, box)
    if not updated_box:
        raise HTTPException(status_code=404, detail="Box not found")
    return status.HTTP_204_NO_CONTENT

@app.get("/fetch/", status_code=status.HTTP_200_OK)
def fetch_boxes():
    return list(Cache().get_all_boxes())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
