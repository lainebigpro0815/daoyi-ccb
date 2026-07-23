"""邮件发送服务"""
import json, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

CONFIG_FILE = Path(__file__).parent.parent.parent / "data" / "email_config.json"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "smtp_host": "",
        "smtp_port": 465,
        "smtp_user": "",
        "smtp_pass": "",
        "sender_name": "CCB项目管理系统",
        "use_ssl": True,
    }


def save_config(data: dict) -> dict:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "saved"}


def get_config() -> dict:
    cfg = _load_config()
    # 不返回密码
    return {k: v for k, v in cfg.items() if k != "smtp_pass"}


def send_email(to_addrs: list[str], subject: str, body: str) -> dict:
    """发送邮件，返回 {success, message}"""
    cfg = _load_config()
    if not cfg.get("smtp_host") or not cfg.get("smtp_user") or not cfg.get("smtp_pass"):
        return {"success": False, "message": "SMTP 未配置"}

    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = f"{cfg['sender_name']} <{cfg['smtp_user']}>"
    msg['To'] = ', '.join(to_addrs)
    import html as pyhtml
    safe_body = pyhtml.escape(body)
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    msg.attach(MIMEText(safe_body.replace('\n', '<br>\n'), 'html', 'utf-8'))

    try:
        if cfg.get("use_ssl", True):
            server = smtplib.SMTP_SSL(cfg["smtp_host"], int(cfg["smtp_port"]))
        else:
            server = smtplib.SMTP(cfg["smtp_host"], int(cfg["smtp_port"]))
            server.starttls()

        server.login(cfg["smtp_user"], cfg["smtp_pass"])
        server.sendmail(cfg["smtp_user"], to_addrs, msg.as_string())
        server.quit()
        return {"success": True, "message": "发送成功"}
    except Exception as e:
        return {"success": False, "message": str(e)}
