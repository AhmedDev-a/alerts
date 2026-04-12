{
    'name': 'Alerts',
    'version': '1.0',
    'summary': 'Alert Engine for MNF system',
    'description': 'Generates alerts based on SQL queries and sends notifications',
    'author': 'Ahmed Khaled',
    "images": ["static/description/icon.png"],
'license': 'LGPL-3',
    'depends': ['base', 'mail'],

    'data': [
        #  SECURITY
        
        'security/ir.model.access.csv',

        # ⚙️ EXISTING DATA
        'data/cron_job.xml',

        # 🧠 EXISTING VIEW 
        'views/alert_engine_view.xml',

        # 🆕 NEW VIEWS
        
        'views/alert_definition_views.xml',
        'views/alert_config_views.xml',
        'views/menu.xml',
        
    ],




    'assets': {
  'web.assets_backend': [
        'mnf_alerts/static/src/js/notification_handler.js',
    ],
    },
    'installable': True,
    'application': True,
}