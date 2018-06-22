from bilibili import bilibili
from statistics import Statistics
from printer import Printer
import utils
import asyncio
import datetime
import time
import random


def CurrentTime():
    currenttime = int(time.mktime(datetime.datetime.now().timetuple()))
    return currenttime


class Delay_Joiner:
    __slots__ = ('jobs',)
    instance = None

    def __new__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(Delay_Joiner, cls).__new__(cls, *args, **kw)
            cls.instance.jobs = asyncio.PriorityQueue()
        return cls.instance
        
    async def run(self):
        while True:
            i = await self.jobs.get()
            # print(i)
            currenttime = CurrentTime()
            sleeptime = i[0] - currenttime
            # print('智能睡眠', sleeptime)
            await asyncio.sleep(max(sleeptime, 0))
            await i[2](*i[3])
      
    @staticmethod          
    async def append2list_jobs(func, time_expected, tuple_values):
        await Delay_Joiner.instance.jobs.put((time_expected, func.__name__, func, tuple_values))
        # print('添加任务', time_expected, func.__name__, func, tuple_values)
        return
        
    @staticmethod
    def getresult():
        print('数目', Delay_Joiner.instance.jobs.qsize())
        
        
class Rafflehandler:
    __slots__ = ('queue_raffle',)
    instance = None

    def __new__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(Rafflehandler, cls).__new__(cls, *args, **kw)
            cls.instance.queue_raffle = asyncio.Queue()
        return cls.instance
        
    async def run(self):
        while True:
            raffle = await self.queue_raffle.get()
            await asyncio.sleep(3)
            list_raffle0 = [self.queue_raffle.get_nowait() for i in range(self.queue_raffle.qsize())]
            list_raffle0.append(raffle)
            list_raffle = list(set(list_raffle0))
                
            # print('过滤完毕')
            # if len(list_raffle) != len(list_raffle0):
                # print('过滤机制起作用')
            
            tasklist = []
            for i in list_raffle:
                i = list(i)
                i[0] = list(i[0])
                for j in range(len(i[0])):
                    if isinstance(i[0][j], tuple):
                        # print('检测')
                        # i[0] = list(i[0])
                        i[0][j] = await i[0][j][1](*(i[0][j][0]))
                # print(i)
                task = asyncio.ensure_future(i[1](*i[0]))
                tasklist.append(task)
            
            # await asyncio.wait(tasklist, return_when=asyncio.ALL_COMPLETED)
            
    @staticmethod
    def Put2Queue(value, func):
        # print('welcome to appending')
        Rafflehandler.instance.queue_raffle.put_nowait((value, func))
        # print('appended')
        return
            
    @staticmethod
    def getlist():
        print('目前TV任务队列状况', Rafflehandler.instance.queue_raffle.qsize())
        

async def handle_1_TV_raffle(num, real_roomid, raffleid, raffle_type):
    # print('参与', raffleid)
    
    while True:
        json_response2 = await bilibili.get_gift_of_TV_app(real_roomid, raffleid, raffle_type)
        code = json_response2['code']
        if not code:
            break
        elif code == -403:
            return True
        elif code == -405:
            print('没抢到。。。。。')
            return False
        elif code != -401 and code != -403:
            print('00', json_response2)
        await asyncio.sleep(1)
    #json_response2 = await bilibili.get_gift_of_TV(real_roomid, raffleid)
    data = json_response2['data']
    Statistics.append_to_TVlist(raffleid, real_roomid)
    Statistics.add_to_result(data['gift_name'], int(data['gift_num']))
    Printer().print_words([f'参与了房间{real_roomid:^9}的道具抽奖'], True)
    # Printer().print_words([f'# 道具抽奖状态: {json_response2["msg"]}'])
    print(f'# 房间{real_roomid:^9}网页端活动抽奖结果: {data["gift_name"]}X{data["gift_num"]}')
    return True
    # -400不存在
    # -500繁忙
    # gift_name': '辣条', 'gift_num'
    '''
    if not json_response2['code']:
        Statistics.append_to_TVlist(raffleid, real_roomid)
        return True
    elif json_response2['code'] == -500:
        print('# -500繁忙，稍后重试')
        return False
    else:
        print(json_response2)
        return True
    '''
 
               
async def handle_1_captain_raffle(num, roomid, raffleid):
    await asyncio.sleep(random.uniform(0.5, min(30, num * 1.3)))
    json_response2 = await bilibili.get_gift_of_captain(roomid, raffleid)
    if not json_response2['code']:
        print("# 获取到房间 %s 的总督奖励: " %(roomid), json_response2['data']['message'])
        Statistics.append_to_captainlist()
    else:
        print(json_response2)
    return True
 
                                       
