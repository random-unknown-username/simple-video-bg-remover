import os, subprocess, uuid, shutil, time
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE = Path(__file__).resolve().parent
FRONT = (BASE / ".." / "frontend").resolve()
TMP = (BASE / ".." / "work").resolve()
TMP.mkdir(parents=True, exist_ok=True)

# serve frontend so i dont need nginx lol
app.mount("/static", StaticFiles(directory=str(FRONT)), name="static")

from starlette.responses import FileResponse as FR


@app.get("/")
def home():
    return FR(str(FRONT / "index.html"))


# global session so model loads once, rembg does weird stuff
try:
    from rembg import new_session

    SESS = new_session("u2netp")
    print("model loaded yay")
except Exception as e:
    print("model load failed", e)
    SESS = None


def run(cmd):
    print("running:", cmd)
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print("ERR", r.stderr[:500])
    return r


def get_duration(p):
    # ffprobe magic
    r = run(
        f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{p}"'
    )
    try:
        return float(r.stdout.strip())
    except:
        print("couldnt parse dur")
        return 0.0


def get_fps(p):
    r = run(
        f'ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of default=noprint_wrappers=1:nokey=1 "{p}"'
    )
    txt = r.stdout.strip()
    if "/" in txt:
        a, b = txt.split("/")
        try:
            return float(a) / float(b)
        except:
            return 24.0
    try:
        return float(txt)
    except:
        return 24.0


def process_video(inp):
    job = uuid.uuid4().hex[:8]
    wdir = TMP / job
    wdir.mkdir(parents=True, exist_ok=True)
    frames_in = wdir / "in"
    frames_out = wdir / "out"
    frames_in.mkdir()
    frames_out.mkdir()
    print("job", job)

    dur = get_duration(inp)
    print("duration", dur)
    if dur > 20.5:
        raise HTTPException(status_code=400, detail="video too long max 20 sec")

    fps = get_fps(inp)
    if fps < 1 or fps > 60:
        fps = 24.0
    print("fps", fps)

    # extract frames, maybe downscale a bit so it doesnt take 3 hours
    run(f'ffmpeg -y -i "{inp}" -vf "scale=640:-2" "{frames_in}/f_%04d.png"')
    # note: scale uses nearest? whatever

    import glob

    pics = sorted(glob.glob(str(frames_in / "*.png")))
    print("num frames", len(pics))
    if len(pics) == 0:
        raise HTTPException(status_code=400, detail="no frames?")

    from rembg import remove
    from PIL import Image

    for i, pic in enumerate(pics):
        try:
            im = Image.open(pic)
            out = remove(im, session=SESS)
            # write matching name
            name = Path(pic).name
            out.save(str(frames_out / name))
        except Exception as e:
            print("frame err", i, e)
        if i % 10 == 0:
            print("did", i, "of", len(pics))

    outname = "result.webm"
    outpath = wdir / outname
    # encode vp9 with alpha. auto-alt-ref 0 is important or it breaks alpha i think
    run(
        f'ffmpeg -y -framerate {fps} -i "{frames_out}/f_%04d.png" -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 32 -auto-alt-ref 0 "{outpath}"'
    )

    if not outpath.exists():
        raise HTTPException(status_code=500, detail="encode failed")
    return outpath, wdir


@app.post("/process")
async def process(video: UploadFile = File(...)):
    # save upload
    updir = TMP / "uploads"
    updir.mkdir(parents=True, exist_ok=True)
    uid = uuid.uuid4().hex
    ext = ".mp4"
    if video.filename and "." in video.filename:
        ext = "." + video.filename.rsplit(".", 1)[-1]
    inpath = updir / (uid + ext)
    print("saving upload", inpath)
    with open(inpath, "wb") as f:
        import shutil

        shutil.copyfileobj(video.file, f)

    try:
        outpath, wdir = process_video(inpath)
    except HTTPException as e:
        print("httpexc", e.detail)
        raise
    except Exception as e:
        print("boom", e)
        raise HTTPException(status_code=500, detail=str(e))

    # return file, cleanup later-ish
    def cleanup():
        try:
            shutil.rmtree(wdir, ignore_errors=True)
        except Exception as e:
            print("cleanup err", e)
        try:
            os.remove(inpath)
        except:
            pass

    from starlette.background import BackgroundTask

    return FileResponse(
        str(outpath),
        media_type="video/webm",
        filename="result.webm",
        background=BackgroundTask(cleanup),
    )


# i always forget to close tags but ok
