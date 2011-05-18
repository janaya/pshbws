import sys
sys.path.append('google')
sys.path.append('tornado')

from tornado.options import define, options
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
#import tornado.wsgi
import wsgiref.handlers

#import json
import simplejson as json
import logging
import urllib2
import urllib

from google.appengine.ext import db

logging.basicConfig(level=logging.DEBUG)
#log = logging.getLogger()
define("port", default=8081, help="run on the given port", type=int)

# Default expiration time of a lease.
DEFAULT_LEASE_SECONDS = (5 * 24 * 60 * 60)  # 5 days

HUB_URL = 'http://pubsubhubbub.appspot.com'
WSS_CALLBACK_URL = 'http://rhizomatik.net:8081/callback'

class SubscriptionChallengeHandler(tornado.web.RequestHandler):
    #TODO: class not needed if using @tornado.web.asynchronous in 
    # Subscription.send_subscribe_request?
    
    def get(self):
        #TODO: is there response in the write ?
        
        challenge = self.get_argument("hub.challenge", None)
        if challenge:
            print "got challenge: %s" % challenge
            self.write(challenge)
            
        else:
            print "no challenge, get arguments:"  
            print self.request.arguments

    def post(self):
        #TODO: check the 'X-Hub-Signature'?
        
        print "got post from: %s" % self.request.get_header['User-Agent']
        data = self.request.body
        # TODO: how to send back confirmation to the WSSubscribeHandler 
        # handler?

class Subscription(db.Model):
    # from google hub, 
    #TODO: to manage the subscriptions, 
    # not via (callback_hash, topic_hash), but by (S dyndns URI, P...)
    
    """Represents a single subscription to a topic for a callback URL."""

    STATE_NOT_VERIFIED = 'not_verified'
    STATE_VERIFIED = 'verified'
    STATE_TO_DELETE = 'to_delete'
    STATES = frozenset([
      STATE_NOT_VERIFIED,
      STATE_VERIFIED,
      STATE_TO_DELETE,
    ])

    callback = db.TextProperty(required=True)
#    callback_hash = db.StringProperty(required=True)
    topic = db.TextProperty(required=True)
#    topic_hash = db.StringProperty(required=True)
    mode = db.TextProperty(required=True)
    verify = db.TextProperty(required=True)
    
    created_time = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    lease_seconds = db.IntegerProperty(default=DEFAULT_LEASE_SECONDS)
#    expiration_time = db.DateTimeProperty(required=True)
    eta = db.DateTimeProperty(auto_now_add=True)
    confirm_failures = db.IntegerProperty(default=0)
    verify_token = db.TextProperty()
    secret = db.TextProperty()
    hmac_algorithm = db.TextProperty()
    subscription_state = db.StringProperty(default=STATE_NOT_VERIFIED,
                                           choices=STATES)

    def send_subscribe_request(self):
        #TODO: use here @tornado.web.asynchronous in case verify=async?
        
        headers = {
#  #        "Authorization": "Basic "+ base64.encode(username + ":" + password),
          "Content-Type": "application/x-www-form-urlencoded",
          "User-Agent": "pshbwss",
        }

        params = {
            'hub.mode': self.mode,
            'hub.callback': WSS_CALLBACK_URL,
            'hub.topic': self.topic,
            'hub.verify': self.verify,
        }
        data = urllib.urlencode(params)
        print data
        request = urllib2.Request(HUB_URL, data, headers)

        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError or urllib2.URLError, e:
            print e.read()
            
        else:
            print response
            respone.close()


class WSSubscribeHandler(tornado.websocket.WebSocketHandler):
    #TODO: how to get the handler of this web socket?
    
    def on_message(self, message):
        print "Received sub/unsubscribe request from websocket client:"
        params = json.loads(message)
        properties = dict([(str(k.split('hub.')[1]),v) for k,v in params.items()])
        
        # TODO: manage invalid parameters
        # TODO: manage several topics
        
        try:
          # TODO: create subscription if it does not exists already
          
          sub = Subscription(**properties)
          
          # TODO: manage unsubscribe
          
          # TODO: manage sync verification
          if params["hub.verify"].lower() == 'sync':
              pass
              
          else:
            if params["hub.mode"].lower() == 'subscribe':
              # TODO: enque verification task if async and store subscription
              
              print "Sending subscription request to the hubbub"
              self.write_message(u"Sending subscription request to the hubbub")
              
              sub.send_subscribe_request()

        except Exception, e:
            logging.exception(e)
            self.write_message(unicode(e))

    def on_close(self):
        print "web socket closed"


class WSHubHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs): 
        print self.__class__.__mro__
        print "Listening to web socket connections on ws://"
        super(WSHubHandler, self).__init__(application, request, **kwargs)

    def open(self):
        print "WebSocket opened"
        self.write_message(u"web socket opened")

    def on_message(self, message):
        print "Received request from web socket client: %s" % message
        mode = json.loads(message.lower()).get("hub.mode",None)
        if mode == 'publish':
            print "mode publish"
            self.write_message(u"mode publish")
#            handler = WSPublishHandler()   
        elif mode in ('subscribe', 'unsubscribe'):
            print "mode sub/unsubsribe"
            self.write_message(u"mode sub/unsubsribe")
            # TODO: this creates a different socket?
            handler = WSSubscribeHandler(self.application, self.request)
        else:
            print "hub.mode is invalid"
            self.write_message(u"hub.mode is invalid")
            return

        handler.on_message(message)

    def on_close(self):
        print "web socket closed"

def main():
    handlers = [
        (r"/", WSHubHandler),
        (r"/callback", SubscriptionChallengeHandler),
    ]

    application = tornado.web.Application(handlers)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    print "listening on port %s ..." % options.port
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()


