from datetime import datetime

def get_work_time():
    now_time = datetime.now()

    weekday = now_time.weekday()

    if weekday in [0, 1, 2, 3, 4] and now_time.replace(hour=9)<now_time<now_time.replace(hour=18) or weekday==5 and now_time.replace(hour=10)<now_time<now_time.replace(hour=14):
        return True
    
    return False