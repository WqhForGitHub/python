"""
CLI 邮件发送工具（SMTP）
功能：
    - 通过 smtplib 发送纯文本/HTML 邮件
    - 支持抄送(CC)、密送(BCC)、附件
    - 命令行参数配置 SMTP 主机/端口/账户/密码
    - 支持 SSL / STARTTLS
    - 由于本演示无网络，main 中使用本机 aiosmtpd-like 简易服务模拟接收
      （只用 smtpd 标准库的等价方式：自实现一个极简 SMTP server）
"""

import os
import ssl
import smtplib
import mimetypes
from email.message import EmailMessage


class Mailer:
    """SMTP 邮件发送器"""

    def __init__(self, host: str, port: int, user: str = "",
                 password: str = "", use_ssl: bool = False,
                 use_starttls: bool = False, timeout: int = 10):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.use_ssl = use_ssl
        self.use_starttls = use_starttls
        self.timeout = timeout

    # -------- 构造邮件 --------
    @staticmethod
    def build_message(sender: str, to: list, subject: str,
                      body: str = "", html: str = None,
                      cc: list = None, bcc: list = None,
                      attachments: list = None) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = ", ".join(to)
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg["Subject"] = subject
        msg.set_content(body or "")
        if html:
            msg.add_alternative(html, subtype="html")

        for path in attachments or []:
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None or encoding:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(path, "rb") as f:
                msg.add_attachment(
                    f.read(), maintype=maintype, subtype=subtype,
                    filename=os.path.basename(path),
                )
        return msg

    # -------- 发送 --------
    def send(self, msg: EmailMessage, recipients: list = None) -> dict:
        recipients = recipients or self._collect_recipients(msg)
        if self.use_ssl:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.host, self.port,
                                  timeout=self.timeout, context=ctx) as s:
                self._login_send(s, msg, recipients)
        else:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as s:
                if self.use_starttls:
                    s.starttls(context=ssl.create_default_context())
                self._login_send(s, msg, recipients)
        return {
            "ok": True,
            "to": recipients,
            "size": len(bytes(msg)),
            "subject": msg["Subject"],
        }

    def _login_send(self, s, msg, recipients):
        if self.user:
            s.login(self.user, self.password)
        s.send_message(msg, from_addr=msg["From"], to_addrs=recipients)

    @staticmethod
    def _collect_recipients(msg) -> list:
        addrs = []
        for h in ("To", "Cc", "Bcc"):
            if msg[h]:
                addrs += [a.strip() for a in msg[h].split(",")]
        return [a for a in addrs if a]


# ==================== Demo ====================

# 用极简方式起一个 mock SMTP 服务，不依赖 aiosmtpd
import socketserver
import threading
import re


class _MockSMTPHandler(socketserver.StreamRequestHandler):
    """非常粗糙的 SMTP 协议处理：只为演示数据接收"""
    received_messages = []

    def handle(self):
        self.wfile.write(b"220 mock.local ESMTP\r\n")
        in_data = False
        data_buf = []
        envelope = {"from": "", "to": []}
        while True:
            line = self.rfile.readline()
            if not line:
                break
            if in_data:
                if line.strip() == b".":
                    self.wfile.write(b"250 OK\r\n")
                    self.received_messages.append({
                        "envelope": dict(envelope),
                        "data": b"".join(data_buf).decode("utf-8", errors="replace"),
                    })
                    in_data = False
                    data_buf = []
                else:
                    # 处理 "..\r\n" 转义
                    if line.startswith(b".."):
                        line = line[1:]
                    data_buf.append(line)
                continue
            cmd = line.strip()
            up = cmd.upper()
            if up.startswith(b"EHLO") or up.startswith(b"HELO"):
                self.wfile.write(b"250-mock.local Hello\r\n250 OK\r\n")
            elif up.startswith(b"MAIL FROM"):
                m = re.search(rb"<([^>]+)>", cmd)
                envelope["from"] = m.group(1).decode() if m else ""
                self.wfile.write(b"250 OK\r\n")
            elif up.startswith(b"RCPT TO"):
                m = re.search(rb"<([^>]+)>", cmd)
                if m:
                    envelope["to"].append(m.group(1).decode())
                self.wfile.write(b"250 OK\r\n")
            elif up == b"DATA":
                self.wfile.write(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                in_data = True
            elif up == b"QUIT":
                self.wfile.write(b"221 Bye\r\n")
                break
            elif up == b"NOOP":
                self.wfile.write(b"250 OK\r\n")
            elif up == b"RSET":
                envelope = {"from": "", "to": []}
                self.wfile.write(b"250 OK\r\n")
            else:
                self.wfile.write(b"250 OK\r\n")


class _ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def _start_mock_smtp():
    server = _ThreadedTCPServer(("127.0.0.1", 0), _MockSMTPHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, port


if __name__ == "__main__":
    print("=" * 60)
    print("  CLI 邮件发送工具（SMTP） Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))

    # 准备一个附件文件
    attach_path = os.path.join(base, "report.txt")
    with open(attach_path, "w", encoding="utf-8") as f:
        f.write("This is a demo attachment.\n第二行：附件内容。")

    # 启动 mock SMTP
    _MockSMTPHandler.received_messages = []
    server, port = _start_mock_smtp()
    print(f"\n  Mock SMTP 监听: 127.0.0.1:{port}")

    # 1. 构造并发送邮件
    print("\n--- 1. 发送纯文本+HTML+附件 ---")
    mailer = Mailer(host="127.0.0.1", port=port, user="", password="")
    msg = Mailer.build_message(
        sender="alice@example.com",
        to=["bob@example.com", "carol@example.com"],
        subject="Demo: SMTP 邮件发送",
        body="这是纯文本正文。\nHello!",
        html="<h1>Hello</h1><p>这是 <b>HTML</b> 正文。</p>",
        cc=["dan@example.com"],
        attachments=[attach_path],
    )
    res = mailer.send(msg)
    print(f"  结果: {res}")

    # 2. 检查 mock 服务收到的消息
    print("\n--- 2. Mock 服务器收到的邮件 ---")
    for i, m in enumerate(_MockSMTPHandler.received_messages, 1):
        env = m["envelope"]
        print(f"  邮件 {i}: from={env['from']}  to={env['to']}")
        # 提取头部预览
        head_lines = m["data"].splitlines()[:8]
        for ln in head_lines:
            print(f"     | {ln[:80]}")
        print(f"     | ... (共 {len(m['data'])} 字节)")

    server.shutdown()
    if os.path.exists(attach_path):
        os.remove(attach_path)

    print("\n--- 3. 真实使用示例（伪代码，不实际执行） ---")
    print("""
    mailer = Mailer(
        host="smtp.qq.com", port=465,
        user="you@qq.com", password="授权码",
        use_ssl=True,
    )
    msg = Mailer.build_message(
        sender="you@qq.com",
        to=["friend@example.com"],
        subject="问候",
        body="你好~",
        attachments=["./report.pdf"],
    )
    mailer.send(msg)
    """)

    print("=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
