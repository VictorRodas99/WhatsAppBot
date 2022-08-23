from bs4 import BeautifulSoup
from datetime import datetime
from alright import WhatsApp
import requests, json, os
from time import sleep

def check_config() -> tuple:
    exists = True
    current_path = os.getcwd()

    #When powershell executes automatically the exe, the origin change to system32
    if current_path.split('\\')[-1].lower() == 'system32':
        try:
            with open('../../origin.txt', 'r') as f:
                path = f.read()
            
            current_path = path
            path = '/'.join(path.split('\\'))
            files = os.listdir(path)

            if 'config.json' not in files: exists = False
            else: exists = True

        except FileNotFoundError:
            print("No existe el archivo origin.txt")
            sleep(2)
            exists = False
        
    else:
        files = os.listdir()
        if 'config.json' not in files: exists = False

    
    return current_path, exists


def write_in_log(names:list) -> None:
    with open('log.txt', 'w') as f:
        now = datetime.now()
        f.write(f"[LOG DATE] -> ({now.day}/{now.month}/{now.year}) [{now.hour}:{now.minute}]\n")
        f.write("Hay algún link o algunos links que ya no funcionan\n")
        f.write("Estos son los grupos cuyos links aún funcionan\n")

        for name in names: f.write(f'- {name}\n')


def get_working_links(links:str) -> tuple:
    links = list(dict.fromkeys(links)) #remove duplicates

    control = False
    names = []
    for link in links:
        group_name = get_group_name(link)

        if group_name == '':
            links.remove(link)
            control = True
        else:
            names.append(group_name)
    
    if control: write_in_log(names)

    return links, names


def get_group_name(link) -> str:
    response = requests.get(link)
    soup = BeautifulSoup(response.content, "html.parser")

    head = soup.find("head")
    meta = head.find("meta", attrs={"property": "og:title"})
    group = meta.attrs['content']

    return group


def get_text(path) -> str:
    with open(path, 'r', encoding="utf8") as f:
        has_image = False
        text = f.read().split('\n')
        path = text[0]

        if '$PATH=' in path:
            path = path[6::]
            text = '\n'.join(text[1::])
            has_image = True
        else:
            path = None
            text = '\n'.join(text)
    
    return text, has_image, path


def get_data_from_json(config_path:str) -> dict:
    with open(config_path, 'r') as config:
        data = json.load(config)
    
    return data


def bot(group_links:list, message_paths:list) -> None:
    group_links, names = get_working_links(group_links)

    x = 0
    while x < len(group_links):
        group = names[x]

        for path in message_paths:
            message, has_image, path_img = get_text(path)
            MESSENGER.find_by_username(group)

            if has_image:
                MESSENGER.send_picture(path_img)
                sleep(1)

            MESSENGER.send_message(message, with_emojis=True) #TODO: what happens if the message doesn't have emojis?

        x+=1


def main(config_path:str) -> None:
    data = get_data_from_json(config_path)
    
    group_links = data["group_links"]
    message_paths = data["messages"]

    bot(group_links, message_paths)


if __name__ == '__main__':
    current_path, config_exists = check_config()

    if config_exists:
        MESSENGER = WhatsApp()
        main(f"{current_path}\\config.json")
    else:
        print("Ejecute `setup` para iniciar las configuraciones")
        sleep(1)