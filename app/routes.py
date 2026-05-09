# from app.controllers import home, handle_check, get_list_rules, download_report, set_session, get_session, get_vars_options, add_rulle, get_user_rulles, del_user_rulle 
from app.controllers import home, handle_check, get_list_rules, download_report
from app.controllers import get_vars_options, add_rulle, get_user_rulles, del_user_rulle 
from app.controllers import get_one_user_rulle, update_user_rulle 

def register_routes(app):
    app.add_url_rule('/', view_func=home, methods=['GET'])
    app.add_url_rule('/check', view_func=handle_check, methods=['POST'])
    app.add_url_rule('/get-list-rules', view_func=get_list_rules, methods=['POST'])
    app.add_url_rule('/reports/<filename>', view_func=download_report, methods=['GET'])
    app.add_url_rule('/get-vars-options', view_func=get_vars_options, methods=['POST'])
    app.add_url_rule('/add-rulle', view_func=add_rulle, methods=['POST'])
    app.add_url_rule('/get-user-rulles', view_func=get_user_rulles, methods=['POST'])
    app.add_url_rule('/del-user-rulle', view_func=del_user_rulle, methods=['POST'])
    app.add_url_rule('/update-user-rulle', view_func=update_user_rulle, methods=['POST'])
    app.add_url_rule('/get-one-user-rulle', view_func=get_one_user_rulle, methods=['POST'])