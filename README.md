# video bg remover

for fun project. needed something for yt shorts edits, so did it myself, works pretty well for what it is

<img width="1917" height="989" alt="image" src="https://github.com/user-attachments/assets/56ce69b7-8a0f-4e2b-9271-1d91815ee0dd" />


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
