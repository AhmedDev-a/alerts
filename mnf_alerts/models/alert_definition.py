from odoo import models, fields, api
from odoo.exceptions import UserError


class AlertDefinition(models.Model):
    _name = 'mnf.alert.definition'
    _description = 'Alert Definition'

    # Alert Code
    alert_code = fields.Char(required=True)

    # SQL that determines when the alert is triggered
    sql_statement = fields.Text(string="SQL Statement")

    # Risk level
    severity = fields.Selection([
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical')
    ], default='info')

    # Link (optional)
    url = fields.Char(string="URL Template")

    # Dynamic message template
    message_template = fields.Text(
        string="Message Template",
        help="Use variables like {$column_name} to display SQL results dynamically"
    )

    
    def action_test_query(self):
        self.ensure_one()

        # Protection: Only allow SELECT
        if not self.sql_statement:
            raise UserError("SQL is empty")

        if not self.sql_statement.lower().strip().startswith("select"):
            raise UserError("Only SELECT queries are allowed!")

        try:
           # Execute the query
            self.env.cr.execute(self.sql_statement)
            result = self.env.cr.fetchall()

            # Column names
            columns = [desc[0] for desc in self.env.cr.description]

            preview_messages = []

            for row in result:
                row_data = dict(zip(columns, row))
                msg = self.message_template or ""

                # Replacing variables
                for key, value in row_data.items():
                    msg = msg.replace(f'{{$%s}}' % key, str(value or ''))

                preview_messages.append(msg)

           # Offer for the first 5 only
            final_preview = "\n".join(preview_messages[:5]) or "No data returned"

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': f'Preview: {self.alert_code}',
                    'message': final_preview,
                    'type': 'info',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise UserError(f"SQL Error: {str(e)}")
