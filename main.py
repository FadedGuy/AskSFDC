import firebase_admin
from pathlib import Path
import random
from firebase_admin import credentials, auth, firestore
from google.cloud import storage as storGC
import PySimpleGUI as gui
import datetime
import string
import subprocess

###########################
# CONSTANTS
INPUT_BOX_SIZE = (20,1)
LISTBOX_SIZE = (85,10)
ENCRYPT_FILE_PATH = "./EncryptFile.exe"
UNECRYPT_FILE_PATH = "./Decrypt.exe"
CREDENTIALS_PATH = "credentials.json"
CREDENTIAL_CERTIFICATE = credentials.Certificate(CREDENTIALS_PATH) #check if path exists
DEFAULT_APP = firebase_admin.initialize_app(CREDENTIAL_CERTIFICATE, {
    'storageBucket' : 'unityloteria.appspot.com'
})

###########################
# TO CHECK
#
# Reload certifications so it includes new ones each time it is called since now
# it only shows the ones that were when the program was initially called 
# 
# Should consider merging encryption and unencryption in the same executable and flag 
# depending on which mode it's supposed to use
# 
# Padding is invalid and cannot be removed.
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
            values=[], enable_events=True,size=LISTBOX_SIZE, key = "k_history_box", expand_x=True
        )
    ]
    
    layout = []
    layout.append([add_users, search_show_users, code_search, bank_question, action_history])
    return layout
    
#Updates action history box from GUI  
def update_listbox(text, win, allow_more):
    listbox_elements = win["k_history_box"].get_list_values()
    if(len(listbox_elements) > 10 or not allow_more):
        new_listbox(text, win)
    else:
        listbox_elements.append([text])
        win['k_history_box'].update(listbox_elements)

#Clears action history and cleans new one
def new_listbox(text, win):
    win['k_history_box'].update([text])

#Creates popup window containing an alert raised by the program
def show_alert(text):
    gui.popup_error(text, title="Caution!", line_width=35, keep_on_top=True, modal=True)

#Adds new user/s from a given mail or text file and calls create_user() for its creation 
def add_user(text, win):
    if(Path(text).exists() and text.endswith('.txt')):
        #Create users from text file
        file = open(text, 'rt')
        for line in file:
            create_user(line.lstrip().rstrip(), win, True) #Remove any leading whitespace to not get an error
    elif(Path(text).exists()):
        #File is not .txt raise error
        show_alert("Invalid file")
    elif(text.find('@') != -1):
        #Create user from mail
        create_user(text.lstrip().rstrip(), win, False)
    else:
        show_alert("Invalid mail")

def generate_password(size):
    available_characters = string.ascii_lowercase + string.ascii_uppercase + string.punctuation + string.digits
    pw = ""
    for each in range(size):
        pw = pw + available_characters[random.randint(0,len(available_characters)-1)]
    print(pw)
    return pw
#Creates user from given mail with a random 6-digit numeric password, sends mail to change it as well
def create_user(mail, win, allow_more_listbox):
    msg_cur = ""
    try:
        new_user = auth.create_user(
            email = mail,
            #Not the best for security since it can be brute force, but this ain't important, can be changed
            password = generate_password(15), 
            disabled = False
        )
        msg_cur = f"Added new email {mail} succesfully"
        auth.generate_password_reset_link(new_user)
    except auth._auth_utils.EmailAlreadyExistsError:
        msg_cur = f"Email already exists {mail}"
    except:
        msg_cur = f"Added new email {mail} succesfully"
    
    update_listbox(msg_cur, win, allow_more_listbox)
    

def delete_users(uid, win, allow_more_listbox):
    msg_cur = ""
    try:
        auth.delete_user(uid=uid)
        msg_cur = f"Deleted user {uid}"
    except firebase_admin._auth_utils.UserNotFoundError:
        msg_cur =  f"User not found {uid}"
    except:
        msg_cur = f"Error occured while deleting {uid}"
        pass
    update_listbox(msg_cur, win, allow_more_listbox)

def del_users(text, win):
    if(Path(text).exists() and text.endswith('.txt')):
        #Delete users from text file
        file = open(text, 'rt')
        for line in file:
            delete_users(line.lstrip().rstrip(), win, True) #Remove any leading whitespace to not get an error
    elif(Path(text).exists()):
        #File is not .txt raise error
        show_alert("Invalid file")
    else:
        #Tries as uid, if not fails
        delete_users(text.lstrip().rstrip(), win, False)

