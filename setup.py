# from wspBot import bot
#import json
import inquirer
import os, platform

PATH_OF_EXE = f"{os.getcwd()}\\bot.exe"

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

def setup_frequency():
    data = {}
    options = ["Diariamente", "Semanalmente", "Cancelar configuración y salir"]

    clear_display()
    print("Ingrese las configuraciones iniciales para utilizar el programa\n")
    frequency = make_question("Escoja la frecuencia de ejecución", options)

    if frequency == "Diariamente":
        hours = get_hours()
        command = get_command('Daily', [hours])

        data['frequency'] = 'Daily'
        data['time'] = hours

    elif frequency == "Semanalmente":
        day = make_question(
            "Seleccione el día de ejecución",
            ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        )

        day_english = get_day_english(day)
        
        hours = get_hours()
        command = get_command('Weekly', [day_english, hours])

        data['frequency'] = 'Weekly'
        data['time'] = {day_english: hours}

    elif frequency[0] == 'C':
        exit()
    else:
        setup_frequency()

    data['tasks'] = len(hours) #Amount of tasks
    return command

def verify_path(path:str) -> tuple:
    if path.lower().strip() == 'x': return True, ''
    if path.lower().strip() == 'd': return True, ''

    status = True
    message = ''

    if '\\' in path:
        status = False
        message = "No ingrese backslashes ['\\']"
    if path[-4:] != '.txt':
        status = False
        aux_message = "Debe ingresar el archivo .txt al final de la ruta"

        if not message:
            message = aux_message
        else:
            message = f"{message} y {aux_message.lower()}"

    return status, message

def show_paths(paths:list) -> list:
    print("")

    questions = [
        inquirer.Checkbox(
            name="check",
            message="¿Qué rutas desea borrar? (Espacio para seleccionar) [Enter para enviar]",
            choices=paths
        )
    ]

    answers = inquirer.prompt(questions)
    answers = answers.values()

    for _ in answers:
        for answer in _:
            paths.remove(answer) #This doesn't remove the path in the list

    print(f"Resultado: {paths}")
    return paths

def setup_paths() -> None:
    clear_display()
    print("Para los mensajes se necesita un archivo txt por cada mensaje que se quiera enviar")
    print("""
    Si los mensajes quieren ser acompañados por una imagen
    debe ingresar la ruta absoluta de la imagen dentro del archivo de texto
    Al inicio (Y SOLO AL INICIO) del archivo de texto se debe incluir lo siguiente:\n
    $PATH='C:/la/ruta/aqui'
    """)

    print("Ingrese las rutas absolutas de los mensajes [C:/Users/YourUser/Desktop/resources/msg.txt]")
    print("- Escriba 'x' para terminar el listado")
    print("- Escriba 'd' si desea eliminar una ruta mal ingresada")
    print("- No ingrese las rutas entre comillas")
    print("- NO INGRESE LAS RUTAS CON BACKSLASHES '\\' INGRESE LAS RUTAS CON SLASHES '/'")
    print("- Si ingresa una ruta que no existe, el mensaje simplemente no será enviado")

    paths = []
    while True:
        single_path = input("> ")
        status_path, err_message = verify_path(single_path)

        while not status_path:
            print(err_message)
            single_path = input("> ")
            status_path, err_message = verify_path(single_path)
        
        if single_path.lower().strip() == 'x': break
        elif single_path.lower().strip() == 'd' and len(paths) > 0:
            paths = show_paths(paths)
            continue

        paths.append(single_path)
    
    if len(paths) == 0:
        response = make_question("No se ingresó ninguna ruta,¿Desea cancelar la configuración?", choices=['s', 'n'])

        if response == 's': exit()

        elif response == 'n':
            confirm = make_question("\n¿Ingresó alguna ruta equivocada que quiera borrar?", choices=['s', 'n'])

            if confirm == 's': paths = show_paths(paths)
            else: setup_paths()

        else:
            setup_paths()
    
    print(paths)
        

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


# if check_JSON():
#     group_links, messages, imgs = get_data_from_config()

#     for link in group_links:
#         bot(link, messages, imgs)

# else:
#     setup()
