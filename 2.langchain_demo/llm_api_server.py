from fastapi import FastAPI, Request
from transformers import AutoTokenizer, AutoModel
import uvicorn, json, datetime
import torch

DEVICE = "cuda"
DEVICE_ID = "0"
CUDA_DEVICE = f"{DEVICE}:{DEVICE_ID}" if DEVICE_ID else DEVICE


def torch_gc():
    if torch.cuda.is_available():
        with torch.cuda.device(CUDA_DEVICE):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()


## prepare llm model
llm_name = "THUDM/chatglm-6b"
# 先把llm模型下载到本地某个目录
checkpoint = "/share/public/huggingface_cache/" + llm_name
print("loading tokenizer ...")
tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
print("loading llm ...")
model = AutoModel.from_pretrained(checkpoint, trust_remote_code=True).half().cuda()
model.eval()

## prepare api server
app = FastAPI()


@app.post("/")
async def create_item(request: Request):
    global model, tokenizer
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    prompt = json_post_list.get("prompt")
    history = json_post_list.get("history")
    max_length = json_post_list.get("max_length")
    top_p = json_post_list.get("top_p")
    temperature = json_post_list.get("temperature")
    response, history = model.chat(
        tokenizer,
        prompt,
        history=history,
        max_length=max_length if max_length else 2048,
        top_p=top_p if top_p else 0.7,
        temperature=temperature if temperature else 0.95,
    )
    now = datetime.datetime.now()
    time = now.strftime("%Y-%m-%d %H:%M:%S")
    answer = {"response": response, "history": history, "status": 200, "time": time}
    log = (
        "["
        + time
        + "] "
        + '", prompt:"'
        + prompt
        + '", response:"'
        + repr(response)
        + '"'
    )
    print(log)
    torch_gc()
    return answer


def main():
    global app
    uvicorn.run(app, host="0.0.0.0", port=10000, workers=1)

# 程序运行的入口
if __name__ == "__main__":
    main()
