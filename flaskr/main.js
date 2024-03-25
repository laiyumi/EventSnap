var video = document.getElementById('video');
var canvas = document.getElementById('canvas');
var context = canvas.getContext('2d');
var videoStreamUrl = false;

navigator.mediaDevices.getUserMedia({video: true}).then(function(stream) {
    video.srcObject = stream;
    videoStreamUrl = stream;
});

document.getElementById("snap").addEventListener("click", function() {
    context.drawImage(video, 0, 0, 640, 480);
    var data = canvas.toDataURL('image/jpeg');
    var http = new XMLHttpRequest();
    var url = '/save_image';
    http.open('POST', url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function() {
        if(http.readyState == 4 && http.status == 200) {
            alert(http.responseText);
        }
     }
    http.send('imageBase64=' + data);
});