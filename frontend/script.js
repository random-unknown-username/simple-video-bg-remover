var file = null;
var fakeTimer = null;

function start(){
  var inp = document.getElementById("fileInput");
  if(!inp.files || inp.files.length==0){ alert("pick a video first dawg"); return; }
  file = inp.files[0];

  if(file.size > 80*1024*1024){ alert("too big"); return; }

  // preview original
  var url = URL.createObjectURL(file);
  document.getElementById("orig").src = url;

  var st = document.getElementById("status");
  st.innerText = "uploading...";
  document.getElementById("prog").style.width = "5%";

  var fd = new FormData();
  fd.append("video", file);

  // fake progress bar because i dont know how to do real one
  var p = 5;
  fakeTimer = setInterval(function(){
    p += Math.random()*3;
    if(p > 90) p = 90;
    document.getElementById("prog").style.width = p + "%";
  }, 400);

  fetch("/process", { method:"POST", body: fd })
    .then(function(r){
      if(!r.ok){ return r.text().then(function(t){ throw new Error(t); }); }
      return r.blob();
    })
    .then(function(blob){
      clearInterval(fakeTimer);
      document.getElementById("prog").style.width = "100%";
      var burl = URL.createObjectURL(blob);
      document.getElementById("res").src = burl;
      var d = document.getElementById("dl");
      d.href = burl;
      d.style.display = "inline-block";
      document.getElementById("status").innerText = "done!";
    })
    .catch(function(err){
      clearInterval(fakeTimer);
      document.getElementById("prog").style.width = "0%";
      document.getElementById("status").innerText = "err: " + err.message;
      console.log(err);
    });
}
