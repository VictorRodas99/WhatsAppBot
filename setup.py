# from wspBot import bot
import json
import inquirer
import os, platform

PATH_OF_EXE = f"{os.getcwd()}\\bot.exe"

COLORS = {
    'black': '30', 'red': '31', 'green': '32',
    'yellow': '33', 'blue': '34', 'magenta': '35',
    'white': '37'
}

def cprint(color:str, text:str, reset:bool=True) -> None:

    for key_color, value in COLORS.items():
        if key_color == color.lower():
            print(f"\033[1;{value}m{text}")
            if reset: print('\033[1;0m', end='')
            return
    
    print(text)

def cinput(color:str, text:str) -> str:

    for key_color, value in COLORS.items():
        if key_color == color.lower():
            return_value = input(f"\033[1;{value}m{text}")
            print('\033[1;0m', end='')
            return return_value
    
    raise Exception("ERROR: Wrong color was given")

def write_json(data:dict) -> None:
    """
    This function setup the config JSON
    """
    JSON_object = json.dumps(data, indent=4)

    with open('config.json', 'w') as f:
        f.write(JSON_object)

def make_question(message:str, choices:list) -> str:
    questions = [
        inquirer.List(
            "answer",
            message,
            choices
        )
    ]

    answers = inquirer.prompt(questions)
    return answers['answer']

def clear_display():
    current_system = platform.system()

    if current_system == "Windows":
        os.system("cls")
    if current_system == "Linux":
        os.system("clear")

def get_day_english(day:str) -> str:
    """
    Return the day in English
    """

    days = {
        "Lunes": "Monday", "Martes": "Tuesday",
        "Miércoles": "Wednesday", "Jueves": "Thursday",
        "Viernes": "Friday", "Sábado": "Saturday", "Domingo": "Sunday"
    }

    for keys, values in days.items():
        if keys == day:
            return values

def verify_hours(hours) -> bool:
    status = True
    for hour in hours:
        am_or_pm = hour[-2:] #get the 12:32(am) string (am or pm)

        if am_or_pm != 'pm' and am_or_pm != 'am':
            status = False
            break

        if ':' in hour:
            hour = hour.split(':')

            if len(hour) > 2: #if the user enter something like this: (12:2:3)
                status = False
                break

            try:
                h = int(hour[0])
                m = int(hour[1][:-2])
                if h > 12: status = False
                if m > 60: status = False
            except ValueError: #if the user enter a word, not a number
                status = False
                break

        else:
            status = False
    
    return not status

def get_command(frequency:str, times:list) -> str:
    commands = []
    task = []
    counter = 0


    if frequency == 'Daily':
        while counter < len(times[0]):
            hour = times[0][counter]

            action = f'$action = New-ScheduledTaskAction -Execute "{PATH_OF_EXE}"'
            trigger = f'$trigger = New-ScheduledTaskTrigger -Daily -At {hour}'
            register = f"Register-ScheduledTask wspbotDaily_{counter} -Action $action -Trigger $trigger"

            task.append(action)
            task.append(trigger)
            task.append(register)
            commands.append(task)
            task = []

            counter+=1

    elif frequency == 'Weekly':
        while counter < len(times[1]):
            hour = times[1][counter]

            action = f'$action = New-ScheduledTaskAction -Execute "{PATH_OF_EXE}"'
            trigger = f"$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek {times[0]} -At {hour}"
            register = f"Register-ScheduledTask wspbotWeek_{counter} -Action $action -Trigger $trigger"

            task.append(action)
            task.append(trigger)
            task.append(register)
            commands.append(task)
            task = []

            counter+=1
    
    return commands

def get_hours() -> list:
    print("\nIngrese la hora de ejecución en formato de 12 horas `h:m[am/pm]`")
    print("Si ingresa más de una hora, ingresalos separados por espacios `h1:m1am h2:m2pm`")

    hours = input("> ").split(' ')

    for x in range(len(hours)): #We remove the whitespacess
        hour = hours[x]
        hours[x] = hour.strip()

    status = verify_hours(hours)

    while status:
        print("\nIngrese las horas en formato adecuado! [horas:minutos][am/pm]")
        hours = input("> ").split(' ')
        status = verify_hours(hours)
    
    return hours

def setup_frequency() -> tuple:
    data = {}
    options = ["Diariamente", "Semanalmente", "Cancelar configuración y salir"]

    clear_display()
    cprint("Blue", "Ingrese las configuraciones iniciales para utilizar el programa\n")
    frequency = make_question("Escoja la frecuencia de ejecución", options)

    if frequency == "Diariamente":
        hours = get_hours()
        command = get_command('Daily', [hours])

        data['frequency'] = 'Daily'
        data['times'] = hours

    elif frequency == "Semanalmente":
        day = make_question(
            "Seleccione el día de ejecución",
            ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        )

        day_english = get_day_english(day)
        
        hours = get_hours()
        command = get_command('Weekly', [day_english, hours])

        data['frequency'] = 'Weekly'
        data['times'] = {day_english: hours}

    elif frequency[0] == 'C':
        exit()
    else:
        setup_frequency()

    data['amount_tasks'] = len(hours) #Amount of tasks

    write_json(data)
    return command

