import firebase_admin
from pathlib import Path
import random
from firebase_admin import credentials, auth, firestore, storage
import google.auth
from google.cloud import storage as storGC
import PySimpleGUI as gui
import datetime
import subprocess

###########################
# CONSTANTS
INPUT_BOX_SIZE = (20,1)
LISTBOX_SIZE = (70,10)
ENCRYPT_FILE_PATH = "./EncryptFile.exe"
UNECRYPT_FILE_PATH = "./DecryptFile.exe"
CREDENTIALS_PATH = "credentials.json"
CREDENTIAL_CERTIFICATE = credentials.Certificate(CREDENTIALS_PATH) #check if path exists
DEFAULT_APP = firebase_admin.initialize_app(CREDENTIAL_CERTIFICATE, {
    'storageBucket' : 'unityloteria.appspot.com'
})
DB = firestore.client() #check_certificate()
###########################

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
                show_alert("Fill in the requiered spaces")
            #win["k_history_box"].Update([f"Added user {values['k_users_field']}"])
        elif event == "k_delete_users_btn":
            if(values['k_val_deladd_field'] != ""):
                del_users(values['k_val_deladd_field'], win)
            else:
                show_alert("Fill in the requiered spaces")
        elif event == "k_search_btn":
            search_users(values["k_val_search_field"], win)
        elif event == "k_code_btn":
            check_certification(values["k_val_code_field"], values["k_code_cb"], win)
        elif event == "k_download_question_btn":
            download_question_bank(values["k_val_questions_field"], win)
        elif event == "k_upload_question_btn":
            upload_question_bank(values["k_val_questions_field"], win)
    win.close()

#Returns layout for the GUI
def layout_creator():
    add_users = [
        gui.Text("Users/UID/File"),
        gui.In(size=INPUT_BOX_SIZE,enable_events=True, key="k_val_deladd_field"),
        gui.FileBrowse(key="k_users_folder", target="k_val_deladd_field"),
        gui.Button("Add", key="k_add_users_btn"),
        gui.Button("Delete", key="k_delete_users_btn")
        ]

    search_show_users = [
        gui.Text("Searches for given user, if left blank shows all users"),
        gui.In(size=INPUT_BOX_SIZE,enable_events=True, key="k_val_search_field"),
        gui.Button("Search", key="k_search_btn")
    ]

    code_search = [
        gui.Text("Verify certification for given code"),
        gui.In(size=INPUT_BOX_SIZE,enable_events=True, key="k_val_code_field"),
        gui.Button("Verify", key="k_code_btn"),
        gui.Checkbox("Save to computer", default=False, key="k_code_cb")
    ]

    bank_question = [
        gui.Text("Download Bank of Question of specified code or upload from file"),
        gui.In(size=INPUT_BOX_SIZE,enable_events=True, key="k_val_questions_field"),
        gui.Button("Download", key="k_download_question_btn"),
        gui.FileBrowse(key="k_questions_folder", target="k_val_questions_field"),
        gui.Button("Upload", key="k_upload_question_btn")
        
    ]

    action_history = [
        gui.Listbox(
            values=[], enable_events=True,size=LISTBOX_SIZE, key = "k_history_box"
        )
    ]
    
    layout = []
    layout.append([add_users, search_show_users, code_search, bank_question, action_history])
    return layout
    
#Updates action history box from GUI  
def update_listbox(text, win):
    listbox_elements = win["k_history_box"].get_list_values()
    listbox_elements.append([text])
    win['k_history_box'].update(listbox_elements)

#Clears action history and cleans new one
def new_listbox(text, win):
    win['k_history_box'].update([text])

#Creates popup window containing an alert raised by the program
def show_alert(text):
    gui.popup(text, title="Caution!")

#Adds new user/s from a given mail or text file and calls create_user() for its creation 
def add_user(text, win):
    if(Path(text).exists() and text.endswith('.txt')):
        #Create users from text file
        file = open(text, 'rt')
        for line in file:
            create_user(line.lstrip().rstrip(), win) #Remove any leading whitespace to not get an error
    elif(Path(text).exists()):
        #File is not .txt raise error
        show_alert("Invalid file")
    elif(text.find('@') != -1):
        #Create user from mail
        create_user(text.lstrip().rstrip(), win)
    else:
        show_alert("Invalid mail")

#Creates user from given mail with a random 6-digit numeric password, sends mail to change it as well
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
        show_alert("Invalid file")
    else:
        #Tries as uid, if not fails
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
            show_alert(f"Unable to get fetch users")
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
            show_alert(f"Unable to get user with mail: {text}")
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
            show_alert(f"Unable to get user with UID: {text}")

def check_certification(code, save, win):
    has_one = False
    code = code.upper()
    users_colection = DB.collection(u'userScores')
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

#Downloads to same folder a file containing the bank questions unencrypted
def download_question_bank(code, win):
    code = code.upper()
    source_name = "BankQuestions/" + code + ".txt.xd"
    filename_encrypt = code + ".txt.xd"
    filename_decrypt = code + ".txt"

    storage_client = storGC.Client.from_service_account_json(CREDENTIALS_PATH)
    bucket_bank = storage_client.bucket("unityloteria.appspot.com")

    try:
        blob = bucket_bank.blob(source_name)
        blob.download_to_filename(filename_encrypt)
        win['k_history_box'].update(["Succesfully downloaded " + code])
    except:
        win['k_history_box'].update(["Unable to download " + code])
        return -1

    value = subprocess.run([UNECRYPT_FILE_PATH, filename_encrypt], capture_output=True)
    if(value.returncode == 0):
        win['k_history_box'].update([f"Succesfully decrypted file {filename_decrypt}"])
    else:
        win['k_history_box'].update(["Unable to decrypt file"])

#Upload a file containing a new bank of questions with a given code and from a file
def upload_question_bank(file, win):
    if not(Path(file).exists() and file.endswith('.txt')):
        list_elements = win['k_history_box'].get_list_values()
        list_elements.append([f"{file} is not a valid file to upload"])
        win['k_history_box'].update(list_elements)
    else:
        up_file = file[file.rindex('/')+1:] + ".xd"
        value = subprocess.run([ENCRYPT_FILE_PATH, file], capture_output=True)
        if(value.returncode != 0):
            list_elements = win['k_history_box'].get_list_values()
            list_elements.append([f"{up_file} was not succesfully encrypted"])
            win['k_history_box'].update(list_elements)            
        else:
            storage_client = storGC.Client.from_service_account_json(CREDENTIALS_PATH)
            bucket_bank = storage_client.bucket("unityloteria.appspot.com")
            blob = bucket_bank.blob(f"BankQuestions/{up_file}")
            
            blob.upload_from_filename(up_file)
            list_elements = win['k_history_box'].get_list_values()
            list_elements.append([f"{up_file} was succesfully uploaded"])
            win['k_history_box'].update(list_elements)

if __name__ == "__main__":
    main()





