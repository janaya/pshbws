
// for each subscription, send subscription again?
var connection = {"hub.mode":"subscribe","hub.verify":"async","hub.callback":"<?php echo SMOB_ROOT.'callback'; ?>","hub.topic": "<?php echo $topic_url; ?>"};
socket.send(JSON.stringify(connection));
socket.on('message', function(obj){
  console.debug(obj);
//  if ('buffer' in obj){
//    document.getElementById('form').style.display='block';
//    document.getElementById('chat').innerHTML = '';
    
//    for (var i in obj.buffer) message(obj.buffer[i]);
//  } else message(obj);
});

function message(obj){
  var el = document.createElement('p');
  if ('announcement' in obj) el.innerHTML = '<em>' + esc(obj.announcement) + '</em>';
  else if ('message' in obj) el.innerHTML = '<b>' + esc(obj.message[0]) + ':</b> ' + esc(obj.message[1]);
  document.getElementById('chat').appendChild(el);
  document.getElementById('chat').scrollTop = 1000000;
}

function send(){
  var val = document.getElementById('text').value;
  socket.send(val);
  console.debug("message sent");
  message({ message: ['you', val] });
  document.getElementById('text').value = '';
}

function esc(msg){
  return String(msg).replace(/</g, '&lt;').replace(/>/g, '&gt;');
};
