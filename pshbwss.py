import sys
sys.path.append('google')

from tornado.options import define, options
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
#import tornado.wsgi
import wsgiref.handlers

import json
import logging
import urllib2
import urllib

from google.appengine.ext import db

logging.basicConfig(level=logging.DEBUG)
define("port", default=8081, help="run on the given port", type=int)

# Default expiration time of a lease.
DEFAULT_LEASE_SECONDS = (5 * 24 * 60 * 60)  # 5 days

class WSSubscriptionChallengeHandler(tornado.websocket.RequestHandler):
    

    def on_message():
        pass

class SubscriptionChallengeHandler(tornado.web.RequestHandler):
    def get(self):
        pass
      
class Subscription(db.Model):
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
    def store(self):
      pass

    def send_subscribe_request(self):
        hub_url = 'http://pubsubhubbub.appspot.com/publish'
#        headers = {
#          "Accept": '*/*',
#  #        "Authorization": "Basic "+ base64.encode(config.pubsubhubbub.username + ":" + config.pubsubhubbub.password),
#          "Content-Length": contentLength,
#          "Content-Type": "application/x-www-form-urlencoded",
#          "Host": hub.hostname,
#          "User-Agent": "pshbwss",
#          "Connection": "close"
#        }

        params = {
            'hub.mode': self.mode,
            'hub.callback': self.callback,
            'hub.topic': self.topic,
        }
        data = urllib.urlencode(params)
        logging.debug(data)
        request = urllib2.Request(hub_url)
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        request.add_data(data)

        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            logging.debug(e)
            logging.debug(e.code)
            logging.debug(e.read())
            
        else:
            page = response.read()
            response.close()
            logging.debug(page)


class WSSubscribeHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs): 
        print self.__class__.__mro__
        logging.debug("Subscribing to..." )
        super(WSSubscribeHandler, self).__init__(application, request, **kwargs)

    def on_message(self, message):
        logging.debug("on wssubscriber handler message")
        params = json.loads(message)
        properties = dict([(k.split('hub.')[1],v) for k,v in params.items()])
        logging.debug(params)
        
#        callback = message_dict.get("hub.callback", None)
#        topic = message_dict.get("hub.topic", None)
#        mode = message_dict.get("hub.mode", None) 
#        verify_type = message_dict.get("hub.verify", None) 
#        verify_token = message_dict.get("verify_token", None)
#        secret = message_dict.get("secret", None)
#        lease_seconds = message_dict.get("lease_seconds", str(DEFAULT_LEASE_SECONDS))

    #    error_message = None
    #    if not callback or not is_valid_url(callback):
    #      error_message = ('Invalid parameter: hub.callback; '
    #                       'must be valid URI with no fragment and '
    #                       'optional port %s' % ','.join(VALID_PORTS))
    #    else:
    #      callback = normalize_iri(callback)

    #    if not topic or not is_valid_url(topic):
    #      error_message = ('Invalid parameter: hub.topic; '
    #                       'must be valid URI with no fragment and '
    #                       'optional port %s' % ','.join(VALID_PORTS))
    #    else:
    #      topic = normalize_iri(topic)

#        enabled_types = [vt for vt in verify_type_list if vt in ('async', 'sync')]
#        if not enabled_types:
#          error_message = 'Invalid values for hub.verify: %s' % (verify_type_list,)
#          logging.debug(error_message)
#          self.write_message(unicode(error_message))
#        else:
#          verify_type = enabled_types[0]

    #    if mode not in ('subscribe', 'unsubscribe'):
    #      error_message = 'Invalid value for hub.mode: %s' % mode

    #    if lease_seconds:
    #      try:
    #        old_lease_seconds = lease_seconds
    #        lease_seconds = int(old_lease_seconds)
    #        if not old_lease_seconds == str(lease_seconds):
    #          raise ValueError
    #      except ValueError:
    #        error_message = ('Invalid value for hub.lease_seconds: %s' %
    #                         old_lease_seconds)

    #    if error_message:
    #      logging.debugging.debug('Bad request for mode = %s, topic = %s, '
    #                    'callback = %s, verify_token = %s, lease_seconds = %s: %s',
    #                    mode, topic, callback, verify_token,
    #                    lease_seconds, error_message)
    #      self.write_message(error_message)
    #      return 400

        try:
    #      # Retrieve any existing subscription for this callback.
    #      sub = Subscription.get_by_key_name(
    #          Subscription.create_key_name(callback, topic))
    
          sub = Subscription(**properties)

    #      # Deletions for non-existant subscriptions will be ignored.
    #      if mode == 'unsubscribe' and not sub:
    #        return self.response.set_status(204)

    #      # Enqueue a background verification task, or immediately confirm.
    #      # We prefer synchronous confirmation.
    
          if params["hub.verify"].lower() == 'sync':
    #        if hooks.execute(confirm_subscription,
    #              mode, topic, callback, verify_token, secret, lease_seconds):
    #          return self.response.set_status(204)
    #        else:
    #          self.write_message('Error trying to confirm subscription')
    #          return self.response.set_status(409)
              pass
              
          else:
            if params["hub.mode"].lower() == 'subscribe':
    #          Subscription.request_insert(callback, topic, verify_token, secret,
    #                                      lease_seconds=lease_seconds)
              # sub.store
              logging.debug("Going to ask subs")
              self.write_message(u"Going to ask subs")
              
              sub.send_subscribe_request()

    #        else:
    #          Subscription.request_remove(callback, topic, verify_token)
    #        logging.debugging.debug('Queued %s request for callback = %s, '
    #                      'topic = %s, verify_token = "%s", lease_seconds= %s',
    #                      mode, callback, topic, verify_token, lease_seconds)
    #        return self.response.set_status(202)

    #    except (apiproxy_errors.Error, db.Error,
    #            runtime.DeadlineExceededError, taskqueue.Error):
        except Exception, e:
            logging.exception(e)
            self.write_message(unicode(e))
            
    #      self.response.headers['Retry-After'] = '120'
    #      return self.response.set_status(503) 


class WSHubHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs): 
        print self.__class__.__mro__
        logging.debug("Listening to WebSocket connections on ws://" )
#        logging.debug(self.socket)
        super(WSHubHandler, self).__init__(application, request, **kwargs)

    def open(self):
#        logging.debug(self.socket)
        logging.debug("WebSocket opened" )
        self.write_message(u"Awaiting feed subscription request")

    def on_message(self, message):
        logging.debug("Received %s" % message)
        mode = json.loads(message.lower()).get("hub.mode",None)
        if mode == 'publish':
            logging.debug("mode publish" )
            self.write_message(u"mode publish")
#            handler = WSPublishHandler()   
        elif mode in ('subscribe', 'unsubscribe'):
            logging.debug("mode sub/unsubsribe" )
            self.write_message(u"mode sub/unsubsribe")
            handler = WSSubscribeHandler(self.application, self.request)
        else:
            logging.debug("hub.mode is invalid" )
            self.write_message(u"hub.mode is invalid")
            return

#        handler.initialize(self.request, self.response)
        handler.on_message(message)

    def on_close(self):
        print "WebSocket closed"

def main():
    handlers = [
        (r"/", WSHubHandler),
    ]
    print handlers

    application = tornado.web.Application(handlers)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    print "listening on port %s ..." % options.port
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()


