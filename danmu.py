from statistics import Statistics
import printer
import rafflehandler
from configloader import ConfigLoader
import utils
import asyncio
import struct
import json
import sys
import aiohttp
                                                          

class BaseDanmu():
    
    __slots__ = ('ws', 'roomid', 'area_id', 'client')
    structer = struct.Struct('!I2H2I')

    def __init__(self, roomid=None, area_id=None):
        self.client = aiohttp.ClientSession()
        if roomid is None:
            self.roomid = ConfigLoader().dic_user['other_control']['default_monitor_roomid']
            self.area_id = 0
        else:
            self.roomid = roomid
            self.area_id = area_id

    # 待确认
    async def terminate(self):
        try:
            await self.ws.close()
        except:
            print('请联系开发者', sys.exc_info()[0], sys.exc_info()[1])
        if not self.ws.closed:
            printer.info([f'请联系开发者  {self.area_id}号弹幕收尾模块状态{self.ws.closed}'], True)
        
    async def start(self):
        try:
            url = 'wss://broadcastlv.chat.bilibili.com:443/sub'
            
            self.ws = await asyncio.wait_for(self.client.ws_connect(url), timeout=3)
        except:
            print("# 连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        printer.info([f'{self.area_id}号弹幕监控已连接b站服务器'], True)
        body = f'{{"uid":0,"roomid":{self.roomid},"protover":1,"platform":"web","clientver":"1.3.3"}}'
        return (await self.__send_msg(opt=7, body=body))

    async def heart_beat(self):
        try:
            while True:
                if not (await self.__send_msg(opt=2, body='')):
                    return
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass

    async def __send_msg(self, opt, body, len_header=16, ver=1, seq=1):
        remain_data = body.encode('utf-8')
        len_data = len(remain_data) + len_header
        header = self.structer.pack(len_data, len_header, ver, opt, seq)
        data = header + remain_data
        try:
            await self.ws.send_bytes(data)
        except asyncio.CancelledError:
            return False
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        return True

    async def __read_msg(self):
        bytes_data = None
        try:
            msg = await asyncio.wait_for(self.ws.receive(), timeout=35.0)
            bytes_data = msg.data
        except asyncio.TimeoutError:
            print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            return None
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            print('请联系开发者')
            return None
        
        return bytes_data
    
    async def handle_msg(self):
        while True:
            bytes_datas = await self.__read_msg()
            if bytes_datas is None:
                return
            len_read = 0
            len_bytes_datas = len(bytes_datas)
            while len_read != len_bytes_datas:
                split_header = self.structer.unpack(bytes_datas[len_read:16+len_read])
                len_data, len_header, ver, opt, seq = split_header
                remain_data = bytes_datas[len_read+16:len_read+len_data]
                # 人气值/心跳 3s间隔
                if opt == 3:
                    # self._UserCount, = struct.unpack('!I', remain_data)
                    printer.debug(f'弹幕心跳检测{self.area_id}')
                # cmd
                elif opt == 5:
                    if not self.handle_danmu(remain_data):
                        return
                # 握手确认
                elif opt == 8:
                    printer.info([f'{self.area_id}号弹幕监控进入房间（{self.roomid}）'], True)
                else:
                    printer.warn(bytes_datas[len_read:len_read + len_data])

                len_read += len_data
                
    def handle_danmu(self, bytes_msg):
        return True
                
                
class DanmuPrinter(BaseDanmu):
    def handle_danmu(self, bytes_msg):
        dic = json.loads(bytes_msg.decode('utf-8'))
        cmd = dic['cmd']
        # print(cmd)
        if cmd == 'DANMU_MSG':
            # print(dic)
            printer.print_danmu(dic)
        return True

        
class DanmuRaffleHandler(BaseDanmu):
    async def check_area(self):
        try:
            while True:
                area_id = await asyncio.shield(utils.FetchRoomArea(self.roomid))
                if area_id != self.area_id:
                    printer.info([f'{self.roomid}更换分区{self.area_id}为{area_id}，即将切换房间'], True)
                    return
                await asyncio.sleep(300)
        except asyncio.CancelledError:
            pass
        
    def handle_danmu(self, bytes_msg):
        dic = json.loads(bytes_msg.decode('utf-8'))
        cmd = dic['cmd']
        
        if cmd == 'PREPARING':
            printer.info([f'{self.area_id}号弹幕监控房间下播({self.roomid})'], True)
            return False
    
        elif cmd == 'NOTICE_MSG':
            # 1 《第五人格》哔哩哔哩直播预选赛六强诞生！
            # 3 <%暗月柴静%> 在 <%優しい七酱%> 的房间开通了总督并触发了抽奖，点击前往TA的房间去抽奖吧
            # 4 欢迎 <%总督 不再瞎逛的菜菜大佬%> 登船
            # 5 恭喜 <%ChineseHerbalTea%> 获得大奖 <%23333x银瓜子%>, 感谢 <%樱桃小姐姐给幻幻子穿上漂亮的裙裙%> 的赠送
            # 6 <%雪昼%> 在直播间 <%529%> 使用了 <%20%> 倍节奏风暴，大家快去跟风领取奖励吧！ (只报20的)
            # 2 全区广播：<%沉鱼落雁的吃藕妹%>送给<%聆桑哟%>1个嗨翻全城，快来抽奖吧
            msg_type = dic['msg_type']
            msg_common = dic['msg_common']
            real_roomid = dic['real_roomid']
            msg_common = dic['msg_common'].replace(' ', '')
            if msg_type == 2:
                str_gift = msg_common.split('%>')[-1].split('，')[0]
                if '个' in str_gift:
                    raffle_num, raffle_name = str_gift.split('个')
                elif '了' in str_gift:
                    raffle_num = 1
                    raffle_name = str_gift.split('了')[-1]
                else:
                    raffle_num = 1
                    raffle_name = str_gift
                broadcast = msg_common.split('广播')[0]
                printer.info([f'{self.area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'], True)
                rafflehandler.Rafflehandler.Put2Queue((real_roomid,), rafflehandler.handle_1_room_TV)
                broadcast_type = 0 if broadcast == '全区' else 1
                Statistics.add2pushed_raffle(raffle_name, 1, broadcast_type)
            elif msg_type == 3:
                raffle_name = msg_common.split('开通了')[-1][:2]
                printer.info([f'{self.area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'], True)
                rafflehandler.Rafflehandler.Put2Queue((real_roomid,), rafflehandler.handle_1_room_guard)
                broadcast_type = 0 if raffle_name == '总督' else 2
                Statistics.add2pushed_raffle(raffle_name, 1, broadcast_type)
            elif msg_type == 6:
                printer.info(["20倍节奏风暴"], True)
                rafflehandler.Rafflehandler.Put2Queue((real_roomid,), rafflehandler.handle_1_room_storm)
                Statistics.add2pushed_raffle('20倍节奏风暴')
        
        return True
            
        
class YjMonitorHandler(BaseDanmu):
    digs = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    def base2dec(self, str_num, base=62):
        result = 0
        for i in str_num:
            result = result * base + self.digs.index(i)
        return result
    
    def get_origin(self, words, gap):
        return map(self.base2dec, words.replace('?', '').split(gap))
        
    def handle_danmu(self, bytes_msg):
        dic = json.loads(bytes_msg.decode('utf-8'))
        cmd = dic['cmd']
        # print(cmd)
        if cmd == 'DANMU_MSG':
            msg = dic['info'][1]
            if '+' in msg:
                try:
                    roomid, raffleid = self.get_origin(msg, '+')
                    printer.info([f'弹幕监控检测到{roomid:^9}的提督/舰长{raffleid}'], True)
                    rafflehandler.Rafflehandler.Put2Queue((roomid, raffleid), rafflehandler.handle_1_room_guard)
                    Statistics.add2pushed_raffle('YJ推送提督/舰长', 1, 2)
                except ValueError:
                    print(msg)
            printer.print_danmu(dic)
        return True
                    
                    
               
    
