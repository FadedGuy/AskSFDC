from os import error
import firebase_admin
from pathlib import Path
import random
from firebase_admin import credentials, auth, firestore
import PySimpleGUI as gui

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
            add_user(values['k_users_field'], win)
            #win["k_history_box"].Update([f"Added user {values['k_users_field']}"])

    win.close()
    #show_menu()

def layout_creator():
    add_users = [
        gui.Text("Add Users"),
        gui.In(size=(50,1), enable_events=True, key="k_users_field"),
        gui.FileBrowse(key="k_users_folder"),
        gui.Button("Add", key="k_add_users_btn")
        ]
    action_history = [
        gui.Listbox(
            values=[], enable_events=True, size = (50,20), key = "k_history_box"
        )
    ]
    layout = []
    layout.append([add_users, action_history])
    return layout
    
def alert_box(alert_text):
    gui.popup(alert_text)

def add_user(text, win):
    if(Path(text).exists() and text.endswith('.txt')):
        #Create users from text file
        print("Create users from file")
        file = open(text, 'rt')
        for line in file:
            create_user(line.lstrip().rstrip(), win) #Remove any leading whitespace to not get an error
    elif(Path(text).exists()):
        #File is not .txt raise error
        alert_box("Invalid file")
    elif(text.find('@') != -1):
        #Is mail
        create_user(text.lstrip().rstrip(), win)
        print("Adding single user")
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
        msg_cur = [f"Added new email {mail} succesfully"]
        print("Added successfully")
        auth.generate_password_reset_link(new_user)
    except auth._auth_utils.EmailAlreadyExistsError:
        msg_cur = [f"Email already exists {mail}"]
        print(f"Email already exists {mail}")
    except:
        msg_cur = [f"Error occured while adding mail {mail}"]
        pass
    elements_list.append(msg_cur)
    win["k_history_box"].update(elements_list)

        
'''
def show_menu():
    menu = {}
    menu['1'] = "Add users"
    menu['2'] = "Delete users"
    menu['3'] = "Show users"
    menu['4'] = "Verify user certification"
    menu['5'] = "Exit"

    while True:
        options = menu.keys()
        print("\n")
        for entry in options:
            print(entry, menu[entry])

        sel = input("Please Select: ")
        print("\n")
        if sel == '1':
            add_user()
        elif sel == '2':
            delete_user()
        elif sel == '3':
            show_users()
        elif sel == '4':
            check_certification()
        elif sel == '5':
            break
        else:
            print("Invalid option")


def add_user():
    opc = input("Enter filePath with emails or email: ")
    if(Path(opc).exists()):
        file = open(opc, "r")
        for line in file:
            create_user(line.lstrip().rstrip())
    else:
        create_user(opc)
        
def create_user(mail):
    try:
        new_user = auth.create_user(
        email = mail,
        password = str(random.randint(1000000, 9999999)),
        disabled = False)
        print('Successfully created new user: {0}'.format(new_user.email))
        auth.generate_password_reset_link(new_user.email)
    except error:
        print('Unable to create account: {0}'.format(mail))


def delete_user():
    opc = input("Enter filePath with UID or UID: ")
    if(Path(opc).exists()):
        file = open(opc, "r")
        for line in file:
            erase_user(line.lstrip().rstrip())
    else:
        erase_user(opc)

def erase_user(id):
    try:
        auth.delete_user(uid=id)
        print('Successfully deleted user: {0}'.format(id))
    except:
        print('Unable to delete user: {0}'.format(id))


def show_users():
    page = auth.list_users()
    while page:
        page = page.get_next_page()

    for user in auth.list_users().iterate_all():
        if(user.user_metadata.last_sign_in_timestamp != None):
            print("User: {0}".format(user.email))
        else:
            print("HAS NOT BEEN ACCESSED User: {0}".format(user.email))


def check_certification():
    code = input("Enter code to verify: ")
    code = code.upper()
    users_colection = db.collection(u'userScores')
    docs = users_colection.stream()
    download_data = False
    file_path = "CertificationScores" + code + ".csv"
    if(input("Want to download the data? Enter 1: ") == "1"):
        download_data = True
        if(Path(file_path).exists()):
            file = open(file_path, "w")
        else:
            file = open(file_path, "x")
        file.write("UID     ,Mail   ,Score,Win,Time to Answer\n")
            
    for doc in docs:
        dict_doc = doc.to_dict()
        if(doc.id.endswith(code)):
            if(dict_doc.get("Win")):
                print(f"{dict_doc['Mail']} has certified with a score of {dict_doc['Score']} in {dict_doc['timeFinish'] - dict_doc['timeBegin']}")
            else:
                print(f"{dict_doc['Mail']} hasn't certified with a score of {dict_doc['Score']} in {dict_doc['timeFinish'] - dict_doc['timeBegin']}")
            if(download_data):
                file.write(f"{doc.id.lstrip(code.upper())},{dict_doc['Mail']},{dict_doc['Score']},{dict_doc['Win']}, {dict_doc['timeFinish'] - dict_doc['timeBegin']}\n")
'''
if __name__ == "__main__":
    main()





