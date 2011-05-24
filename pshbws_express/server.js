// slight modifications to https://github.com/julien51/socket-sub/blob/master/server.js

var fs = require("fs"),
    express = require("express"),
    sys = require("sys"),
    http = require("http"),
    querystring = require("querystring"),
    url = require("url"),
    base64 = require("./deps/base64"),
    ws = require('./deps/node-websocket-server/lib/ws');


var config = JSON.parse(fs.readFileSync("./config.json", "utf8") ) || JSON.parse(fs.readFileSync("./default_config.json", "utf8") );

var log = function(message) {
  if(config.debug) {
    sys.puts(message);
  }
};

//////////////////////////////////////////////////////////////////////////////////////////
//                              Object Definitions                                      //
//////////////////////////////////////////////////////////////////////////////////////////

//
// Feed object
var Feed = function(url) {
  log("Feed, url: "+url);
  this.url = url;
  this.id = base64.encode(url);
  this.callback_url = config.pubsubhubbub.callback_url_root + config.pubsubhubbub.callback_url_path + this.id;
}

//
// Subscription object
var Subscription = function(socket_id, feed ) {
  this.socket_id = socket_id;
  log("Subscription feed: "+feed);
  this.feed = feed; 
};

//
// Subscription store. We may want to persist it later, but right now, it's in memory.
// Which means that the server will probably eat a lot of memory when there are a lot of client connected and/or a lot of feeds susbcribed
var SubscriptionStore = function() {
  this.feeds = {};
  
  //
  // Delete the subscription for this socket id and feed id. If all susbcriptions have been deleted for this socket id, delete the it too.
  this.delete_subscription = function(feed_id, socket_id) {
    var feed = this.feeds[feed_id];
    if(feed) {
      subscription = feed.subscriptions[socket_id];
      if(subscription) {
        delete feed.subscriptions[socket_id];
        if(feed.subscriptions.length == 0) {
          delete this.feeds[feed_id];
        }
        return true
      }
      else {
        if(feed.subscriptions.length == 0) {
          delete this.feeds[feed_id];
        }
        return false
      }
    }
    else {
      return false;
    }
  }

  // 
  // Creates (or just returns) a new subscription for this socket id and this feed url
  this.subscribe = function(socket_id, url) {
    log("this.subscribe, url: "+url);
    var feed = new Feed(url)
    if(!this.feeds[feed.id]) {
      // The feed doesn't exist yet
      this.feeds[feed.id] = {
        subscriptions : {},
        feed: feed
      }
    }
    if(!this.feeds[feed.id].subscriptions[socket_id]) {
      var subscription = new Subscription(socket_id, feed);
      this.feeds[feed.id].subscriptions[socket_id] = subscription;
      return subscription;
    }
    else {
      return this.feeds[feed.id].subscriptions[socket_id];
    }
  }
  
  //
  // Returns the subscription for this socket id and feed id
  this.subscription = function(socket_id, feed_id) {
    var feed = this.feeds[feed_id];
    if(feed) {
      return feed.subscriptions[socket_id];
    }
    else {
      return false;
    }
  }
  
};


//////////////////////////////////////////////////////////////////////////////////////////
//                              PubSubHubbub                                            //
//////////////////////////////////////////////////////////////////////////////////////////


//
// Main PubSubHubub method. Peforms the subscription and unsubscriptions
// It uses the credentials defined earlier.
var subscribe = function(feed, mode, hub, callback, errback) {
  log("Called subscribe");
  var params = {
    "hub.mode"      : mode,
    "hub.verify"    : config.pubsubhubbub.verify_mode,
    "hub.callback"  : feed.callback_url,
    "hub.topic"     : feed.url
  };
  
  var hub_url = hub || config.pubsubhubbub.hub;
  
  var body = querystring.stringify(params)
      hub = url.parse(hub_url),
      contentLength = body.length,
      headers = {
        "Accept": '*/*',
//        "Authorization": "Basic "+ base64.encode(config.pubsubhubbub.username + ":" + config.pubsubhubbub.password),
        "Content-Length": contentLength,
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": hub.hostname,
        "User-Agent": "Socket-Sub for Node.js",
        "Connection": "close"
      };
  log("request body: " + body);
  var client  = http.createClient(hub.port || 80, hub.hostname );
  var request = client.request("POST", hub.pathname + (hub.search || ""), headers);
  log("hub.pathname: " + hub.pathname)
  request.write(body, 'utf8');

  request.addListener("response", function(response) {
    log("in request.addListener response");
    var body = "";
    response.addListener("data", function(chunk) {
        body += chunk;
        log("in request.addListener data");
        log("body: " + body);
    });
    response.addListener('end', function() {
      log("in request.addListener end");
      if(response.statusCode == (202 || 204)) {
        log("response.statusCode: " + response.statusCode);
        callback();
      }
      else {
        errback(body);
      }
    });
  });
  request.end(); // Actually Perform the request
}


