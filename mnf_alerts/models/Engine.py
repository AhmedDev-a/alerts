# mnf_alerts/models/engine.py
from odoo import models, fields, api
from datetime import datetime, timedelta
import re  
# Regex has been added to support variable replacement even within parentheses

# =========================================
# Alert Engine Model
# =========================================
class AlertEngine(models.Model):
    _name = 'mnf.alert.engine'
    _description = 'Alert Engine'

   # Essential fields to avoid OWL problems
    name = fields.Char(string='Engine Name', required=True)
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def run_alerts(self):
        AlertConfig = self.env['mnf.alert.config']
        alert_configs = AlertConfig.search([('active', '=', True)])

        notifications = []

        for config in alert_configs:
            # Check the alert duration to avoid repeated sending
            if config.last_send_time:
                delta = datetime.now() - config.last_send_time
                allowed = False
                if config.duration_unit == 'minutes':
                    allowed = delta >= timedelta(minutes=config.duration_value)
                elif config.duration_unit == 'hours':
                    allowed = delta >= timedelta(hours=config.duration_value)
                else:
                    allowed = delta >= timedelta(days=config.duration_value)
                if not allowed:
                    continue

           # Check for valid SQL
            if not config.alert_id or not config.alert_id.sql_statement:
                continue

            try:
               # SQL Execution
                self.env.cr.execute(config.alert_id.sql_statement)
                result = self.env.cr.fetchall()

                if result:
                  # Convert results to a dictionary with column names
                    columns = [desc[0] for desc in self.env.cr.description]
                    rows = [dict(zip(columns, row)) for row in result]

                   # Bring the message template
                    template = config.alert_id.message_template or ""
                    url_template = config.alert_id.url or ""

                    messages = []
                    urls = []

                    for row_data in rows:
                        msg = template
                        url = url_template

                        for key, value in row_data.items():
                            msg = re.sub(r"\(?\{\$" + re.escape(key) + r"\}\)?", str(value or ''), msg)
                            url = re.sub(r"\(?\{\$" + re.escape(key) + r"\}\)?", str(value or ''), url)

                        messages.append(msg)
                        urls.append(url)

                    message_text = "\n".join(messages)
                    final_url = urls[0] if urls else ""

                    #  1. Real-time Web Notification
                    if config.allow_web and config.user_ids:
                        for user in config.user_ids:
                            if user.partner_id:
                                self.env['bus.bus']._sendone(
                                    user.partner_id,
                                    'simple_notification',
                                    {
                                        'title': f'Alert {config.alert_id.alert_code or ""}',
                                        'message': message_text,
                                        'type': 'danger' if config.alert_id.severity=='critical' 
                                                 else 'warning' if config.alert_id.severity=='warning'
                                                 else 'success',  # info
                                        'url': final_url,
                                    }
                                )

                           

                                #  NEW: Activity 
                                self.env['mail.activity'].with_context(
                                    mail_notify=False,       #  prevent email notifications
                                     tracking_disable=True,  # optional: reduce chatter noise
                                     mail_activity_quick_update=True
                                     ).create({
                                    'summary': message_text,
                                    'note': f'{message_text}<br/><a href="{final_url}" target="_blank">Open Record</a>',
                                    'user_id': user.id,
                                    'res_model_id': self.env['ir.model']._get('res.partner').id,
                                    'res_id': user.partner_id.id,
                                })

                   
                   # Add to the notifications list to display in the interface
                    notifications.append({
                        'title': 'Alert',
                        'message': f'Alert Triggered: {config.name}',
                        'type': 'warning',
                        'sticky': False,
                    })

                    # Last updated time of sending
                    config.write({'last_send_time': datetime.now()})

            except Exception as e:
                # Record any error without disabling the system
                self.env['ir.logging'].create({
                    'name': 'AlertEngine SQL Error',
                    'type': 'server',
                    'dbname': self.env.cr.dbname,
                    'level': 'error',
                    'message': str(e),
                    'path': 'mnf.alert.engine',
                    'func': 'run_alerts',
                })

       # Display only the first notification in the Odoo interface
        if notifications:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': notifications[0],
            }

        return True

    # Button to manually enable alerts from the interface
    def button_run_alerts(self):
        return self.run_alerts()


# =========================================
# Alert Config Form
# =========================================
class AlertConfig(models.Model):
    _name = 'mnf.alert.config'
    _description = 'Alert Config'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    alert_id = fields.Many2one('mnf.alert.definition', string='Alert Definition')

   # Add this new field for users
    user_ids = fields.Many2many('res.users', string='Users to Notify')

  # Track the last time the alert was sent
    last_send_time = fields.Datetime(string='Last Send Time')

    #Set the alert duration to avoid repeated sending
    duration_value = fields.Integer(string='Duration Value', default=0)
    duration_unit = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days')
    ], string='Duration Unit', default='minutes')

    allow_web = fields.Boolean(string='Allow Web Notification', default=True)
    allow_email = fields.Boolean(string='Allow Email Notification', default=False)

    # =====================================================
    # =====================================================
    def button_run_alerts(self):
        engine = self.env['mnf.alert.engine'].search([], limit=1)
        if not engine:
            engine = self.env['mnf.alert.engine'].create({'name': 'Default Engine'})
        return engine.run_alerts()