async def handle_1_activity_raffle(num, giftId, text1, text2, raffleid):
    # print('参与')
    await asyncio.sleep(random.uniform(0.5, min(30, num * 1.3)))
    json_response1 = await bilibili.get_gift_of_events_app(text1, text2, raffleid)
    json_pc_response = await bilibili.get_gift_of_events_web(text1, text2, raffleid)
    
    Printer().print_words([f'参与了房间{text1:^9}的{bilibili.get_giftids_raffle(str(giftId))}活动抽奖'], True)

    if not json_response1['code']:
        Printer().print_words([f'# 移动端活动抽奖结果: {json_response1["data"]["gift_desc"]}'])
        Statistics.add_to_result(*(json_response1['data']['gift_desc'].split('X')))
    else:
        print(json_response1)
        Printer().print_words([f'# 移动端活动抽奖结果: {json_response1}'])
        
    Printer().print_words(
            [f'# 网页端活动抽奖状态:  {json_pc_response}'])
    if not json_pc_response['code']:
        Statistics.append_to_activitylist(raffleid, text1)
    else:
        print(json_pc_response)
    return True

                
async def handle_1_room_TV(real_roomid):
    await asyncio.sleep(random.uniform(0.5, 1.5))
    result = await utils.check_room_true(real_roomid)
    if True in result:
        Printer().print_words([f'WARNING:检测到房间{real_roomid:^9}的钓鱼操作'], True)
    else:
        # print(True)
        await bilibili.post_watching_history(real_roomid)
        json_response = await bilibili.get_giftlist_of_TV(real_roomid)
        current_time = CurrentTime()
        # print(json_response['data']['list'])
        checklen = json_response['data']['list']
        list_available_raffleid = []
        for j in checklen:
            # await asyncio.sleep(random.uniform(0.5, 1))
            # resttime = j['dtime']
            raffle_id = j['raffleId']
            raffle_type = j['type']
            time_wanted = j['time_wait'] + current_time

            list_available_raffleid.append((raffle_id, raffle_type, time_wanted))
            

            # print(raffle_id, raffle_type)
        num_available = len(list_available_raffleid)
        # print(list_available_raffleid)
        for raffle_id, raffle_type, time_wanted in list_available_raffleid:
            await Delay_Joiner.append2list_jobs(handle_1_TV_raffle, time_wanted, (num_available, real_roomid, raffle_id, raffle_type))

async def handle_1_room_activity(giftId, text1, text2):
    await asyncio.sleep(random.uniform(0.5, 1.5))
    result = await utils.check_room_true(text1)
    if True in result:
        Printer().print_words([f'WARNING:检测到房间{text1:^9}的钓鱼操作'], True)
    else:
        # print(True)
        await bilibili.post_watching_history(text1)
        json_response = await bilibili.get_giftlist_of_events(text1)
        checklen = json_response['data']
        list_available_raffleid = []
        for j in checklen:
            # await asyncio.sleep(random.uniform(0.5, 1))
            resttime = j['time']
            raffleid = j['raffleId']
            if Statistics.check_activitylist(text1, raffleid):
                list_available_raffleid.append(raffleid)
        tasklist = []
        num_available = len(list_available_raffleid)
        for raffleid in list_available_raffleid:
            task = asyncio.ensure_future(handle_1_activity_raffle(num_available, giftId, text1, text2, raffleid))
            tasklist.append(task)
        if tasklist:
            raffle_results = await asyncio.gather(*tasklist)
            if False in raffle_results:
                print('有繁忙提示，稍后重新尝试')
                Rafflehandler.Put2Queue((giftId, text1, text2), handle_1_room_activity)
            

async def handle_1_room_captain(roomid):
    await asyncio.sleep(random.uniform(0.5, 1.5))
    result = await utils.check_room_true(roomid)
    if True in result:
        Printer().print_words([f'WARNING:检测到房间{roomid:^9}的钓鱼操作'], True)
    else:
        # print(True)
        await bilibili.post_watching_history(roomid)
        num = 0
        while True:
            json_response1 = await bilibili.get_giftlist_of_captain(roomid)
            # print(json_response1)
            num = len(json_response1['data']['guard'])
            if not num:
                await asyncio.sleep(5)
            else:
                break
            
        list_available_raffleid = []
        # guard这里领取后，list对应会消失，其实就没有status了，这里是为了统一
        for j in json_response1['data']['guard']:
            id = j['id']
            status = j['status']
            if status == 1:
                # print('未参加')
                list_available_raffleid.append(id)
            elif status == 2:
                # print('过滤')
                pass
            else:
                print(json_response1)
            
        tasklist = []
        num_available = len(list_available_raffleid)
        for raffleid in list_available_raffleid:
            task = asyncio.ensure_future(handle_1_captain_raffle(num_available, roomid, raffleid))
            tasklist.append(task)
        if tasklist:
            raffle_results = await asyncio.gather(*tasklist)
            if False in raffle_results:
                print('有繁忙提示，稍后重新尝试')
                Rafflehandler.Put2Queue((roomid,), handle_1_room_captain)
                
         