def get_error_message_for_path(message:str, aux_message:str) -> tuple:
    """
    This function is for verify_path()
    """

    status = False

    if not message:
        message = aux_message
    else:
        message = f"{message} y {aux_message.lower()}"
    
    return status, message

def verify_path(path:str) -> tuple:
    if path.lower().strip() == 'x': return True, ''
    if path.lower().strip() == 'd': return True, ''

    status = True
    message = ''

    if '\\' in path:
        status = False
        message = "No ingrese backslashes ['\\']"
    
    if '/' not in path:
        status, message = get_error_message_for_path(message, "Ingrese las rutas separadas por slashes ['/']")
    
    if '//' in path:
        status, message = get_error_message_for_path(message, "Formato no adecuado para las rutas")

    if path[-4:] != '.txt':
        status, message = get_error_message_for_path(message, "Debe ingresar el archivo .txt al final de la ruta")

    return status, message

def show_paths(paths:list, err:str='') -> list:
    print("")

    if err != '':
        questions = [
            inquirer.Checkbox(
                name="check",
                message=err,
                choices=paths
            )
        ]
    else:
        questions = [
            inquirer.Checkbox(
                name="check",
                message="¿Qué rutas desea borrar? (Espacio para seleccionar) [Enter para enviar]",
                choices=paths
            )
        ]

    answers = inquirer.prompt(questions)
    answers = answers.values()

    exists_answer = False
    for _ in answers:
        for answer in _:
            exists_answer = True
            paths.remove(answer)

    if not exists_answer:
        return(show_paths(paths, err="ERROR: No ha seleccionado [Aprete espacio]"))
    else:
        return paths

def setup_paths() -> list:
    clear_display()
    cprint("Blue", "Para los mensajes se necesita un archivo txt por cada mensaje que se quiera enviar")
    print("""
    Si los mensajes quieren ser acompañados por una imagen
    debe ingresar la ruta absoluta de la imagen dentro del archivo de texto.\n
    Al inicio \033[1;31m(Y SOLO AL INICIO)\033[1;0m del archivo de texto se debe incluir lo siguiente:
    """)
    cprint("Yellow", "    $PATH='C:/la/ruta/aqui'\n")

    print("Ingrese las rutas absolutas de los mensajes ", end='')
    cprint("Yellow", "[C:/Users/YourUser/Desktop/resources/msg.txt]")

    print("- Escriba \033[1;34m'x'\033[1;0m para terminar el listado")
    print("- Escriba \033[1;34m'd'\033[1;0m si desea eliminar una ruta mal ingresada")
    print("- No ingrese las rutas entre comillas")
    cprint("Red", "- NO INGRESE LAS RUTAS CON BACKSLASHES '\\' INGRESE LAS RUTAS CON SLASHES \033[1;32m'/'\033[1;0m")
    print("- Si ingresa una ruta que no existe, el mensaje simplemente no será enviado")

    paths = []
    while True:
        single_path = cinput("Blue", "> ")
        status_path, err_message = verify_path(single_path)

        while not status_path:
            cprint("Red", err_message)
            single_path = cinput("Blue", "> ")
            status_path, err_message = verify_path(single_path)
        
        if single_path.lower().strip() == 'x': break
        elif single_path.lower().strip() == 'd' and len(paths) > 0:
            paths = show_paths(paths)
            cprint("Blue", "Siga ingresando nuevas rutas o ingrese 'x' para salir")
            continue
        
        if single_path != 'd': #If the user put first of all a 'd'
            paths.append(single_path)
    
    if len(paths) == 0:
        response = make_question("No se ingresó ninguna ruta,¿Desea cancelar la configuración?", choices=['Sí', 'No'])

        if response[0] == 'S': exit()

        elif response[0] == 'N':
            confirm = make_question("\n¿Ingresó alguna ruta equivocada que quiera borrar?", choices=['Sí', 'No'])

            if confirm[0] == 'S': paths = show_paths(paths)
            else: setup_paths()

        else:
            setup_paths()
    
    write_json({"messages": paths})
    return paths
        
def setup_links() -> None:
    clear_display()
    print("Ingrese los links de los grupos a los cuales mandar los mensajes")
    print("Ingrese los links completos [https://chat.whatsapp.com/AbCdF123]")
    print("- No ingrese los links entre comillas")
    print("- Escriba 'x' para terminar el listado")
    print("- Escriba 'd' para eliminar algún link mal ingresado")

#setup_frequency()
#setup_paths()



# def get_data_from_config() -> tuple:
#     with open('config.json', 'r') as f:
#         data = json.load(f)
    
#     return data['groupLinks'], data['messages'], data['imgs']

# def check_JSON() -> bool:
#     try:
#         f = open('config.json', 'r')
#         f.close()
#         return True
#     except FileNotFoundError:
#         return False

# def main_setup() -> None:

#     if check_JSON():
#         # group_links, messages, imgs = get_data_from_config()

#         # for link in group_links:
#         #     bot(link, messages, imgs)

# else:
#     setup()
