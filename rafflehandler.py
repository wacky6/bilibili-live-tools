from online_net import OnlineNet
from statistics import Statistics
import printer
import utils
import asyncio
import time
import random
from bilitimer import BiliTimer


def CurrentTime():
    currenttime = int(time.time())
    return currenttime


class Rafflehandler:
    __slots__ = ('queue_raffle', 'list_raffle_id')
    instance = None

    def __new__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(Rafflehandler, cls).__new__(cls, *args, **kw)
            cls.instance.queue_raffle = asyncio.Queue()
            cls.instance.list_raffle_id = []
        return cls.instance

    async def run(self):
        while True:
            raffle = await self.queue_raffle.get()
            await asyncio.sleep(0.5)
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
    async def Put2Queue_wait(value, func):
        # print('welcome to appending')
        await Rafflehandler.instance.queue_raffle.put((value, func))
        # print('appended')
        return

    @staticmethod
    def getlist():
        print('目前TV任务队列状况', Rafflehandler.instance.queue_raffle.qsize())

    def add2raffle_id(self, raffle_id):
        self.list_raffle_id.append(raffle_id)
        if len(self.list_raffle_id) > 150:
            # print(self.list_raffle_id)
            del self.list_raffle_id[:75]
            # print(self.list_raffle_id)

    def check_duplicate(self, raffle_id):
        return (raffle_id in self.list_raffle_id)


async def handle_1_TV_raffle(num, raffle_type, real_roomid, raffleid):
    while True:
        printer.info([f'参与房间{real_roomid:^9}的 {raffle_type} 抽奖：{raffleid}'], True)
        json_response2 = await OnlineNet().req('get_gift_of_TV', raffle_type, real_roomid, raffleid)
        code = json_response2['code']
        if not code:
            break
        elif code == -403:
            return True
        elif code == -405:
            print('没抢到。。。。。')
            printer.warn(f'{raffleid}  {raffle_type} {num}')
            return False
        elif code == -400:
            print(json_response2)
            return
        elif code != -401 and code != -403:
            print(json_response2)
            return

    printer.info([f'房间{real_roomid:^9}的抽奖：{raffleid} = {json_response2["msg"]}'], True)
    return True


async def handle_1_guard_raffle(num, roomid, raffleid):
    await asyncio.sleep(random.uniform(0.5, min(30, num * 1.3)))
    json_response2 = await OnlineNet().req('get_gift_of_guard', roomid, raffleid)
    # print(json_response2)
    if not json_response2['code']:
        print("# 获取到房间 %s 的提督/舰长奖励: " % (roomid), json_response2['data']['message'])
        # print(json_response2)
        Statistics.append_to_guardlist()
    else:
        print(json_response2)
    return True

async def handle_1_storm_raffle(id):
    json_response1 = await OnlineNet().req('get_gift_of_storm', id)
    print(json_response1)

async def handle_1_room_TV(real_roomid):
    result = await utils.enter_room(real_roomid)
    if not result:
        return None

    json_response = await OnlineNet().req('get_giftlist_of_TV', real_roomid)
    current_time = CurrentTime()
    checklen = json_response['data']['list']
    if not checklen:
        return None

    list_available_raffleid = []
    for j in checklen:
        raffle_id = j['raffleId']
        raffle_type = j['type']
        time_wanted = j['time_wait'] + current_time
        # 处理一些重复
        if not Rafflehandler().check_duplicate(raffle_id):
            list_available_raffleid.append((raffle_id, raffle_type, time_wanted))
            Rafflehandler().add2raffle_id(raffle_id)

    num_available = len(list_available_raffleid)
    # print(list_available_raffleid)
    for raffle_id, raffle_type, time_wanted in list_available_raffleid:
        BiliTimer.append2list_jobs(handle_1_TV_raffle, time_wanted, (num_available, raffle_type, real_roomid, raffle_id))

async def handle_1_room_storm(roomid):
    result = await utils.enter_room(roomid)
    if result:
        temp = await OnlineNet().req('get_giftlist_of_storm', roomid)
        check = len(temp['data'])
        list_available_raffleid = []
        if check != 0 and temp['data']['hasJoin'] != 1:
            id = temp['data']['id']
            list_available_raffleid.append((id, 0))
        for id, time_wanted in list_available_raffleid:
            BiliTimer.append2list_jobs(handle_1_storm_raffle, time_wanted, (id,))

async def handle_1_room_guard(roomid, raffleid=None):
    result = await utils.enter_room(roomid)
    if result:
        if raffleid is not None:
            json_response1 = {'data': [{'id': raffleid}]}
        else:
            for i in range(10):
                json_response1 = await OnlineNet().req('get_giftlist_of_guard', roomid)
                # print(json_response1)
                if not json_response1['data']:
                    await asyncio.sleep(1)
                else:
                    break
            if not json_response1['data']:
                print(f'{roomid}没有guard或者guard已经领取')
                return
        list_available_raffleid = []
        # guard这里领取后，list对应会消失，其实就没有status了，这里是为了统一
        for j in json_response1['data']:
            raffle_id = j['id']
            if not Rafflehandler().check_duplicate(raffle_id):
                # print(raffle_id)
                list_available_raffleid.append(raffle_id)
                Rafflehandler().add2raffle_id(raffle_id)

        tasklist = []
        num_available = len(list_available_raffleid)
        for raffleid in list_available_raffleid:
            task = asyncio.ensure_future(handle_1_guard_raffle(num_available, roomid, raffleid))
            tasklist.append(task)
        if tasklist:
            raffle_results = await asyncio.gather(*tasklist)
            if False in raffle_results:
                print('有繁忙提示，稍后重新尝试')
                Rafflehandler.Put2Queue((roomid,), handle_1_room_guard)