//////////////////////////////////////////////////////////////////////////////////////////
//                              Let's get started                                       //
//////////////////////////////////////////////////////////////////////////////////////////

// Web Socket Server ---- (server <-> browser) --------------------------------------
var ws_server = ws.createServer({ debug: config.debug });

ws_server.addListener("listening", function() {
  var hostInfo = config.websocket.listen.host + ":" + config.websocket.listen.port.toString();
  log("Listening to WebSocket connections on ws://" + hostInfo);
});

// Handle Web Sockets when they connect
ws_server.addListener("connection", function(socket ) {
  // When connected
  ws_server.send(socket.id, "Awaiting client message");
  socket.addListener("message", function(json) {
    log("message received: "+json);
    subs = JSON.parse(json);
    
    //if subs["hub.mode"] == 'subscribe'
    
    // When asked to subscribe to a feed_url
    ws_server.send(socket.id, "Subscribing to " + subs["hub.topic"]);
    var subscription = subscriptions_store.subscribe(socket.id, subs["hub.topic"]);
    subscribe(subscription.feed, "subscribe", subs.hub_url, function() {
      ws_server.send(socket.id, "Subscribed to " + subs["hub.topic"]);
      log("Subscribed to " + subscription.feed.url + subs["hub.topic"] + " for " + socket.id);
    }, function(error) {
    ws_server.send(socket.id, "Couldn't subscribe to " + subs["hub.topic"] + " : "+ error.trim() );
      log("Failed subscription to " + subs["hub.topic"] + " for " + socket.id);
    });
    
    //if  subs["hub.mode"] == 'publish'
    //ws_server.send(socket.id, "Subscribing to " + subs["hub.topic"]);
    //var publication = publications_store.subscribe(socket.id, subs["hub.topic"]);
    //publish(publication.feed, "subscribe", subs.hub_url, function() {
    //  ws_server.send(socket.id, "Publicated " + subs["hub.topic"]);
    //  log("Publicated " + subscription.feed.url + subs["hub.topic"] + " for " + socket.id);
    //}, function(error) {
    //ws_server.send(socket.id, "Couldn't publish to " + subs["hub.topic"] + " : "+ error.trim() );
    //  log("Failed publication " + subs["hub.topic"] + " for " + socket.id);
    //});
    
    //if  subs["hub.mode"] == 'unsubscribe'
    
  });
});

// Handle Web Sockets when they disconnect. 
ws_server.addListener("close", function(socket ) {
  // Not much to do.
  //unsubscribe !!
});

// Web Server -------- (server <-> hub) --------------------------------------------
var web_server = express.createServer();

// PubSubHubbub verification of intent
web_server.get(config.pubsubhubbub.callback_url_path + ':feed_id', function(req, res) {
//web_server.get(config.pubsubhubbub.callback_url_path + ':feed_id?hub.challenge?hub.topic=?hub.mode?hub.lease_seconds', function(req, res) {
//web_server.get(config.pubsubhubbub.callback_url_path + ':feed_id?hub.challenge=challenge&hub.topic=topic&hub.mode=mode&hub.lease_seconds=secs', function(req, res) {
    log("in server.get");
    log("req.url"+req.url);
    var challenge = req.url.split("hub.challenge=")[1].split("&")[0];
    log("challenge"+challenge);
    var mode = req.url.split("hub.mode=")[1].split("&")[0];
    log("mode"+mode);
    log("req.method"+req.method);
    log("req.headers.accept"+req.headers.accept);
    log("req.headers.server"+req.headers.server);
    //log("req.params.hub_challenge"+req.params.hub_challenge);
    //log("req.params[hub.challenge]"+req.params['hub.challenge']);
    //log("req.params.hub.challenge"+req.params.hub.challenge);
    var feed = subscriptions_store.feeds[req.params.feed_id];
    log("req.params.feed_id:"+ req.params.feed_id);
    //if (feed && req.query.hub.mode == "subscribe") {
    if (feed && mode == "subscribe") {
      log("Confirmed " + mode + " to " + feed.feed.url )
      res.send(challenge, 200);
      log("Send: " + challenge);
      //notify the publisher about the follower!
    }
    else if (feed && mode == "unsubscribe") {
      // We need to check all the susbcribers. To make sure they're all offline
      var sockets = 0;
      for(subscription_id in feed.subscriptions) {
        subscription = feed_subs.subscriptions[subscription_id];
        ws_server.send(subscription.socket_id, "", function(socket) {
          if(socket) {
            sockets += 1;
          } 
        });
      }
      if(sockets == 0) {
        // We haven't found any socket to send the updates too
        // Let's delete the feed
        log("Confirmed " + mode + " to " + feed.feed.url)
        res.send(challenge, 200);
      }
      else {
        log("Couldn't confirm " + mode + " to " + feed.feed.url)
        res.send(404);
      }
    }
    else {
      log("Couldn't confirm " + mode + " to " + req.params.feed_id)
      res.send(404);
    }
});

