from time import sleep
import os, subprocess
import inquirer
import json

task_frequency = False #False (Daily) | True (Weekly)

PATH_OF_EXE = f"{os.getcwd()}\\bot.exe"

COLORS = {
    'black': '30', 'red': '31', 'green': '32',
    'yellow': '33', 'blue': '34', 'magenta': '35',
    'white': '37'
}


#This resolve the problem with subprocess and pyinstaller
def subprocess_args(include_stdout=True):
    # The following is true only on Windows.
    if hasattr(subprocess, 'STARTUPINFO'):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        env = os.environ
    else:
        si = None
        env = None

    if include_stdout:
        ret = {'stdout': subprocess.PIPE}
    else:
        ret = {}

    ret.update({'stdin': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'startupinfo': si,
                'env': env })
            
    return ret

def execute_process(args:list, output_name:str) -> str:
    output_name = f"{output_name}.txt"

    with open(output_name, 'wb') as f:
        try:
            try:
                txt = subprocess.check_output(args, **subprocess_args(False))
                f.write(txt)

            except subprocess.CalledProcessError as e:
                f.write(b'1\n')
                f.write(e.stderr)

        except OSError as e:
            f.write('Failed: {}'.format(str(e)))
    
    with open(output_name, 'r') as f: output = f.read()
    
    return output



#Powershell
def get_task_names() -> list:
    #NO optimizado!

    if task_frequency:
        task_name = "wspbotWeek_"
    else:
        task_name = "wspbotDaily_"

    output = execute_process(["powershell", f'Get-ScheduledTask | Select-String "{task_name}"'], "task_names")
    output = output.split("\n")

    output_list = []
    for out in output:
        if 'TaskName' in out:
            start = out.find('TaskName')
            end = out.find(',')
            output_list.append(out[start:end])


    output_list = list(dict.fromkeys(output_list))

    tasks_names = []
    for char in output_list:
        start = char.index('"')
        end   = char.rindex('"')
        tasks_names.append(char[start:end].replace('"', ''))
    
    os.system("del task_names.txt")
    return tasks_names

def unregister_task(task_name:str) -> None:
    command = f'Unregister-ScheduledTask -TaskName "{task_name}" -Confirm:$false'
    output = execute_process(["powershell", command], "unregister")

    #if throws an error
    if output.split('\n')[0] == '1':
        raise Exception(f"ERROR: No se pudo borrar la tarea `{task_name}`")
    
    os.system("del unregister.txt")

def exec_powershell() -> bool:
    """
    Executes the task register,
    returns ```True``` if the script ends successfully, otherwise returns ```False```
    """

    status = True

    arg = "Set-ExecutionPolicy RemoteSigned -Scope Process -Force; if ($?) { ./setTasks.ps1 }"
    output = execute_process(["powershell", arg], "register")
    stderror = output.split('\n')[0]

    if stderror == '1': status = False
    else:
        print(output)
        os.system("del register.txt")
        os.system("del setTasks.ps1")

    return status

def write_script(commands:list) -> bool:
    """
    Creates the task register script
    """

    for command in commands:
        with open("setTasks.ps1", 'w') as script:
            for section in command:
                script.write(f"{section}\n")

        success_status = exec_powershell() 
        if not success_status: break
    
    return success_status



#Input-output (General)
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

def clear_display(msg=True) -> None:
    os.system("cls")
    if msg: cprint("Blue", "Ingrese las configuraciones iniciales para utilizar el programa\n")



#Config file
def check_config() -> bool:
    exists = True
    files = os.listdir()

    if 'config.json' not in files:
        exists = False

    return exists

def write_json(data:dict) -> None:
    """
    This function setup the config JSON
    """
    JSON_object = json.dumps(data, indent=4)

    with open('config.json', 'w') as f:
        f.write(JSON_object)

def delete_or_change(data, key:str, option:str) -> list:
    """
    This function is for ```change_data()```
    """

    if key == "group_links":
        if option == 'B': new_data = show_links_or_paths(data, mode="links")
        else: new_data = get_link_or_path_from_user("Siga ingresando nuevos links o ingrese 'x' para salir", "links")

    elif key == "messages":
        if option == 'B': new_data = show_links_or_paths(data, mode="paths")
        else: new_data = get_link_or_path_from_user("Siga ingresando nuevas rutas o ingrese 'x' para salir", "paths")

    elif key == "times":
        if option == 'B': new_data = show_links_or_paths(data, mode="horas")
        else: new_data = get_hours()   

    return new_data 

