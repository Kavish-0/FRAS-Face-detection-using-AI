function startRecognition(){

fetch("/start",{
method:"POST"
})
.then(res=>res.json())
.then(data=>{

if(data.status==="started"){

alert("Camera started. Look at the camera.")

checkStatus()

}else{

alert("Recognition already running.")

}

})

}


function checkStatus(){

const interval=setInterval(()=>{

fetch("/start/status")
.then(res=>res.json())
.then(data=>{

if(!data.running){

clearInterval(interval)

if(data.result && data.result!=="failed"){

alert("Attendance marked for "+data.result)

location.reload()

}else{

alert("Face not recognized")

}

}

})

},2000)

}