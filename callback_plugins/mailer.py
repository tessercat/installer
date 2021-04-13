""" Custom Ansible mailer callback plugin module. """
from __future__ import absolute_import, division, print_function
__metaclass__ = type  # pylint: disable=invalid-name
from email.message import EmailMessage
import smtplib
from pprint import pformat
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """ Mail host admin when playbooks complete. """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'mailer'
    CALLBACK_NEEDS_WHITELIST = False

    _failures = []
    _play = None
    _tasks = {}  # Maps hosts to tasks / task status.

    def _email_admin(self, subject, body):
        """ Email host admin. """
        hostname = 'unknown'
        admin_email = None
        play_vars = self._play.get_variable_manager().get_vars()
        if hasattr(play_vars, 'get'):
            admin_email = play_vars.get('admin_email')
            hostname = play_vars.get('hostname')
        if not admin_email:
            raise Exception('No admin email')
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = '[%s] %s' % (hostname, subject)
        msg['From'] = '<noreply@%s>' % hostname
        msg['To'] = '<%s>' % admin_email
        print('Send admin mail', admin_email)
        with smtplib.SMTP('localhost') as server:
            server.send_message(msg)

    def _update_tasks(self, task):
        """ Update the host-to-tasks dict. """
        hostvars = task.get_variable_manager().get_vars()['hostvars']
        for host, _ in hostvars.items():
            if not self._tasks.get(host):
                self._tasks[host] = []
            self._tasks[host].append([task, ""])

    # Callback overrides.

    def playbook_on_stats(self, stats):
        """ Process playbook stats event for all hosts. """

        # Send admin email on change or failure.
        if self._failures:
            send_admin_email = True
        else:
            send_admin_email = False

        # Set playbook status to complete or failed.
        status = 'complete'
        for host in stats.processed.keys():
            summary = stats.summarize(host)
            if summary['failures'] or summary['unreachable']:
                status = 'failed'
                break

        # Generate a per-host dict of tasks with non-empty status.
        tasklist = {}
        for host, tasks in self._tasks.items():
            tasklist[host] = []
            for task in tasks:
                if task[1]:
                    send_admin_email = True
                    tasklist[host].append(task)

        # Send admin mail.
        if send_admin_email:
            body = 'Playbook tasks:\n\n%s' % pformat(tasklist)
            if self._failures:
                body += '\n\n%s' % '\n\n'.join(self._failures)
            self._email_admin('%s %s' % (self._play.name, status), body)
        else:
            print('No change')

    def runner_on_failed(self, host, res, ignore_errors=False):
        """ Process failed task result. """

        # Set status for failed tasks.
        if self._tasks.get(host):
            self._tasks[host][-1][1] = 'failed'
        else:
            self._email_admin(
                'Missing host for failed task', '%s\n\n%s' % (host, res)
            )

        # Append the failure reason to the failures list.
        if res.get('stderr'):
            message = res['stderr']
        elif res.get('msg'):
            message = res['msg']
        elif res.get('failure'):
            message = res['failure']
        else:
            message = 'Unknown task failure reason.'
        self._failures.append('%s: %s' % (host, message))

    def runner_on_ok(self, host, res):
        """ Process ok task result. """

        # Set status for changed tasks, leave empty for others.
        if res.get('changed'):
            if self._tasks.get(host):
                self._tasks[host][-1][1] = 'changed'
            else:
                self._email_admin(
                    'Missing host for OK task', '%s\n\n%s' % (host, res)
                )

    def v2_playbook_on_play_start(self, play):
        """ Process playbook start events. """
        self._play = play

    def v2_playbook_on_handler_task_start(self, task):
        """ Process handler start events. """
        self._update_tasks(task)

    def v2_playbook_on_task_start(self, task, is_conditional):
        """ Process task start events. """
        self._update_tasks(task)
