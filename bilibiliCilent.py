from bilibili import bilibili
from statistics import Statistics
from printer import Printer
import rafflehandler
from configloader import ConfigLoader
import utils
import asyncio
import websockets
import struct
import json
import re
import sys


async def DanMuraffle(area_id, connect_roomid, messages):
    dic = json.loads(messages)
    cmd = dic['cmd']
    
    if cmd == 'PREPARING':
        Printer().print_words([f'{area_id}分区检测器下播！将切换监听房间'], True)
        return False
    elif cmd == 'SYS_GIFT':
        if 'giftId' in dic:
            if str(dic['giftId']) in bilibili.get_giftids_raffle_keys():
                
                text1 = dic['real_roomid']
                text2 = dic['url']
                giftId = dic['giftId']
                Printer().print_words(["检测到房间{:^9}的{}活动抽奖".format(text1, bilibili.get_giftids_raffle(str(giftId)))], True)
                rafflehandler.Rafflehandler.Put2Queue((giftId, text1, text2), rafflehandler.handle_1_room_activity)
                Statistics.append2pushed_raffle('活动', area_id=area_id)
                        
            elif dic['giftId'] == 39:
                Printer().print_words(["节奏风暴"], True)
                temp = await bilibili.get_giftlist_of_storm(dic)
                check = len(temp['data'])
                if check != 0 and temp['data']['hasJoin'] != 1:
                    id = temp['data']['id']
                    json_response1 = await bilibili.get_gift_of_storm(id)
                    print(json_response1)
                else:
                    Printer().print_words([dic, "请联系开发者"])
            else:
                text1 = dic['real_roomid']
                text2 = dic['url']
                Printer().print_words([dic, "请联系开发者"])
                try:
                    giftId = dic['giftId']
                    Printer().print_words(["检测到房间{:^9}的{}活动抽奖".format(text1, bilibili.get_giftids_raffle(str(giftId)))], True)
                    rafflehandler.Rafflehandler.Put2Queue((giftId, text1, text2), rafflehandler.handle_1_room_activity)
                    Statistics.append2pushed_raffle('活动', area_id=area_id)
                            
                except:
                    Printer().print_words([dic, "请联系开发者"])
                
        else:
            Printer().print_words(['普通送礼提示', dic['msg_text']])
        return
    elif cmd == 'SYS_MSG':
        if 'real_roomid' in dic:
            real_roomid = dic['real_roomid']
            type_text = (dic['msg'].split(':?')[-1]).split('，')[0].replace('一个', '')
            Printer().print_words([f'{area_id}号检测到{real_roomid:^9}的{type_text}'], True)
            rafflehandler.Rafflehandler.Put2Queue((real_roomid,), rafflehandler.handle_1_room_TV)
            Statistics.append2pushed_raffle(type_text, area_id=area_id)
            
    elif cmd == 'GUARD_MSG':
        a = re.compile(r"(?<=在主播 )\S+(?= 的直播间开通了总督)")
        res = re.search(a, dic['msg'])
        if res is not None:
            name = str(res.group())
            Printer().print_words([f'{area_id}号检测到{name:^9}的总督'], True)
            rafflehandler.Rafflehandler.Put2Queue((((name,), utils.find_live_user_roomid),), rafflehandler.handle_1_room_captain)
            Statistics.append2pushed_raffle('总督', area_id=area_id)
        
  
def printDanMu(area_id, messages):
    dic = json.loads(messages)
    cmd = dic['cmd']
    # print(cmd)
    if cmd == 'DANMU_MSG':
        # print(dic)
        Printer().print_danmu(dic)
        return
                                                          

