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
    gui.Window(title="Ask Salesforce Admin", layout=[[]], margins=(300,300)).read()
    show_menu()

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
if __name__ == "__main__":
    main()





