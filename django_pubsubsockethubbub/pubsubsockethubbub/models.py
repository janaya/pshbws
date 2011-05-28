from datetime import datetime, timedelta
from itertools import groupby
from copy import deepcopy
import hmac
from hashlib import sha1
import random
import logging

from django.db import models
from django.utils.http import urlencode
import httplib2

#from subhub import utils

#class SubscriptionManager(models.Manager):
#    def process(self, log=None):
#        '''
#        Processes all subscriptions for expiration and automatic refreshing.
#        '''
#        utils.lock('subscription')
#        try:
#            if log is None:
#                log = logging.getLogger('subhub.subscription.process')

#            for subscription in self.all():
#                if subscription.expires < datetime.now():
#                    subscription.delete()
#                    log.info('Subscription expired %s' % subscription)
#                elif subscription.expires - datetime.now() < timedelta(seconds=MIN_LEASE):
#                    task, created = SubscriptionTask.objects.get_or_create(
#                        callback = subscription.callback,
#                        topic = subscription.topic,
#                        verify_token = subscription.verify_token,
#                        mode = 'subscribe',
#                        defaults = {
#                            'secret': subscription.secret,
#                        }
#                    )
#                    if created:
#                        log.info('Refresh request for %s' % subscription)
#        finally:
#            utils.unlock('subscription')

#    def process_task(self, task):
#        '''
#        Tries to create a new subscription from a subscription task.
#        The task should already be verified with a subscriber. However such
#        verification only confirms the intent of the subscriber and actual
#        subscription may still fail for different reasons (mostly from checks
#        in parse_atom).
#        '''
#        atom = utils.parse_atom(task.topic)
#        if task.mode == 'subscribe':
#            subscription, created = self.get_or_create(
#                callback = task.callback,
#                topic = atom.link('self'),
#                verify_token = task.verify_token,
#                defaults = {
#                    'secret': task.secret,
#                    'expires': datetime.now(),
#                },
#            )
#            subscription.expires = datetime.now() + timedelta(seconds=task.lease_seconds)
#            subscription.save()
#        else:
#            self.filter(callback=task.callback, topic=atom.link('self')).delete()

class Subscription(models.Model):
    '''
    Live verified subscription.
    '''
    callback = models.URLField()
    topic = models.URLField()
    expires = models.DateTimeField()
    verify_token = models.CharField(max_length=1024, blank=True)
    secret = models.CharField(max_length=1024, blank=True)

#    objects = SubscriptionManager()

    class Meta:
        unique_together = [
            ('callback', 'topic', 'verify_token'),
        ]

    def __unicode__(self):
        return u'(%s, %s)' % (self.callback, self.topic)

MODES = [
    ('subscribe', 'Subscribe'),
    ('unsubscribe', 'Unsubscribe'),
]

MIN_LEASE = 86400
MAX_LEASE = 365 * 86400


#class SubscriptionTaskManager(models.Manager):
#    def process(self, log=None):
#        '''
#        Verifies all tasks in queue.
#        '''
#        utils.lock('subscriptiontask')
#        try:
#            if log is None:
#                log = logging.getLogger('subhub.subscriptiontask.process')

#            for task in self.all():
#                result, description = task.verify()
#                if result:
#                    log.info('%s: %s' % (task, description))
#                else:
#                    log.error('%s (ttl=%s): %s' % (task, task.ttl, description))
#        finally:
#            utils.unlock('subscriptiontask')


#class SubscriptionTask(models.Model):
#    '''
#    Unverified task for creating a subscription.
#    '''
#    callback = models.URLField()
#    topic = models.URLField()
#    verify_token = models.CharField(max_length=1024, blank=True)
#    mode = models.CharField(max_length=20, choices=MODES)
#    lease_seconds = models.IntegerField(default=MAX_LEASE)
#    secret = models.CharField(max_length=1024, blank=True)
#    ttl = models.IntegerField(default=5)

#    objects = SubscriptionTaskManager()

#    class Meta:
#        ordering = ['id']
#        unique_together = [
#            ('callback', 'topic', 'verify_token', 'mode'),
#        ]

#    def __unicode__(self):
#        return u'(%s, %s, %s)' % (self.mode, self.callback, self.topic)

#    def save(self, *args, **kwargs):
#        self.lease_seconds = min(MAX_LEASE, max(MIN_LEASE, self.lease_seconds))
#        return super(SubscriptionTask, self).save(*args, **kwargs)

#    def verify(self):
#        '''
#        Verifies subscription request by querying the subscriber.

#        Returns a pair (result, description) where:

#        - result: True if verification yielded definitive result, either
#          successful or not. False if verification process has failed and will
#          be retried until retry attempts are exhausted. Retry attempts are
#          stored in self.ttl.

#        - description: extended description of result. If result is True it can
#          be 'verified' of 'cancelled'. If result is False it's an error
#          message.
#        '''
#        challenge = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(40))
#        params = {
#            'hub.mode': self.mode,
#            'hub.topic': self.topic,
#            'hub.challenge': challenge,
#            'hub.lease_seconds': self.lease_seconds,
#        }
#        if self.verify_token:
#            params['hub.verify_token'] = self.verify_token
#        join = '&' if '?' in self.callback else '?'
#        url = '%s%s%s' % (self.callback, join, urlencode(params))
#        h = httplib2.Http(timeout=utils.HTTP_TIMEOUT)
#        try:
#            response, body = h.request(url, 'GET')
#            if (200 <= response.status < 300) and body == challenge:
#                Subscription.objects.process_task(self)
#                self.delete()
#                return True, 'verified'
#            elif response.status == 404 or \
#                ((200 <= response.status < 300) and body != challenge):
#                self.delete()
#                if self.mode == 'subscribe':
#                    # cleanup subscriptions that could be active if this is
#                    # an auto-refresh task
#                    Subscription.objects.filter(
#                        topic = self.topic,
#                        callback = self.callback,
#                        verify_token = self.verify_token,
#                    ).delete()
#                return True, 'cancelled'
#            else:
#                error = '%s: %s' % (response.status, body.replace('\n', ' '))
#        except utils.HTTP_ERRORS + utils.FEED_ERRORS, e:
#            error = '%s, %s' % (e.__class__.__name__, e)
#        self.ttl -= 1
#        if self.ttl:
#            self.save()
#        else:
#            self.delete()
#        return False, error

