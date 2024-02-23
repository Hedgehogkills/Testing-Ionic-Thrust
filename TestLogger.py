import serial
import gspread
import time
from google.oauth2 import service_account
from datetime import datetime
import threading


def push_data_to_cloud(data_logged, date_time_array, cmd, testName):
    """Pushes and formats data to a Google SpreadSheet"""
    
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    creds_sample = service_account.Credentials.from_service_account_file("----------------your-file-location-------------").with_scopes(scope)
    client = gspread.authorize(creds_sample)
    sheet = client.open("DataLog") # Google sheet used to log all tests

    # existing_data = sheet.get_all_records()
    print(data_logged)
    print(date_time_array)
    
    # DATA FORMATTING HERE----------------
    worksheet = sheet.add_worksheet(title=testName, rows=len(data_logged)+2, cols=2)
    
    worksheet.update_cell(1,2, 'Thrust (g)')
    if (cmd == "t"):
        worksheet.update_cell(1,1, 'Time')
        # Updates all values and inputs at once to keep from Api update error
        values = []
        for cpfs in range(len(data_logged)):
            values.append([date_time_array[cpfs], data_logged[cpfs]])
        rng = "'" + worksheet._properties['title'] + "'!A2"
        worksheet.spreadsheet.values_update(rng, params={'valueInputOption': 'USER_ENTERED'}, body={'values': values})

    elif(cmd == "c"):
        worksheet.update_cell(1,1, 'Test #')
        values = []
        for cpfs in range(len(data_logged)-1):
            values.append([cpfs, data_logged[cpfs]])
        rng = "'" + worksheet._properties['title'] + "'!A2"
        worksheet.spreadsheet.values_update(rng, params={'valueInputOption': 'USER_ENTERED'}, body={'values': values})
    worksheet.update_cell((len(data_logged)+2),1, 'Annotations:')
    annotations = input("AnnotaPretions: ")
    worksheet.update_cell((len(data_logged)+2), 2, annotations)
    
    print('Readings pushed to cloud')


def get_the_date_and_time():
    """Pulls current date and time to be logged"""
    # datetime object containing current date and time
    now = datetime.now()

    # H:M:S
    dt_string = str(now.strftime('%H:%M:%S'))
    print(dt_string)
    return dt_string


def finding_averages_per_second(date_time, data):
    """Averages the data logged per second"""

    # Removing all zero data points from the data
    x = len(date_time)
    noZeros = []
    newTime = []
    for i in range(x):
        if (data[i] != 0 or data[i] != 1):
            noZeros.append(data[i])
            newTime.append(date_time[i])
    data = noZeros
    date_time = newTime

    sums = 0
    count = 0
    current_sec = date_time[0]
    averaged_data = []
    seconds = []
    # Averaging out all the data for each second tested
    for i in range(len(date_time)):
        if(date_time[i] == current_sec):
            current_sec = date_time[i]
            sums += abs(int(data[i]))
            count += 1
        elif(date_time[i] != current_sec):
            averaged_data.append(int(sums/count))
            sums = abs(int(data[i]))
            count = 1
            seconds.append(current_sec)
            current_sec = date_time[i]
    averaged_data.append(int(sums/count))
    seconds.append(current_sec)
    return averaged_data, seconds



def continuous_quit(cmd):
    """Multithreads to check when to end data collection for continuous test"""

    inp = ""
    if(cmd == "c"):
        while inp != "q":
            inp = input()
        return False
    return False


def data_from_arduino():
    """Interprets data from the serial monitor"""
    # Main lists to store data
    data_logged = []
    date_time_array = []
    
    # Starting Arduino
    arduino_port = 'COM3'
    baud_rate = 9600
    ser = serial.Serial(arduino_port, baud_rate, timeout=1)

    print("Set test name: ")
    testName = input() # name of worksheet created
    # Clarifying the type of test to record
    cmd = input("Choose your test to start (t, c): ")
    while True:
        if (cmd == "t"): # timed test conditions
            print("You chose 't' for timed test.")
            timed = int(input("How many seconds should the test be? "))
            s = input("Start thruster then hit enter to start test.")
            ser.write(b's')
            break
        elif(cmd == "c"): # continous test conditions
            print("You chose 'c' for continuous test.")
            print("Press 'q' to end testing.")
            s = input("Start thruster then hit enter to start test.")
            ser.write(b's')
            break
        else:
            print("invalid input")
            cmd = input()

    # buffer for receiving data
    buffer_size = 16
    buffer = bytearray()

    # starting timey
    start_time = time.time()
    testing = True

    # initial threading for if c is called
    t1 = threading.Thread(target=continuous_quit, args=(cmd))

    # to read and reset data received
    while testing:

    # Read data from Arduino
        data = ser.read(buffer_size)

        # Add the received data to the buffer
        buffer.extend(data)

        # Process complete messages in the buffer
        while b'\n' in buffer:
            message, buffer = buffer.split(b'\n', 1)
            decoded_message = message.decode().strip()
            print("Data received from Arduino:", decoded_message)

            # Storing collected data
            date_time_array.append(get_the_date_and_time())
            data_logged.append(float(decoded_message))
            
            # Conditions to end code
            # for timed testing
            if(cmd == "t"):
                if (time.time() >=start_time + timed):
                    testing = False
                    # averaging the data collected for each second of trials
                    data_logged, date_time_array = finding_averages_per_second(date_time_array, data_logged)
                    ser.write(b'q')
                    break
            
            # for continuous testing
            elif(cmd == "c"):
                if(t1 == False):
                    testing = False

                    # rejoining the quit thread when called
                    t1.join()
                    print("Second Thread closed Successfully")
                    ser.write(b'q')
                    break

    # closes serial port to Arduino
    ser.close()   

    # pushing data to API services
    push_data_to_cloud(data_logged, date_time_array,  cmd, testName)

    # Clearing Data From Lists
    data_logged.clear()
    date_time_array.clear()


# --------------------------
data_from_arduino() # ------
# --------------------------
