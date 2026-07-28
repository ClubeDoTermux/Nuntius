import asyncio
import email
import imaplib
import logging
import smtplib
from email.header import decode_header
from email.mime.text import MIMEText

from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo

logger = logging.getLogger("nuntius.platforms.email")


class EmailBot(PlatformBase):
    info = PlatformInfo(
        name="email",
        description="Email bidirecional via IMAP + SMTP",
        config_schema={
            "imap_server": {"type": "string", "description": "Servidor IMAP (ex: imap.gmail.com)", "required": True},
            "smtp_server": {"type": "string", "description": "Servidor SMTP (ex: smtp.gmail.com)", "required": True},
            "email": {"type": "string", "description": "Endereco de email do bot", "required": True},
            "password": {"type": "string", "description": "Senha ou app password", "required": True},
            "imap_port": {"type": "integer", "description": "Porta IMAP (default: 993)", "required": False},
            "smtp_port": {"type": "integer", "description": "Porta SMTP (default: 587)", "required": False},
            "poll_interval": {"type": "integer", "description": "Intervalo de verificacao em segundos (default: 60)", "required": False},
        },
        extra_help="Use uma senha de app para Gmail. Configure IMAP em Configuracoes > Encaminhamento e POP/IMAP.",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)

    async def start(self):
        cfg = self.config
        self.imap_server = cfg.get("imap_server", "")
        self.smtp_server = cfg.get("smtp_server", "")
        self.email_addr = cfg.get("email", "")
        self.password = cfg.get("password", "")
        self.imap_port = cfg.get("imap_port", 993)
        self.smtp_port = cfg.get("smtp_port", 587)
        self.poll_interval = cfg.get("poll_interval", 60)

        if not all([self.imap_server, self.smtp_server, self.email_addr, self.password]):
            print("Email: configuracoes incompletas.")
            return

        self._running = True
        print(f"Email bot rodando (verificando {self.email_addr} a cada {self.poll_interval}s)...")
        while self._running:
            try:
                await self._check_inbox()
            except Exception as e:
                logger.warning(f"Erro ao verificar emails: {e}")
            await asyncio.sleep(self.poll_interval)

    async def _check_inbox(self):
        def _sync_check():
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_addr, self.password)
            mail.select("INBOX")
            status, ids = mail.search(None, "UNSEEN")
            if status != "OK":
                mail.logout()
                return []
            results = []
            for msg_id in ids[0].split() if ids[0] else []:
                status, data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                raw = data[0][1]
                parsed = email.message_from_bytes(raw)
                subject, encoding = decode_header(parsed["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="replace")
                from_addr = parsed.get("From", "")
                body = ""
                if parsed.is_multipart():
                    for part in parsed.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                            break
                else:
                    body = parsed.get_payload(decode=True).decode("utf-8", errors="replace")
                results.append((msg_id, from_addr, subject, body))
                mail.store(msg_id, "+FLAGS", "\\Seen")
            mail.logout()
            return results

        emails = await asyncio.to_thread(_sync_check)
        for msg_id, from_addr, subject, body in emails:
            msg_obj = IncomingMessage(
                text=body.strip() or subject,
                user_id=from_addr,
                user_name=from_addr,
                platform="email",
                chat_id=from_addr,
            )
            result = await self.agent.chat(msg_obj.text)
            await self._send_email(from_addr, subject, result)

    async def _send_email(self, to: str, subject: str, body: str):
        def _sync_send():
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = f"Re: {subject}"
            msg["From"] = self.email_addr
            msg["To"] = to
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_addr, self.password)
                server.send_message(msg)

        await asyncio.to_thread(_sync_send)

    async def send_message(self, message: OutgoingMessage) -> bool:
        try:
            await self._send_email(message.chat_id, "Nuntius", message.text)
            return True
        except Exception:
            return False


register(EmailBot)
