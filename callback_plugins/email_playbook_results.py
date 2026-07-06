import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from ansible.plugins.callback import CallbackBase  # type: ignore
from ansible.utils.display import Display  # type: ignore

display = Display()


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "email_playbook_results"

    def __init__(self):
        super(CallbackModule, self).__init__()
        # Track per-host results
        self._succeeded: list[str] = []
        self._failed: list[str] = []
        self._failure_reasons: dict[str, str] = {}  # hostname -> reason
        self._generated_on = datetime.now().strftime("%b %d, %Y %I:%M %p")

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #
    def _is_relevant_task(self, task_name: str) -> bool:
        return "Backing up" in task_name or "Gathering" in task_name

    # ------------------------------------------------------------------ #
    #  Event hooks                                                         #
    # ------------------------------------------------------------------ #
    def v2_runner_on_ok(self, result):
        task_name = result._task.get_name()
        hostname = result._host.get_name()

        if self._is_relevant_task(task_name):
            if hostname in self._failed:
                self._failed.remove(hostname)
                self._failure_reasons.pop(hostname, None)
            if hostname not in self._succeeded:
                self._succeeded.append(hostname)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        task_name = result._task.get_name()
        hostname = result._host.get_name()

        if self._is_relevant_task(task_name):
            if hostname in self._succeeded:
                self._succeeded.remove(hostname)
            if hostname not in self._failed:
                self._failed.append(hostname)
            reason = result._result.get("msg", "Task failed during playbook execution")
            self._failure_reasons[hostname] = str(reason)

    def v2_runner_on_unreachable(self, result):
        task_name = result._task.get_name()
        hostname = result._host.get_name()

        if self._is_relevant_task(task_name):
            if hostname in self._succeeded:
                self._succeeded.remove(hostname)
            if hostname not in self._failed:
                self._failed.append(hostname)
            reason = result._result.get("msg", "Host unreachable")
            self._failure_reasons[hostname] = str(reason)

    def v2_playbook_on_stats(self, stats):
        if self._succeeded or self._failed:
            self.send_email()

    # ------------------------------------------------------------------ #
    #  HTML builder                                                        #
    # ------------------------------------------------------------------ #
    def _build_html(self) -> str:
        total = len(set(self._succeeded + self._failed))
        failed_count = len(self._failed)
        succeeded_count = len(self._succeeded)

        # ---- Summary rows ----
        summary_rows = f"""
        <tr><td class="stat-label">Devices scheduled for backup</td><td class="stat-val">{total}</td></tr>
        <tr><td class="stat-label">Devices with backup failure</td><td class="stat-val {"stat-fail" if failed_count else ""}">{failed_count}</td></tr>
        <tr><td class="stat-label">Devices successfully backed up</td><td class="stat-val">{succeeded_count}</td></tr>
        <tr><td class="stat-label">Disabled Devices</td><td class="stat-val">0</td></tr>
        """

        # ---- Failed section ----
        failed_section = ""
        if self._failed:
            failed_rows = "".join(
                f'<tr><td class="device-name">{_esc(h)}</td>'
                f'<td class="failure-reason">{_esc(self._failure_reasons.get(h, "Backup Operation performed during backup schedule execution failed"))}</td></tr>'
                for h in self._failed
            )
            failed_section = f"""
            <div class="section-header section-fail">Backup operation failed for the following device(s)</div>
            <table class="device-table">
              <tbody>{failed_rows}</tbody>
            </table>
            """

        # ---- Succeeded section ----
        ok_section = ""
        if self._succeeded:
            ok_items = "".join(
                f'<div class="device-item">{_esc(h)}</div>'
                for h in self._succeeded
            )
            ok_section = f"""
            <div class="section-header section-neutral">Successfully backed up the following device(s)</div>
            <div class="device-list">{ok_items}</div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NVIDIA Backup Report</title>
<style>
  body {{
    margin: 0;
    padding: 0;
    background: #f0f2f5;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 13px;
    color: #333;
  }}
  .wrapper {{
    max-width: 960px;
    margin: 24px auto;
    background: #fff;
    border: 1px solid #d0d5dd;
    border-radius: 4px;
    overflow: hidden;
  }}

  /* ---- App header ---- */
  .app-header {{
    background: #fff;
    padding: 10px 18px 4px;
    border-bottom: 2px solid #1a73a7;
  }}
  .app-header .vendor {{
    font-size: 11px;
    color: #666;
    margin: 0;
  }}
  .app-header .app-name {{
    font-size: 18px;
    font-weight: 700;
    color: #1a4e6e;
    margin: 0 0 4px;
  }}

  /* ---- Blue title bar ---- */
  .title-bar {{
    background: #1a73a7;
    color: #fff;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.3px;
  }}

  /* ---- Meta strip ---- */
  .meta-strip {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px 32px;
    padding: 10px 18px;
    border-bottom: 1px solid #e0e5eb;
    background: #fafbfc;
    font-size: 12px;
  }}
  .meta-strip span {{ color: #555; }}
  .meta-strip strong {{ color: #222; }}

  /* ---- Stats table ---- */
  .stats-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 0;
  }}
  .stats-table td {{
    padding: 5px 18px;
    border-bottom: 1px solid #eef0f3;
  }}
  .stat-label {{ color: #444; width: 320px; }}
  .stat-val {{
    font-weight: 700;
    color: #222;
    padding-left: 12px;
  }}
  .stat-fail {{ color: #c0392b; }}

  /* ---- Section headers ---- */
  .section-header {{
    padding: 7px 18px;
    font-weight: 600;
    font-size: 12.5px;
    border-top: 1px solid #d0d5dd;
    border-bottom: 1px solid #d0d5dd;
    margin-top: 2px;
  }}
  .section-fail    {{ background: #fce8e8; color: #7b1c1c; }}
  .section-neutral {{ background: #eaf1fb; color: #1a4e6e; }}

  /* ---- Device list (succeeded) ---- */
  .device-list {{ padding: 8px 18px 12px; }}
  .device-item {{
    padding: 3px 0;
    color: #333;
    border-bottom: 1px dotted #e8eaed;
    font-size: 12.5px;
  }}

  /* ---- Failed device table ---- */
  .device-table {{
    width: 100%;
    border-collapse: collapse;
  }}
  .device-table td {{
    padding: 6px 18px;
    border-bottom: 1px solid #fce8e8;
    vertical-align: top;
  }}
  .device-name {{ width: 240px; font-weight: 600; color: #333; }}
  .failure-reason {{ color: #666; font-style: italic; }}

  /* ---- Footer ---- */
  .footer {{
    text-align: center;
    padding: 12px;
    font-size: 11px;
    color: #aaa;
    border-top: 1px solid #e8eaed;
    background: #fafbfc;
  }}
</style>
</head>
<body>
<div class="wrapper">

  <div class="app-header">
    <p class="vendor">Ansible Automation</p>
    <p class="app-name">NVIDIA Backup Report</p>
  </div>

  <div class="title-bar">Configuration Backup Schedule Notification</div>

  <div class="meta-strip">
    <span><strong>Schedule Name :</strong> Daily NVIDIA Backup</span>
    <span><strong>Task Type :</strong> Configuration Backup</span>
    <span><strong>Created By :</strong> ansible</span>
    <span><strong>Generated On :</strong> {self._generated_on}</span>
  </div>

  <table class="stats-table">
    <tbody>{summary_rows}</tbody>
  </table>

  {failed_section}

  {ok_section}

  <div class="footer">
    Generated by Ansible NVIDIA Backup Automation &nbsp;|&nbsp; {self._generated_on}
  </div>
</div>
</body>
</html>"""

    # ------------------------------------------------------------------ #
    #  Email sender                                                        #
    # ------------------------------------------------------------------ #
    def send_email(self):
        html_body = self._build_html()

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Ansible Notification - NVIDIA Backup Automation"
        msg["From"] = "FROM_EMAIL_ADDRESS"

        recipients = [

            "TO_EMAILADDRESS_1",
            "TO_EMAIL_ADDRESS_2",
        ]

        msg["To"] = ", ".join(recipients)

        # Plain-text fallback
        total = len(set(self._succeeded + self._failed))
        plain = (
            f"NVIDIA Backup Report - {self._generated_on}\n"
            f"Devices scheduled : {total}\n"
            f"Failed            : {len(self._failed)}\n"
            f"Succeeded         : {len(self._succeeded)}\n\n"
        )
        if self._failed:
            plain += "FAILED:\n"
            for h in self._failed:
                plain += f"{h}: {self._failure_reasons.get(h, '')}\n"
            plain += "\n"
        if self._succeeded:
            plain += "SUCCEEDED:\n" + "\n".join(self._succeeded) + "\n"

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        smtp_server = "SMTP_IP"
        smtp_port = SMTP_PORT #type: ignore

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.sendmail(msg["From"], recipients, msg.as_string())
                display.display("Email sent successfully.")
        except Exception as e:
            display.display(f"Failed to send email: {e}", stderr=True)


# ------------------------------------------------------------------ #
#  Utility                                                             #
# ------------------------------------------------------------------ #
def _esc(text: str) -> str:
    """HTML-escape a string."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )