from alright import WhatsApp
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime
import requests

MESSENGER = WhatsApp()

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
    with open('./msg.txt', 'r', encoding="utf8") as f:
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


#bot("https://chat.whatsapp.com/LrIxKHzMBJsLvwzSWUfLQu", './msg.txt', './image.jpg')