import email
import smtplib
import ssl

from nanopub_submitter.config import SubmitterConfig
from nanopub_submitter.logger import LOG


class Mailer:
    _instance = None

    def __init__(self):
        self.cfg = None

    @classmethod
    def init(cls, config: SubmitterConfig):
        cls.get().cfg = config

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = Mailer()
        return cls._instance

    def _msg_text(self, nanopub_uri: str):
        return f"Hello,\n" \
               f"new nanopublication has been submitted:\n" \
               f"{nanopub_uri}\n" \
               f"____________________________________________________\n" \
               f"Have a nice day!\n" \
               f"{self.cfg.mail.name}\n"

    def notice(self, nanopub_uri: str):
        if not self.cfg.mail.enabled:
            LOG.debug(f'Notification for {nanopub_uri} skipped'
                      f'(mail disabled)')
            return
        if len(self.cfg.mail.recipients) < 1:
            LOG.debug(f'Notification for {nanopub_uri} skipped'
                      f'(no recipients defined)')
            return
        LOG.info(f'Sending notification for {nanopub_uri}')

        msg = email.message.Message()
        msg['From'] = self.cfg.mail.email
        msg['To'] = ', '.join(self.cfg.mail.recipients)
        msg['Subject'] = f'[{self.cfg.mail.name}] New nanopublication'
        msg.add_header('Content-Type', 'text/plain')
        msg.set_payload(self._msg_text(nanopub_uri))
        try:
            result = self._send(msg)
            LOG.debug(f'Email result: {result}')
        except Exception as e:
            LOG.warn(f'Failed to send notification: {str(e)}')

    def _send(self, message: email.message.Message):
        if self.cfg.mail.security == 'ssl':
            return self._send_smtp_ssl(
                message=message,
            )
        return self._send_smtp(
            message=message,
            use_tls=self.cfg.mail.security == 'starttls',
        )

    def _send_smtp_ssl(self, message: email.message.Message):
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
                host=self.cfg.mail.host,
                port=self.cfg.mail.port,
                context=context,
        ) as server:
            if self.cfg.mail.auth:
                server.login(
                    user=self.cfg.mail.username,
                    password=self.cfg.mail.password,
                )
            return server.send_message(
                msg=message,
                from_addr=self.cfg.mail.email,
                to_addrs=self.cfg.mail.recipients,
            )

    def _send_smtp(self, message: email.message.Message,
                   use_tls: bool):
        context = ssl.create_default_context()
        with smtplib.SMTP(
                host=self.cfg.mail.host,
                port=self.cfg.mail.port,
        ) as server:
            if use_tls:
                server.starttls(context=context)
            if self.cfg.mail.auth:
                server.login(
                    user=self.cfg.mail.username,
                    password=self.cfg.mail.password,
                )
            return server.send_message(
                msg=message,
                from_addr=self.cfg.mail.email,
                to_addrs=self.cfg.mail.recipients,
            )