def search_users(text, win):
    if(text == "" or text == " "):
        try:
            page = auth.list_users()
            while page:
                page = page.get_next_page()
            msg = ""
            for user in auth.list_users().iterate_all():
                ts = float(user.user_metadata.last_sign_in_timestamp)
                ts = ts/1000
                msg = f"Mail: {user.email}, UID: {user.uid}, Last Accesed: {datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')}"
                update_listbox(msg, win, True)            
        except:
            show_alert(f"Unable to get fetch users")
            #When blank
    elif(text.find('@') != -1):
        try:
            user = auth.get_user_by_email(text)
            ts = float(user.user_metadata.last_sign_in_timestamp)
            ts = ts/1000
            msg = f"Mail: {user.email}, UID: {user.uid}, Last Accesed: {datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')}"
            update_listbox(msg, win, False)
        except:
            show_alert(f"Unable to get user with mail: {text}")
    else:
        try:
            user = auth.get_user(text)
            ts = float(user.user_metadata.last_sign_in_timestamp)
            ts = ts/1000
            msg = f"Mail: {user.email}, UID: {user.uid}, Last Accesed: {datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')}"
            update_listbox(msg, win, False)
        except:
            show_alert(f"Unable to get user with UID: {text}")

def check_certification(code, save, win):
    has_one = False
    code = code.upper()
    db = firestore.client(DEFAULT_APP)
    users_colection = db.collection(u'userScores')
    docs = users_colection.stream()
    file_path = "CertificationScores" + code + ".csv"
    if(save):
        if(Path(file_path).exists()):
            file = open(file_path, "w")
        else:
            file = open(file_path, "x")
        file.write("UID     ,Mail   ,Score,Win,Time to Answer\n")
    for doc in docs:
        dict_doc = doc.to_dict()
        if(doc.id.endswith(code) and code != ""):
            has_one = True
            if(dict_doc.get("Win")):
                update_listbox(f"{dict_doc['Mail']} has certified with a score of {dict_doc['Score']} in {dict_doc['timeFinish'] - dict_doc['timeBegin']}", win, True)
            else:
                update_listbox(f"{dict_doc['Mail']} hasn't certified with a score of {dict_doc['Score']} in {dict_doc['timeFinish'] - dict_doc['timeBegin']}", win, True)
            if(save):
                file.write(f"{doc.id.lstrip(code.upper())},{dict_doc['Mail']},{dict_doc['Score']},{dict_doc['Win']}, {dict_doc['timeFinish'] - dict_doc['timeBegin']}\n")
    if(not has_one):
        update_listbox(f"No certifications on record for code {code}", win,False)

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
        update_listbox("Succesfully downloaded " + code, win, False)
    except:
        update_listbox("Unable to download " + code, win, False)
        return -1

    # Calls the external unecryption program so the file is unencrypted and saved, it return
    # 0 when it finished succesfully, and -1 when it encountered an error somewhere in the
    # process
    value = subprocess.run([UNECRYPT_FILE_PATH, filename_encrypt], capture_output=True)
    if(value.returncode == 0):
        update_listbox(f"Succesfully decrypted file {filename_decrypt}", win, False)
    else:
        update_listbox("Unable to decrypt file", win, False)


#Upload a file containing a new bank of questions with a given code and from a file
def upload_question_bank(file, win):
    if not(Path(file).exists() and file.endswith('.txt')):
        update_listbox(f"{file} is not a valid file to upload", win, False)
    else:
        up_file = file[file.rindex('/')+1:] + ".xd"
        
        # Calls external encryption program so the file is encrypted and then uploaded to the
        # cloud service
        value = subprocess.run([ENCRYPT_FILE_PATH, file], capture_output=True)
        if(value.returncode != 0):      
            update_listbox(f"{up_file} was not succesfully encrypted", win, False)      
        else:
            storage_client = storGC.Client.from_service_account_json(CREDENTIALS_PATH)
            bucket_bank = storage_client.bucket("unityloteria.appspot.com")
            blob = bucket_bank.blob(f"BankQuestions/{up_file}")
            
            blob.upload_from_filename(up_file)
            
            update_listbox(f"{up_file} was succesfully uploaded", win, False)

if __name__ == "__main__":
    main()