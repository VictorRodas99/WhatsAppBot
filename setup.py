# from wspBot import bot
#import json
import os, platform

PATH_OF_EXE = f"{os.getcwd()}\\bot.exe"

def clear_display():
    current_system = platform.system()

    if current_system == "Windows":
        os.system("cls")
    if current_system == "Linux":
        os.system("clear")

def verify_day(day) -> tuple:
    """
    Return True if the given day is correct and the day in English as well
    """

    days = {
        "lunes": "monday", "martes": "tuesday",
        "miércoles": "wednesday", "jueves": "thursday",
        "viernes": "friday", "sábado": "saturday", "domingo": "sunday"
    }

    for keys, values in days.items():
        if keys == day: return True, values
    
    return False, ''

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


    if frequency == 'Daily':
        for hour in times[0]:
            action = f'$action = New-ScheduledTaskAction -Execute "{PATH_OF_EXE}"'
            trigger = f'$trigger = New-ScheduledTaskTrigger -Daily -At {hour}'
            register = f"Register-ScheduledTask wspbotDaily -Action $action -Trigger $trigger"

            task.append(action)
            task.append(trigger)
            task.append(register)
            commands.append(task)
    elif frequency == 'Weekly':
        for hour in times[1]:
            action = f'$action = New-ScheduledTaskAction -Execute "{PATH_OF_EXE}"'
            trigger = f"$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek {times[0]} -At {hour}"
            register = "Register-ScheduledTask wspbotWeek -Action $action -Trigger $trigger"

            task.append(action)
            task.append(trigger)
            task.append(register)
            commands.append(task)

    
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

def setup_frequency(recursive=False):
    data = {}

    if not recursive:
        clear_display()
        print("Ingrese las configuraciones iniciales para utilizar el programa\n")
        print("1) Escoja la frecuencia de ejecución\n")
    else:
        print("\nIngrese una opción válida")

    print("[a] -> Diaramente")
    print("[b] -> Semanalmente")
    print("[c] -> Cancelar configuración y salir\n")

    frequency = input("[a/b/c] > ")

    if frequency.lower().strip() == 'a':
        hours = get_hours()
        command = get_command('Daily', [hours])

        data['frequency'] = 'Daily'
        data['time'] = hours

    elif frequency.lower().strip() == 'b':
        print("Ingrese el día de ejecución")
        day = input("> ").strip().lower()

        status_day, day_english = verify_day(day)
        while not status_day:
            print("\nIngrese un día correcto (no olvide los acentos)")

            day = input("> ").strip().lower()
            status_day, day_english = verify_day(day)
        
        hours = get_hours()
        command = get_command('Weekly', [day_english, hours])

        data['frequency'] = 'Weekly'
        data['time'] = {day_english: hours}

    elif frequency.lower().strip() == 'c':
        exit()
    else:
        setup_frequency(True)

    
    return command

def setup_paths() -> None:
    clear_display()
    print("Para los mensajes se necesita un archivo txt por cada mensaje que se quiera enviar")
    print("""
        Si los mensajes quieren ser acompañados por una imagen
        debe ingresar la ruta absoluta de la imagen dentro del archivo de texto
        Al inicio (Y SOLO AL INICIO) del archivo de texto se debe incluir lo siguiente:\n
        $PATH='la\\ruta\\aqui'
    """)

    print("2) Ingrese las rutas absolutas de los mensajes [C:/Users/YourUser/Desktop/resources/msg.txt]")
    print("- Escriba 'x' para terminar el listado")
    print("- No ingrese las rutas entre comillas")
    print("- NO INGRESE LAS RUTAS CON BACKSLASHES '\\' INGRESE LAS RUTAS CON SLASHES '/'")

    paths = []
    while True:
        single_path = input("> ")
        if single_path.lower().strip() == 'x': break

        #TODO: verify the path before append

        paths.append(single_path)



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
