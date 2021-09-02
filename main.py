from re import A
import firebase_admin
from pathlib import Path
import random
from firebase_admin import credentials, auth, firestore
import PySimpleGUI as gui
import datetime

#Save your google credentials in the same folder
cred = credentials.Certificate("credentials.json")
default_app = firebase_admin.initialize_app(cred)
db = firestore.client()

def main():
    win = gui.Window("Ask Salesforce Admin", layout_creator())
    while True:
        event, values = win.read()
        if event == "Exit" or event == gui.WIN_CLOSED:
            break
        elif event == "k_add_users_btn":
            if(values['k_val_deladd_field'] != ""):
                add_user(values['k_val_deladd_field'], win)
            else:
                alert_box("Fill in the requiered spaces")
            #win["k_history_box"].Update([f"Added user {values['k_users_field']}"])
        elif event == "k_delete_users_btn":
            if(values['k_val_deladd_field'] != ""):
                del_users(values['k_val_deladd_field'], win)
            else:
                alert_box("Fill in the requiered spaces")
        elif event == "k_search_btn":
            search_users(values["k_val_search_field"], win)
        elif event == "k_code_btn":
            check_certification(values["k_val_code_field"], values["k_code_cb"], win)

    win.close()
    #show_menu()

def layout_creator():
    add_users = [
        gui.Text("Users/UID/File"),
        gui.In(size=(50,1), enable_events=True, key="k_val_deladd_field"),
        gui.FileBrowse(key="k_users_folder"),
        gui.Button("Add", key="k_add_users_btn"),
        gui.Button("Delete", key="k_delete_users_btn")
        ]
    search_show_users = [
        gui.Text("Searches for given user, if left blank shows all users"),
        gui.In(size=(35,1), enable_events=True, key="k_val_search_field"),
        gui.Button("Search", key="k_search_btn")
    ]
    code_search = [
        gui.Text("Verify certification for given code"),
        gui.In(size=(35,1), enable_events=True, key="k_val_code_field"),
        gui.Button("Verify", key="k_code_btn"),
        gui.Checkbox("Save to computer", default=False, key="k_code_cb")
    ]
    action_history = [
        gui.Listbox(
            values=[], enable_events=True, size = (80,10), key = "k_history_box"
        )
    ]
    
    layout = []
    layout.append([add_users, search_show_users, code_search, action_history])
    return layout
    
def alert_box(alert_text):
    gui.popup(alert_text, title="Alert")

def add_user(text, win):
    if(Path(text).exists() and text.endswith('.txt')):
        #Create users from text file
        file = open(text, 'rt')
        for line in file:
            create_user(line.lstrip().rstrip(), win) #Remove any leading whitespace to not get an error
    elif(Path(text).exists()):
        #File is not .txt raise error
        alert_box("Invalid file")
    elif(text.find('@') != -1):
        #Is mail
        create_user(text.lstrip().rstrip(), win)
    else:
        #Not a valid mail
        alert_box("Invalid mail")

def create_user(mail, win):
    elements_list = win["k_history_box"].get_list_values()
    msg_cur = ""
    try:
        new_user = auth.create_user(
            email = mail,
            password = str(random.randint(111111,999999)),
            disabled = False
        )
        msg_cur = f"Added new email {mail} succesfully"
        auth.generate_password_reset_link(new_user)
    except auth._auth_utils.EmailAlreadyExistsError:
        msg_cur = f"Email already exists {mail}"
    except:
        msg_cur = f"Added new email {mail} succesfully"
    elements_list.append(msg_cur)
    win["k_history_box"].update(elements_list)
    

def delete_users(uid, win):
    elements_list = win["k_history_box"].get_list_values()
    msg_cur = ""
    try:
        auth.delete_user(uid=uid)
        msg_cur = f"Deleted user {uid}"
    except firebase_admin._auth_utils.UserNotFoundError:
        msg_cur =  f"User not found {uid}"
    except:
        msg_cur = f"Error occured while deleting {uid}"
        pass
    elements_list.append(msg_cur)
    win["k_history_box"].update(elements_list)


def del_users(text, win):
    if(Path(text).exists() and text.endswith('.txt')):
        #Delete users from text file
        file = open(text, 'rt')
        for line in file:
            delete_users(line.lstrip().rstrip(), win) #Remove any leading whitespace to not get an error
    elif(Path(text).exists()):
        #File is not .txt raise error
        alert_box("Invalid file")
    else:
        #Might be uid
        delete_users(text.lstrip().rstrip(), win)

def search_users(text, win):
    if(text == ""):
        try:
            page = auth.list_users()
            while page:
                page = page.get_next_page()
            elements_list = win["k_history_box"].get_list_values()
            msg = ""
            for user in auth.list_users().iterate_all():
                ts = float(user.user_metadata.last_sign_in_timestamp)
                ts = ts/1000
                msg = f"Mail: {user.email}, UID: {user.uid}, Last Accesed: {datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')}"
                elements_list.append(msg)
            
            win["k_history_box"].update(elements_list)
        except:
            alert_box(f"Unable to get fetch users")
    elif(text.find('@') != -1):
        try:
            user = auth.get_user_by_email(text)
            elements_list = win["k_history_box"].get_list_values()
            ts = float(user.user_metadata.last_sign_in_timestamp)
            ts = ts/1000
            msg = f"Mail: {user.email}, UID: {user.uid}, Last Accesed: {datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')}"
            elements_list.append(msg)
            win["k_history_box"].update(elements_list)
        except:
            alert_box(f"Unable to get user with mail: {text}")
    else:
        try:
            user = auth.get_user(text)
            elements_list = win["k_history_box"].get_list_values()
            ts = float(user.user_metadata.last_sign_in_timestamp)
            ts = ts/1000
            msg = f"Mail: {user.email}, UID: {user.uid}, Last Accesed: {datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')}"
            elements_list.append(msg)
            win["k_history_box"].update(elements_list)
        except:
            alert_box(f"Unable to get user with UID: {text}")

def check_certification(code, save, win):
    has_one = False
    code = code.upper()
    users_colection = db.collection(u'userScores')
    docs = users_colection.stream()
    file_path = "CertificationScores" + code + ".csv"
    if(save):
        if(Path(file_path).exists()):
            file = open(file_path, "w")
        else:
            file = open(file_path, "x")
        file.write("UID     ,Mail   ,Score,Win,Time to Answer\n")
    elements_list = []
    for doc in docs:
        dict_doc = doc.to_dict()
        if(doc.id.endswith(code) and code != ""):
            has_one = True
            if(dict_doc.get("Win")):
                elements_list.append(f"{dict_doc['Mail']} has certified with a score of {dict_doc['Score']} in {dict_doc['timeFinish'] - dict_doc['timeBegin']}")
            else:
                elements_list.append(f"{dict_doc['Mail']} hasn't certified with a score of {dict_doc['Score']} in {dict_doc['timeFinish'] - dict_doc['timeBegin']}")

            if(save):
                file.write(f"{doc.id.lstrip(code.upper())},{dict_doc['Mail']},{dict_doc['Score']},{dict_doc['Win']}, {dict_doc['timeFinish'] - dict_doc['timeBegin']}\n")
    if(has_one):
        win["k_history_box"].update(elements_list)
    else:
        win["k_history_box"].update([f"No certifications on record for code {code}"])

if __name__ == "__main__":
    main()





