from app.controllers import home,handle_check,get_list_rules, download_report

def register_routes(app):
    app.add_url_rule('/', view_func=home, methods=['GET'])
    app.add_url_rule('/check', view_func=handle_check, methods=['POST'])
    app.add_url_rule('/get-list-rules', view_func=get_list_rules, methods=['POST'])
    app.add_url_rule('/reports/<filename>', view_func=download_report, methods=['GET'])