class bilibiliClient():
    
    __slots__ = ('ws', 'connected', 'roomid', 'raffle_handle', 'area_id')

    def __init__(self, roomid=None, area_id=None):
        self.ws = None
        self.connected = False
        if roomid is None:
            self.roomid = ConfigLoader().dic_user['other_control']['default_monitor_roomid']
            self.area_id = 0
            self.raffle_handle = False
        else:
            self.roomid = roomid
            self.area_id = area_id
            self.raffle_handle = True

    # 待确认
    async def close_connection(self):
        try:
            await self.ws.close()
        except:
            print('请联系开发者', sys.exc_info()[0], sys.exc_info()[1])
        self.connected = False
        
    async def CheckArea(self):
        while self.connected:
            area_id = await utils.FetchRoomArea(self.roomid)
            if area_id != self.area_id:
                print(f'{self.roomid}更换分区{self.area_id}为{area_id}，即将切换房间')
                break
            await asyncio.sleep(300)
        
    async def connectServer(self):
        try:
            self.ws = await websockets.connect('wss://broadcastlv.chat.bilibili.com:2245/sub')
        except:
            print("# 连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        # print('测试点')
        if (await self.SendJoinChannel(self.roomid)):
            self.connected = True
            Printer().print_words([f'连接弹幕服务器{self.roomid}成功'], True)
            return True

    async def HeartbeatLoop(self):
        Printer().print_words(['直播间弹幕心跳（由于该心跳间隔为30s，所以后续不再提示）'], True)
        while self.connected:
            await self.SendSocketData(opt=2, body='')
            await asyncio.sleep(30)

    async def SendJoinChannel(self, channelId):
        body = f'{{"uid":0,"roomid":{channelId},"protover":1,"platform":"web","clientver":"1.3.3"}}'
        await self.SendSocketData(opt=7, body=body)
        return True

    async def SendSocketData(self, opt, body, len_header=16, ver=1, seq=1):
        bytearr = body.encode('utf-8')
        len_data = len(bytearr) + len_header
        sendbytes = struct.pack('!IHHII', len_data, len_header, ver, opt, seq)
        sendbytes = sendbytes + bytearr
        try:
            await self.ws.send(sendbytes)
        except websockets.exceptions.ConnectionClosed:
            print("# 主动关闭或者远端主动关闭.")
            await self.ws.close()
            self.connected = False
            return None
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            self.connected = False

    async def ReadSocketData(self):
        bytes_data = None
        try:
            bytes_data = await asyncio.wait_for(self.ws.recv(), timeout=35.0)
        except asyncio.TimeoutError:
            print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            await self.ws.close()
            self.connected = False
            return None
        except websockets.exceptions.ConnectionClosed:
            print("# 主动关闭或者远端主动关闭")
            await self.ws.close()
            await self.ws.close()
            self.connected = False
            return None
        except:
            # websockets.exceptions.ConnectionClosed'>
            print(sys.exc_info()[0], sys.exc_info()[1])
            print('请联系开发者')
            await self.ws.close()
            self.connected = False
            return None
        # print(tmp)
           
        # print('测试0', bytes_data)
        return bytes_data
    
    async def ReceiveMessageLoop(self):
        if self.raffle_handle:
            while self.connected:
                bytes_datas = await self.ReadSocketData()
                if bytes_datas is None:
                    break
                len_read = 0
                len_bytes_datas = len(bytes_datas)
                while len_read != len_bytes_datas:
                    state = None
                    split_header = struct.unpack('!I2H2I', bytes_datas[len_read:16+len_read])
                    len_data, len_header, ver, opt, seq = split_header
                    remain_data = bytes_datas[len_read+16:len_read+len_data]
                    # 人气值/心跳 3s间隔
                    if opt == 3:
                        # self._UserCount, = struct.unpack('!I', remain_data)
                        pass
                    # cmd
                    elif opt == 5:
                        messages = remain_data.decode('utf-8')
                        state = await DanMuraffle(self.area_id, self.roomid, messages)
                    # 握手确认
                    elif opt == 8:
                        pass
                    else:
                        self.connected = False
                        Printer().print_warning(bytes_datas[len_read:len_read + len_data])
                                
                    if state is not None and not state:
                        return
                    len_read += len_data
                    
        else:
            while self.connected:
                bytes_datas = await self.ReadSocketData()
                if bytes_datas is None:
                    break
                len_read = 0
                len_bytes_datas = len(bytes_datas)
                while len_read != len_bytes_datas:
                    state = None
                    split_header = struct.unpack('!I2H2I', bytes_datas[len_read:16+len_read])
                    len_data, len_header, ver, opt, seq = split_header
                    remain_data = bytes_datas[len_read+16:len_read+len_data]
                    # 人气值/心跳 3s间隔
                    if opt == 3:
                        # self._UserCount, = struct.unpack('!I', remain_data)
                        pass
                    # cmd
                    elif opt == 5:
                        messages = remain_data.decode('utf-8')
                        state = printDanMu(self.area_id, messages)
                    # 握手确认
                    elif opt == 8:
                        pass
                    else:
                        self.connected = False
                        Printer().print_warning(bytes_datas[len_read:len_read + len_data])
                                
                    if state is not None and not state:
                        return
                    len_read += len_data
                  
                    
                    
               
    
