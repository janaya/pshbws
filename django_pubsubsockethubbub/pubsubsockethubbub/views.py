from django.http import HttpResponse
from datetime import datetime
import json
from models import Subscription

#def web_server_hub_handler(request):
#    if request.POST.get('hub.mode', None) == 'subscribe':
#        logging.debug("mode subscribe")
#        web_server_subscribe_handler(request)

#def web_server_subscribe_handler(request):
#    logging.debug("request.POST: ")
#    logging.debug(request.POST)
#    subs_dict = request.POST
#    try:
#        callback = request.POST['hub.callback']
#        topic = request.POST['hub.topic']
#        mode = request.POST['hub.mode']
#        verify = _get_verify(request.POST.getlist('hub.verify'))
#    except KeyError, e:
#        return http.HttpResponseBadRequest(str(e))

#    defaults = {
#        'lease_seconds': (request.POST.get('hub.lease-seconds'), int),
#        'secret': (request.POST.get('hub.secret'), str),
#    }
#    try:
#        defaults = dict((k, c(v)) for k, (v, c) in defaults.items() if v is not None)
#    except ValueError, e:
#        return http.HttpResponseBadRequest(str(e))
#    
#    verify_token = request.POST.get('hub.verify_token', ''),
#    
#    response = subscribe(subs_dict)
#    if response.find('ERROR') == 0:
#        return http.HttpResponseBadRequest(response)

#def ws_subscribe(subs_dict):
#    if subs_dict["hub.mode"] not in dict(models.MODES):
#      return 'ERROR: Unknown hub.mode: %s' % mode
##    task, created = models.SubscriptionTask.objects.get_or_create(**subs_dict)
#    if subs_dict["hub.verify"] == 'sync':
##        result, description = task.verify()

##        challenge = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(40))
##        params = {
##            'hub.mode': subs_dict["hub.mode"],
##            'hub.topic': subs_dict["topic"],
##            'hub.challenge': challenge,
##            'hub.lease_seconds': min(MAX_LEASE, max(MIN_LEASE, self.lease_seconds))
##        }
##        if self.verify_token:
##            params['hub.verify_token'] = self.verify_token
##        join = '&' if '?' in subs_dict["hub.callback"] else '?'
##        url = '%s%s%s' % (self.callback, join, urlencode(params))
##        h = httplib2.Http(timeout=utils.HTTP_TIMEOUT)
##        try:
##            response, body = h.request(url, 'GET')
#        
#        
#        if result and description == 'verified':
#            return http.HttpResponse('', status=204)
#        else:
#            return http.HttpResponseBadRequest('Verification failed: %s' % description)
#    else:
#        return http.HttpResponse('Subscription queued', status=202)

buffer = []

def socketio(request):
    print "in socketio"
    socketio = request.environ['socketio']
    if socketio.on_connect():
        print buffer
        socketio.send({'buffer': buffer})
        socketio.broadcast({'announcement': socketio.session.session_id + ' connected'})

    while True:
        message = socketio.recv()
        print "message received: "
        print message

        if len(message) == 1:
            print "len 1"
            message = message[0]
            
            message_dict = json.loads(message)
            print message_dict
            
            if message_dict["hub.mode"] == 'subscribe':
                params = {
                    'topic': message_dict["hub.topic"],
                    'callback': message_dict["hub.callback"],
                    'expires': datetime.now(),
                }
                subcription = Subscription.objects.get_or_create(**params)
            socketio.send('204')
            print "sent ACK"

        else:
            if not socketio.connected():
                socketio.send('disconnected')
                break

    return HttpResponse()
