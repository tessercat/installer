""" Custom Ansible mailer callback plugin module. """
from __future__ import absolute_import, division, print_function
__metaclass__ = type  # pylint: disable=invalid-name
from email.message import EmailMessage
import smtplib
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """ Mail host admin when playbooks complete. """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'mailer'
    CALLBACK_NEEDS_WHITELIST = False

    _changes = []
    _failures = []
    _notes = []
    _play = None

    def _email_admin(self, subject, body):
        """ Email host admin. """
        hostname = 'unknown'
        admin_email = None
        play_vars = self._play.get_variable_manager().get_vars()
        if hasattr(play_vars, 'get'):
            admin_email = play_vars.get('admin_email')
            hostname = play_vars.get('hostname')
        if not admin_email:
            raise ValueError('No admin email')
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = f'[{hostname}] {subject}'
        msg['From'] = f'<noreply@{hostname}'
        msg['To'] = f'<{admin_email}>'
        print('Send admin mail', admin_email)
        with smtplib.SMTP('localhost') as server:
            server.send_message(msg)

    # Callback overrides.

    def playbook_on_stats(self, stats):
        """ Process playbook results """

        # Set playbook status.
        status = 'complete'
        for host in stats.processed.keys():
            summary = stats.summarize(host)
            if summary['failures'] or summary['unreachable']:
                status = 'failed'
                break

        # Generate email body.
        body = ''
        if self._changes:
            body += '# Changes\n\n'
            body += '\n\n'.join(
                [f'{changed} changed' for changed in self._changes]
            )
        if self._failures:
            if body:
                body += '\n\n'
            body += '# Failures'
            for failure in self._failures:
                body += f'\n\n## {failure[0]} failed\n\n{failure[1]}'
        if self._notes:
            if body:
                body += '\n\n'
            body += '# Notes'
            for note in self._notes:
                body += f'\n\n## {note[0]} stdout\n\n{note[1]}'

        # Send.
        if body:
            self._email_admin(f'{self._play.name} {status}', body)
        else:
            print('No change')

    def v2_playbook_on_play_start(self, play):
        """ Process playbook start events. """
        self._play = play

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """ Process failed task result. """
        # pylint: disable=protected-access

        # Add the task and its failure message to the failures list.
        res = result._result
        if res.get('stderr'):
            message = res['stderr']
        elif res.get('msg'):
            message = res['msg']
        elif res.get('failure'):
            message = res['failure']
        else:
            message = 'Unknown task failure reason.'
        self._failures.append((str(result._task), message))

    def v2_runner_on_ok(self, result):
        """ Process ok task result. """
        # pylint: disable=protected-access

        # Add changed tasks to the changes list.
        if result.is_changed():
            self._changes.append(str(result._task))

            # Add changed admin tasks and their stdout to the notes list.
            if result._task.register == 'admin_email_note':
                self._notes.append((
                    str(result._task),
                    '\n'.join(result._result.get('stdout_lines'))
                ))
