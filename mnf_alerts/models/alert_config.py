from odoo import models, fields

class AlertConfig(models.Model):
    _name = 'mnf.alert.config'
    _description = 'Alert Configuration'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
   # alert_ids = fields.Many2many('mnf.alert.definition', string='Alerts')
    alert_id = fields.Many2one('mnf.alert.definition', required=True)
    def do_something(self):
        alerts = self.env['mnf.alert.definition'].search([])
        for alert in alerts:
            print(alert.alert_code)