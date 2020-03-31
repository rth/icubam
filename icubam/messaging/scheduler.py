from absl import logging
import dataclasses
import datetime
import functools
import time
import tornado.ioloop
from typing import Optional

from icubam.messaging import message
from icubam.www.handlers import update
from icubam.www import updater
from icubam import time_utils


@dataclasses.dataclass
class ScheduledMessage:
  timeout: object = None
  msg: message.Message = None
  when: int = -1


class MessageScheduler:
  """Schedules the sending of SMS to users."""

  def __init__(self, config, db, queue):
    self.config = config
    self.db = db
    self.queue = queue
    self.base_url = self.config.server.base_url
    self.max_retries = self.config.scheduler.max_retries
    self.reminder_delay = self.config.scheduler.reminder_delay
    pings = self.config.scheduler.ping
    self.when = [time_utils.parse_hour(h) for h in pings]

    # Keys: by (user_id, icu_id), value is ScheduledMessage
    self.timeouts = {}
    self.updater = updater.Updater(self.config, None)

  def computes_delay(self, delay=None) -> int:
    """Computes the delay if None."""
    if delay is not None:
      return int(delay)

    if not self.when:
      logging.warning('No ping time. Check config.')
      return -1

    return int(time_utils.get_next_timestamp(self.when) - time.time())

  def schedule_message(
      self, msg: message.Message, delay: Optional[int]) -> bool:
    """Schedules a message to be sent later."""
    delay = self.computes_delay(delay)
    if delay < 0:
      logging.error("Negative delay for scheduling: skipping")
      return False

    when = delay + time.time()
    key = msg.user_id, msg.icu_id
    timeout = self.timeouts.get(key, None)
    if timeout is not None and when > timeout.when:
      logging.info(f'A message is schedule before {when}, Skipping scheduling.')
      return False

    io_loop = tornado.ioloop.IOLoop.current()
    if timeout is not None:
      self.unschedule(msg.user_id, msg.icu_id)

    handle = io_loop.call_later(delay, self.may_send, msg)
    self.timeouts[key] = ScheduledMessage(handle, msg, when)
    logging.info('Scheduling {} in {}s.'.format(msg.icu_name, delay))
    return True

  def schedule(self, user, icu_id: int, delay: Optional[int] = None) -> bool:
    user_icus = {i.icu_id: i for i in user.icus}
    if not user.is_active or icu_id not in user_icus:
      user_id = user.user_id
      logging.info(f'Cannot send message to user {user_id} in icu {icu_id}')
      return

    url = self.updater.get_user_url(user, icu_id)
    msg = message.Message(icu_id, user, url)
    return self.schedule_message(msg, delay)

  def schedule_all(self, delay=None):
    """Schedules messages for all the users."""
    users = self.db.get_users()
    for user in users:
      for icu in user.icus:
        self.schedule(user, icu.icu_id, delay=delay)

  def unschedule(self, user_id: int, icu_id: int):
    timeout = self.timeouts.pop((user_id, icu_id), None)
    if timeout is None:
      logging.info(f'No timeout for user {user_id}')
      return

    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.remove_timeout(timeout.time)
    logging.info(f'Unscheduling message for {user_id} in {icu_id}.')

  async def may_send(self, msg):
    # This message was never sent: send it!
    if msg.first_sent is None:
      return await self.do_send(msg)

    # Otherwise check if it has been answered or sent too many times.
    bed_count = self.db.get_bed_count_for_icu(msg.icu_id)
    last_update = None if bed_count is None else bed_count.last_modified
    uptodate = (last_update is not None) and (last_update > msg.first_sent)
    # The message has been answered or too many tries, send for next session.
    if uptodate or (msg.attempts > self.max_retries):
      msg.reset()
      # This message will be sent again at the next session.
      return self.schedule(msg)
    else:
      await self.do_send(msg)

  async def do_send(self, msg):
    msg.attempts += 1
    if msg.first_sent is None:
      msg.first_sent = time.time()

    logging.info('Sending to {} now ({}/{})'.format(
      msg.icu_name, msg.attempts, self.max_retries + 1))
    if self.queue is not None:
      await self.queue.put(msg)
    self.schedule_message(msg, delay=self.reminder_delay)

  @property
  def messages(self):
    """For debug purpose only"""
    users = self.db.get_users()
    result = []
    for user in users:
      for icu in user.icus:
        url = self.updater.get_user_url(user, icu.icu_id)
        result.append(message.Message(icu.icu_id, user, url))
    return result
