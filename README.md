# video bg remover

for fun project. needed something for yt shorts edits, so made this lol. works kinda.

# how to run:
need python 3.10+ and ffmpeg installed
```
pip install -r requirements.txt
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000
```

open http://localhost:8000

notes:
- uses rembg (u2netp) so kinda slow
- output is webm with transparent bg, use chrome
- keep videos short (<20 sec)
- if it crashes just rerun