#    def ws_verify(self):
#        '''
#        Verifies subscription request by querying the subscriber.

#        Returns a pair (result, description) where:

#        - result: True if verification yielded definitive result, either
#          successful or not. False if verification process has failed and will
#          be retried until retry attempts are exhausted. Retry attempts are
#          stored in self.ttl.

#        - description: extended description of result. If result is True it can
#          be 'verified' of 'cancelled'. If result is False it's an error
#          message.
#        '''
#        challenge = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(40))
#        params = {
#            'hub.mode': self.mode,
#            'hub.topic': self.topic,
#            'hub.challenge': challenge,
#            'hub.lease_seconds': self.lease_seconds,
#        }
#        if self.verify_token:
#            params['hub.verify_token'] = self.verify_token
#        join = '&' if '?' in self.callback else '?'
#        url = '%s%s%s' % (self.callback, join, urlencode(params))
#        h = httplib2.Http(timeout=utils.HTTP_TIMEOUT)
#        try:
#            response, body = h.request(url, 'GET')
#            
#            
#            
#            if (200 <= response.status < 300) and body == challenge:
#                Subscription.objects.process_task(self)
#                self.delete()
#                return True, 'verified'
#            elif response.status == 404 or \
#                ((200 <= response.status < 300) and body != challenge):
#                self.delete()
#                if self.mode == 'subscribe':
#                    # cleanup subscriptions that could be active if this is
#                    # an auto-refresh task
#                    Subscription.objects.filter(
#                        topic = self.topic,
#                        callback = self.callback,
#                        verify_token = self.verify_token,
#                    ).delete()
#                return True, 'cancelled'
#            else:
#                error = '%s: %s' % (response.status, body.replace('\n', ' '))
#        except utils.HTTP_ERRORS + utils.FEED_ERRORS, e:
#            error = '%s, %s' % (e.__class__.__name__, e)
#        self.ttl -= 1
#        if self.ttl:
#            self.save()
#        else:
#            self.delete()
#        return False, error

#class DistributionTaskManager(models.Manager):
#    def add(self, topic, entry_id):
#        '''
#        Adds a task for distributing content for all subscribers of the topic.
#        '''
#        for subscription in Subscription.objects.filter(topic=topic):
#            self.get_or_create(
#                subscription = subscription,
#                entry_id = entry_id,
#            )

#    def process(self, log=None):
#        '''
#        Processes all content distribution tasks grouped by subscriptions (i.e.
#        a single topic for a single callback). A subscription may receive one
#        or more accumulated entries.
#        '''
#        utils.lock('distribution')
#        try:
#            if log is None:
#                log = logging.getLogger('subhub.distribution.process')

#            qs = self.get_query_set().select_related('subscription').order_by('subscription')
#            feed_cache = {}

#            def filter_feed(url, tasks):
#                ids = set(t.entry_id for t in tasks)
#                feed = deepcopy(utils.parse_atom(url, cache=feed_cache))
#                for element in feed.root.findall('entry'):
#                    if element.find('id').text not in ids:
#                        feed.root.remove(element)
#                return feed

#            groups = groupby(qs, lambda t: t.subscription)
#            updates = ((s, filter_feed(s.topic, tasks)) for s, tasks in groups)

#            def process_update(subscription, feed):
#                if not feed.root.findall('entry'):
#                    return True
#                body = str(feed)
#                h = httplib2.Http(timeout=utils.HTTP_TIMEOUT)
#                headers = {
#                    'Content-type': 'application/atom+xml; charset=utf-8',
#                    'Content-length': str(len(body)),
#                }
#                if subscription.secret:
#                    signature = hmac.new(subscription.secret.encode('utf-8'), body, sha1).hexdigest()
#                    headers['X-Hub-Signature'] = 'sha1=%s' % signature
#                try:
#                    response, body = h.request(subscription.callback, 'POST',
#                        headers = headers,
#                        body = body,
#                    )
#                    if 200 <= response.status < 300:
#                        sent_ids = [id.text for id in feed.root.findall('entry/id')]
#                        log.info('%s (%s)' % (subscription, ', '.join(sent_ids)))
#                        return True
#                    else:
#                        log.error('%s: HTTP Error %s' % (subscription, response.status))
#                except utils.HTTP_ERRORS, e:
#                    log.error('%s: %s' % (subscription, e))
#                return False

#            results = utils.pool(process_update, updates)
#            for result, (subscription, feed) in results:
#                if result:
#                    self.filter(subscription=subscription).delete()
#        finally:
#            utils.unlock('distribution')

#class DistributionTask(models.Model):
#    '''
#    Task for pushing a particular entry to a subscriber.
#    '''
#    subscription = models.ForeignKey(Subscription)
#    entry_id = models.CharField(max_length=1024)

#    objects = DistributionTaskManager()

#    class Meta:
#        unique_together = [
#            ('subscription', 'entry_id'),
#        ]
