import asyncio
import utils
import danmu
import printer
from online_net import OnlineNet
from configloader import ConfigLoader
import random
import math
import traceback

async def get_one(areaid):
    # 1 娱乐分区, 2 游戏分区, 3 手游分区, 4 绘画分区
    while True:
        json_rsp = await OnlineNet().req('req_realroomid', areaid)
        data = json_rsp['data']
        if not data:
            await asyncio.sleep(3)
            printer.warn(json_rsp)
            continue

        # choose candidate rooms
        n_candidates = max(1, math.floor(len(data) / 3))
        candidate_rooms = sorted(data, key=lambda room: int(room['online']), reverse=True)[:n_candidates]
        random.shuffle(candidate_rooms)

        for room in candidate_rooms:
            roomid = room['roomid']
            if (await utils.check_room_for_danmu(roomid, areaid)):
                return roomid


class connect():
    __slots__ = ('danmuji', 'room_id', 'area_id')
    instance = None

    def __new__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(connect, cls).__new__(cls, *args, **kw)
            cls.instance.danmuji = None
            cls.instance.room_id = 0
            cls.instance.area_id = -1
        return cls.instance

    async def run(self):
        self.room_id = ConfigLoader().dic_user['other_control']['default_monitor_roomid']
        self.danmuji = danmu.DanmuPrinter(self.room_id, self.area_id)
        time_now = 0
        while True:
            if int(utils.CurrentTime()) - time_now <= 3:
                printer.info(['当前网络不稳定，弹幕监控将自动延迟3秒后重启'], True)
                await asyncio.sleep(3)
            time_now = int(utils.CurrentTime())
            connect_results = await self.danmuji.open()
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.read_datas())
            task_heartbeat = asyncio.ensure_future(self.danmuji.heart_beat())
            tasks = [task_main, task_heartbeat]
            finished, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            printer.info(['主弹幕姬异常或主动断开，正在处理剩余信息'], True)
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            await self.danmuji.close()
            await asyncio.wait(pending)
            printer.info(['主弹幕姬退出，剩余任务处理完毕'], True)

    @staticmethod
    async def reconnect(roomid):
        ConfigLoader().dic_user['other_control']['default_monitor_roomid'] = roomid
        print('已经切换roomid')
        if connect.instance.danmuji is not None:
            connect.instance.danmuji.room_id = roomid
            await connect.instance.danmuji.close()


class RaffleConnect():
    def __init__(self, areaid):
        self.danmuji = None
        self.roomid = 0
        self.areaid = areaid

    async def run(self):
        self.danmuji = danmu.DanmuRaffleHandler(self.roomid, self.areaid)
        time_now = 0
        while True:
            if int(utils.CurrentTime()) - time_now <= 3:
                printer.info(['当前网络不稳定，弹幕监控将自动延迟3秒后重启'], True)
                await asyncio.sleep(3)
            self.danmuji.room_id = await get_one(self.areaid)
            time_now = int(utils.CurrentTime())
            connect_results = await self.danmuji.open()
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.read_datas())
            task_heartbeat = asyncio.ensure_future(self.danmuji.heart_beat())
            task_checkarea = asyncio.ensure_future(self.danmuji.check_area())
            tasks = [task_main, task_heartbeat, task_checkarea]
            finished, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            printer.info([f'{self.areaid}号弹幕姬异常或主动断开，正在处理剩余信息'], True)
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            if not task_checkarea.done():
                task_checkarea.cancel()
            await self.danmuji.close()
            await asyncio.wait(pending)
            printer.info([f'{self.areaid}号弹幕姬退出，剩余任务处理完毕'], True)


class YjConnection():
    def __init__(self):
        self.danmuji = None
        self.roomid = 0
        self.areaid = 0

    async def run(self):
        self.roomid = ConfigLoader().dic_user['other_control']['raffle_minitor_roomid']
        if not self.roomid:
            return
        self.danmuji = danmu.YjMonitorHandler(self.roomid, self.areaid)
        time_now = 0
        while True:
            if int(utils.CurrentTime()) - time_now <= 3:
                printer.info(['当前网络不稳定，弹幕监控将自动延迟3秒后重启'], True)
                await asyncio.sleep(3)
            printer.info(['正在启动Yj监控弹幕姬'], True)
            time_now = int(utils.CurrentTime())
            connect_results = await self.danmuji.open()
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.read_datas())
            task_heartbeat = asyncio.ensure_future(self.danmuji.heart_beat())
            tasks = [task_main, task_heartbeat]
            finished, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            printer.info(['Yj弹幕姬异常或主动断开，正在处理剩余信息'], True)
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            await self.danmuji.close()
            await asyncio.wait(pending)
            printer.info(['Yj弹幕姬退出，剩余任务处理完毕'], True)