//
// Incoming POST notifications.
// Sends the data to the right Socket, based on the subscription. Unsubscibes unused subscriptions.
web_server.post(config.pubsubhubbub.callback_url_path + ':feed_id', function(req, res) {
  log("in server post");
  var feed_subs = subscriptions_store.feeds[req.params.feed_id];
  log("req.params.feed_id " + req.params.feed_id);
  if (feed_subs) {
    req.on('data', function(data) {
      log("in data");
      var sockets = 0;
      for(subscription_id in feed_subs.subscriptions) {
        subscription = feed_subs.subscriptions[subscription_id];
        ws_server.send(subscription.socket_id, data, function(socket) {
          if(socket) {
            sockets += 1;
            log("Sent notification for " + subscription.socket_id + " for " + subscription.feed.url);
            //socket die here: Sent notification for 58010 for http://..

//http.js:542
//    throw new Error("Can't use mutable header APIs after sent.");
//          ^
//Error: Can't use mutable header APIs after sent.
//    at ServerResponse.getHeader (http.js:542:11)
//    at ServerResponse.header (/usr/local/lib/node/.npm/express/2.0.0/package/lib/response.js:226:17)
//    at ServerResponse.send (/usr/local/lib/node/.npm/express/2.0.0/package/lib/response.js:65:17)
//    at IncomingMessage.<anonymous> (/home/duy/socket-sub/server.js:296:13)
//    at IncomingMessage.emit (events.js:64:17)
//    at HTTPParser.onBody (http.js:121:23)
//    at Socket.ondata (http.js:1001:22)
//    at Socket._onReadable (net.js:675:27)
//    at IOWatcher.onReadable [as callback] (net.js:177:10)

          } 
          else {
            log("Looks like " + subscription.socket_id + " is offline! Removing " + subscription.feed.url + " from it");
            //have to subscribe each time socket is not connected! :(
            subscriptions_store.delete_subscription(subscription.feed.id, subscription.socket_id);
          }
        });
      }
      if(sockets == 0) {
        // We haven't found any socket to send the updates too
        // Let's delete the feed
        log("Nobody subscribed to feed " + feed_subs.feed.url)
        subscribe(feed_subs.feed, "unsubscribe", function() {
          log("Unsubscribed from " + feed_subs.feed.url);
          delete subscriptions_store.feeds[req.params.feed_id];
        }, function(error) {
          log("Couldn't unsubscribe from " + feed_subs.feed.url + "(" + error.trim() + ")");
        }) 
        res.send(404);
      }
      else {
        res.send("Thanks", 200);
      }
    });
  }
  else {
    log("Couldn't find feed " + req.params.feed_id)
    res.send(404);
  }
});

web_server.addListener("listening", function() {
  var hostInfo = config.pubsubhubbub.listen.host + ":" + config.pubsubhubbub.listen.port.toString();
  log("Listening to HTTP connections on http://" + hostInfo);
});

web_server.get("/", function(req, res) {
  res.send("<a href='http://github.com/julien51/socket-sub'>Socket Sub</a>", 200);
});

var subscriptions_store = new SubscriptionStore(); 
ws_server.listen(config.websocket.listen.port, config.websocket.listen.host);
web_server.listen(config.pubsubhubbub.listen.port, config.pubsubhubbub.listen.host);

