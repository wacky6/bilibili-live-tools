import OnlineHeart
import Silver
import Tasks
import connect
from rafflehandler import Rafflehandler
import asyncio
import printer
from statistics import Statistics
from bilibili import bilibili
from configloader import ConfigLoader
import threading
import os
import online_net
import bili_console
from bilitimer import BiliTimer


loop = asyncio.get_event_loop()
fileDir = os.path.dirname(os.path.realpath('__file__'))

conf = ConfigLoader(fileDir)
area_ids = conf.dic_user['other_control']['area_ids']

# print('Hello world.')
printer.init_config()
bilibili()
online_net.login()
online_net.OnlineNet()
Statistics(len(area_ids))

rafflehandler = Rafflehandler()
var_console = bili_console.Biliconsole(loop)

list_raffle_connection = [connect.RaffleConnect(i) for i in area_ids]
list_raffle_connection_task = [i.run() for i in list_raffle_connection]
yjconnection = connect.YjConnection()

danmu_connection = connect.connect()


bili_timer = BiliTimer(loop)

console_thread = threading.Thread(target=var_console.cmdloop)

console_thread.start()

Tasks.init()
tasks = [
    OnlineHeart.run(),
    Silver.run(),
    danmu_connection.run(),
    rafflehandler.run(),
    yjconnection.run()
]
try:
    loop.run_until_complete(asyncio.wait(tasks + list_raffle_connection_task))
except KeyboardInterrupt:
    # print(sys.exc_info()[0], sys.exc_info()[1])
    if ConfigLoader().dic_user['other_control']['keep-login']:
        pass
    else:
        response = online_net.logout()
    
console_thread.join()

loop.close()
    