def change_data(data, key:str) -> list | dict:
    if type(data) == list:
        if len(data) < 2:
            cprint("Red", "Solo hay un dato, no puede borrarlo, solo modificarlo!")
            cprint("Red", f"El dato: {data[0]}")
            exit(1)

        cprint("Yellow", "Puede borrar un dato o puede cambiarlo por otro")
        response = make_question("¿Qué acción desea realizar?", choices=["Borrar", "Nuevo dato"])

        new_data = delete_or_change(data, key, option=response[0])
 
    elif type(data) == dict:
        cprint("Red", "No implementado")
        exit(1)
    else:
        cprint("Red", "Only <dict> and <list> types are implemented")
        exit(1)
    
    return new_data

def modify_json() -> None:
    with open("config.json", 'r') as config:
        data:dict = json.load(config)

    choices = list(data.keys())
    del choices[2] #remove amount_task from list

    key = make_question("¿Qué datos desea modificar?", choices)
    entry = change_data(data[key], key)
    data[key] = entry

    if key == "times": #if times has changed then we change the schedule of tasks
        commands = get_command(data["frequency"], [entry])
        old_task_names = get_task_names()

        if len(old_task_names) > 0: #if an unregister has been done externally
            for name in old_task_names: unregister_task(name)
            cprint("Green", "Tareas viejas removidas")

        success = write_script(commands)
        if not success: cprint("Red", "\nAn error has ocurred in the task register\n")
    
    write_json(data)



#Checkers
def get_error_message_for_path(message:str, aux_message:str) -> tuple:
    """
    This function is for ```verify_path()```
    """

    status = False

    if not message:
        message = aux_message
    else:
        message = f"{message} y {aux_message.lower()}"
    
    return status, message

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

def verify_link(link:str) -> tuple:
    if link.lower().strip() == 'x': return True, ''
    if link.lower().strip() == 'd': return True, ''

    status = True
    message = ''

    if 'https://' not in link[:8]:
        status = False
        message = "El link debe empezar por \033[1;33m'https://'\033[1;0m"

    if '\\' in link or '/' not in link or '//' in link[9::]:
        status = False
        aux_message = "Formato no adecuado para los link"

        if not message:
            message = aux_message
        else:
            message = f"{aux_message} | {message}"


    return status, message



#Get formatted data
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

def get_command(frequency:str, times:list) -> str:
    global task_frequency
    commands = []
    task = []
    counter = 0


    if frequency == 'Daily':
        task_frequency = False

        while counter < len(times[0]):
            hour = times[0][counter]

            action = f'$action = New-ScheduledTaskAction -Execute "{PATH_OF_EXE}";'
            trigger = f'$trigger = New-ScheduledTaskTrigger -Daily -At {hour};'
            register = f"Register-ScheduledTask wspbotDaily_{counter} -Action $action -Trigger $trigger;"

            task.append(action)
            task.append(trigger)
            task.append(register)
            commands.append(task)
            task = []

            counter+=1

    elif frequency == 'Weekly':
        task_frequency = True

        while counter < len(times[1]):
            hour = times[1][counter]

            action = f'$action = New-ScheduledTaskAction -Execute "{PATH_OF_EXE}";'
            trigger = f"$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek {times[0]} -At {hour};"
            register = f"Register-ScheduledTask wspbotWeek_{counter} -Action $action -Trigger $trigger;"

            task.append(action)
            task.append(trigger)
            task.append(register)
            commands.append(task)
            task = []

            counter+=1
    
    return commands

def get_hours() -> list:
    cprint("Yellow", "\nIngrese la hora de ejecución en formato de 12 horas `h:m[am/pm]`")
    print("Si ingresa más de una hora, ingresalos separados por espacios \033[1;34m`h1:m1am h2:m2pm`\033[1;0m")

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



#Get data from user
def show_links_or_paths(data:list, mode:str, err:str='',) -> list:
    print("")

    if err != '':
        questions = [
            inquirer.Checkbox(
                name="check",
                message=err,
                choices=data
            )
        ]
    else:
        questions = [
            inquirer.Checkbox(
                name="check",
                message=f"¿Qué {mode} desea borrar? (Espacio para seleccionar) [Enter para enviar]",
                choices=data
            )
        ]

    answers = inquirer.prompt(questions)
    answers = answers.values()

    exists_answer = False
    for _ in answers:
        for answer in _:
            exists_answer = True
            data.remove(answer)

    if not exists_answer:
        return(show_links_or_paths(data, mode, err="ERROR: No ha seleccionado [Aprete espacio]"))
    else:
        return data

def get_link_or_path_from_user(message_delete:str, mode:str) -> list:
    data = []
    while True:
        single_data = cinput("Blue", "> ")

        if mode == "paths": correct, err_message = verify_path(single_data)
        elif mode == "links": correct, err_message = verify_link(single_data)

        while not correct:
            cprint("Red", err_message)
            single_data = cinput("Blue", "> ")

            if mode == "paths": correct, err_message = verify_path(single_data)
            elif mode == "links": correct, err_message = verify_link(single_data)
        
        if single_data.lower().strip() == 'x': break
        
        elif single_data.lower().strip() == 'd' and len(data) > 0:
            data = show_links_or_paths(data, mode)
            cprint("Blue", message_delete)
            continue
        
        if single_data != 'd': #If the user put first of all a 'd'
            data.append(single_data)
    
    return data



#Main functions
def setup_frequency() -> tuple:
    data = {}
    options = ["Diariamente", "Semanalmente", "Cancelar configuración y salir"]

    clear_display()
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

    cprint("Blue", "\nTiempo configurado!\n")
    sleep(1)
    return data, command

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

    paths = get_link_or_path_from_user("Siga ingresando nuevas rutas o ingrese 'x' para salir", "paths")
    
    if len(paths) == 0:
        response = make_question("No se ingresó ninguna ruta, ¿Desea cancelar la configuración?", choices=['Sí', 'No'])

        if response[0] == 'S': exit()

        elif response[0] == 'N':
            print("")
            confirm = make_question("¿Ingresó alguna ruta equivocada que quiera borrar?", choices=['Sí', 'No'])

            if confirm[0] == 'S': paths = show_links_or_paths(paths, "rutas")
            else: setup_paths()

        else:
            return(setup_paths())
    
    cprint("Blue", "\nRutas configuradas!\n")
    sleep(1)
    return paths
        
def setup_links() -> list:
    clear_display()
    cprint("Blue", "Ingrese los links de los grupos a los cuales mandar los mensajes\n")
    print("Ingrese los links completos \033[1;33m[https://chat.whatsapp.com/AbCdF123]\033[1;0m")
    print("- No ingrese los links entre comillas")
    print("- Escriba 'x' para terminar el listado")
    print("- Escriba 'd' para eliminar algún link mal ingresado")

    links = get_link_or_path_from_user("Siga ingresando nuevos links o ingrese 'x' para salir", "links")

    if len(links) == 0:
        response = make_question("No se ingresó ningún link, ¿Desea cancelar la configuración?", choices=['Sí', 'No'])

        if response[0] == 'S': exit()

        elif response[0] == 'N':
            print("")
            confirm = make_question("¿Ingresó algún link equivocado que quiera borrar?", choices=['Sí', 'No'])

            if confirm[0] == 'S': links = show_links_or_paths(links, "links")
            else: setup_links()

        else:
            return(setup_links())
    
    cprint("Blue", "\nLinks configurados!\n")
    sleep(1)
    return links

def main_setup() -> None:
    data = {}

    frequency_data, commands = setup_frequency()
    message_paths = setup_paths()
    group_links = setup_links()
    
    data = frequency_data
    data['messages'] = message_paths
    data['group_links'] = group_links

    write_json(data)
    success_status = write_script(commands)

    if not success_status: cprint("Red", "\nAn error has ocurred in the task register\n")

#TODO: check for nonexistent paths

config_exists = check_config()

if config_exists:
    clear_display(msg=False)
    cprint("Blue", "Ya existe una configuración")
    response = make_question("¿Desea modificar las configuraciones dadas?", choices=['Sí', 'No'])

    if response[0] == 'S':
        modify_json() #TODO: change the task schedule if times have been changed
    else:
        task_names = get_task_names()

        if len(task_names) > 0:
            for name in task_names: unregister_task(name)

        main_setup()
else:
    main_setup()