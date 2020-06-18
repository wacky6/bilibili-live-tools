from statistics import Statistics
import printer
import rafflehandler
import utils
import asyncio
import struct
import json
import sys
import aiohttp
import zlib


class BaseDanmu():
    structer = struct.Struct('!I2H2I')

    def __init__(self, room_id, area_id):
        self.client = aiohttp.ClientSession()
        self._area_id = area_id
        self.room_id = room_id
        self._bytes_heartbeat = self._wrap_str(opt=2, body='')

    @property
    def room_id(self):
        # 仅仅为了借用roomi_id.setter，故不设置
        pass

    @room_id.setter
    def room_id(self, room_id):
        self._room_id = room_id
        str_conn_room = f'{{"uid":0,"roomid":{room_id},"protover":1,"platform":"web","clientver":"1.3.3"}}'
        self._bytes_conn_room = self._wrap_str(opt=7, body=str_conn_room)

    def _wrap_str(self, opt, body, len_header=16, ver=1, seq=1):
        remain_data = body.encode('utf-8')
        len_data = len(remain_data) + len_header
        header = self.structer.pack(len_data, len_header, ver, opt, seq)
        data = header + remain_data
        return data

    async def _send_bytes(self, bytes_data):
        try:
            await self.ws.send_bytes(bytes_data)
        except asyncio.CancelledError:
            return False
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        return True

    async def _read_bytes(self):
        bytes_data = None
        try:
            # 如果调用aiohttp的bytes read，none的时候，会raise exception
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

    async def open(self):
        try:
            url = 'wss://broadcastlv.chat.bilibili.com:443/sub'
            self.ws = await asyncio.wait_for(self.client.ws_connect(url), timeout=3)
        except:
            print("# 连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        return (await self._send_bytes(self._bytes_conn_room))

    async def heart_beat(self):
        try:
            while True:
                if not (await self._send_bytes(self._bytes_heartbeat)):
                    return
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass

    async def read_datas(self):
        while True:
            datas = await self._read_bytes()
            # 本函数对bytes进行相关操作，不特别声明，均为bytes
            if datas is None:
                return
            data_l = 0
            len_datas = len(datas)
            while data_l != len_datas:
                # 每片data都分为header和body，data和data可能粘连
                # data_l == header_l && next_data_l = next_header_l
                # ||header_l...header_r|body_l...body_r||next_data_l...
                tuple_header = self.structer.unpack_from(datas[data_l:])
                len_data, len_header, ver, opt, seq = tuple_header
                body_l = data_l + len_header
                next_data_l = data_l + len_data

                if ver == 2:
                    # handle ver 2 zlib gibberish, insert decompressed data to datas
                    decompressed = zlib.decompress(datas[body_l:next_data_l])
                    datas = decompressed + datas[next_data_l:]
                    data_l = 0
                    len_datas = len(datas)
                    continue
                else:
                    # ver 0 and ver 1 doesn't need decompression
                    body_l = data_l + len_header
                    next_data_l = data_l + len_data
                    body = datas[body_l:next_data_l]

                # 人气值(或者在线人数或者类似)以及心跳
                if opt == 3:
                    # UserCount, = struct.unpack('!I', remain_data)
                    printer.debug(f'弹幕心跳检测{self._area_id}')
                # cmd
                elif opt == 5:
                    if not self.handle_danmu(body):
                        return
                # 握手确认
                elif opt == 8:
                    printer.info([f'{self._area_id}号弹幕监控进入房间（{self._room_id}）'], True)
                else:
                    printer.warn(datas[data_l:next_data_l])

                data_l = next_data_l

    # 待确认
    async def close(self):
        try:
            await self.ws.close()
        except:
            print('请联系开发者', sys.exc_info()[0], sys.exc_info()[1])
        if not self.ws.closed:
            printer.info([f'请联系开发者  {self._area_id}号弹幕收尾模块状态{self.ws.closed}'], True)

    def handle_danmu(self, body):
        return True


class DanmuPrinter(BaseDanmu):
    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
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
                is_ok = await asyncio.shield(utils.check_room_for_danmu(self._room_id, self._area_id))
                if not is_ok:
                    printer.info([f'{self._room_id}不再适合作为监控房间，即将切换'], True)
                    return
                await asyncio.sleep(300)
        except asyncio.CancelledError:
            pass

    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
        cmd = dic['cmd']

        if cmd == 'PREPARING':
            printer.info([f'{self._area_id}号弹幕监控房间下播({self._room_id})'], True)
            return False

        elif cmd == 'NOTICE_MSG':
            # 1 《第五人格》哔哩哔哩直播预选赛六强诞生！
            # 2 全区广播：<%user_name%>送给<%user_name%>1个嗨翻全城，快来抽奖吧
            # 3 <%user_name%> 在 <%user_name%> 的房间开通了总督并触发了抽奖，点击前往TA的房间去抽奖吧
            # 4 欢迎 <%总督 user_name%> 登船
            # 5 恭喜 <%user_name%> 获得大奖 <%23333x银瓜子%>, 感谢 <%user_name%> 的赠送
            # 6 <%user_name%> 在直播间 <%529%> 使用了 <%20%> 倍节奏风暴，大家快去跟风领取奖励吧！(只报20的)
            # 8 全区广播：主播<%红莉栖魔王喵%>开启了“任意门”，点击前往TA的房间去抽奖吧！
            msg_type = dic['msg_type']
            msg_common = dic['msg_common']
            real_roomid = dic['real_roomid']
            msg_common = dic['msg_common'].replace(' ', '')
            msg_common = msg_common.replace('”', '')
            msg_common = msg_common.replace('“', '')
            if msg_type == 2 or msg_type == 8:
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
                printer.info([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'], True)
                rafflehandler.Rafflehandler.Put2Queue((real_roomid,), rafflehandler.handle_1_room_TV)
                broadcast_type = 0 if broadcast == '全区' else 1
                Statistics.add2pushed_raffle(raffle_name, broadcast_type)
            elif msg_type == 3:
                raffle_name = msg_common.split('开通了')[-1][:2]
                printer.info([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'], True)
                rafflehandler.Rafflehandler.Put2Queue((real_roomid,), rafflehandler.handle_1_room_guard)
                broadcast_type = 0 if raffle_name == '总督' else 2
                Statistics.add2pushed_raffle(raffle_name, broadcast_type)
            elif msg_type == 6:
                raffle_name = '二十倍节奏风暴'
                printer.info([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'], True)
                rafflehandler.Rafflehandler.Put2Queue((real_roomid,), rafflehandler.handle_1_room_storm)
                Statistics.add2pushed_raffle(raffle_name)

        return True


class YjMonitorHandler(BaseDanmu):
    def __init__(self, room_id, area_id):
        super().__init__(room_id, area_id)
        keys = '阝飠牜饣卩卪厸厶厽孓宀巛巜彳廴彡彐忄扌攵氵灬爫犭疒癶礻糹纟罒罓耂虍訁覀兦亼亽亖亗吂卝匸皕旡玊尐幵朩囘囙囜囝囟囡団囤囥囦囧囨囩囪囫囬囮囯困囱囲図囵囶囷囸囹固囻囼图囿圀圁圂圃圄圅圆圇圉圊圌圍圎圏圐圑園圓圔圕圖圗團圙圚圛圜圝圞'
        self.__reverse_keys = {value: i for i, value in enumerate(keys)}
        self.__read = {}

    def __base2dec(self, str_num, base=110):
        result = 0
        for i in str_num:
            result = result * base + self.__reverse_keys[i]
        return result

    def __reverse(self, msg):
        msg = msg.replace('?', '')
        first = self.__reverse_keys.get(msg[0], -1)
        last = self.__reverse_keys.get(msg[-1], -1)

        # 校验
        if 0 <= first <= 109 and 0 <= last <= 109 and not (first + last - 109):
            type = msg[-2]
            msg_id, id = map(self.__base2dec, msg[:-2].split('.'))
            return msg_id, type, id
        return None

    def __combine_piece(self, uid, msg):
        # None/''
        if not msg:
            return None
        if uid not in self.__read:
            self.__read[uid] = {}
        user_danmus = self.__read[uid]
        msg_id, type, id = msg
        msg_id_wanted = (msg_id - 1) if (msg_id % 2) else (msg_id + 1)
        id_wanted = user_danmus.pop(msg_id_wanted, None)
        if id_wanted is not None:
            if msg_id % 2:
                return type, id_wanted, id
            else:
                return type, id, id_wanted
        else:
            user_danmus[msg_id] = id
            return None

    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
        cmd = dic['cmd']
        # print(cmd)
        if cmd == 'DANMU_MSG':
            info = dic['info']
            ori = info[1]
            uid = info[2][0]
            # print(ori)
            try:
                msg = self.__reverse(ori)
                '''
                if msg is not None:
                    msg_id, type, id = msg
                    if type == '~' and not msg_id % 2:
                        storm_id = id
                        print('节奏风暴', storm_id)
                        rafflehandler.Rafflehandler.Put2Queue((storm_id,), rafflehandler.handle_1_storm_raffle)
                '''

                result = self.__combine_piece(uid, msg)
                # print('监控read dic', self.__read)
                if result is None:
                    return True
                # print(result)
                type, raffle_id, room_id = result
                if type == '+':
                    printer.info([f'{self._area_id}号弹幕监控检测到{room_id:^9}的大航海(id: {raffle_id})'], True)
                    rafflehandler.Rafflehandler.Put2Queue((room_id, raffle_id), rafflehandler.handle_1_room_guard)
                    Statistics.add2pushed_raffle('Yj协同大航海', 2)
            except Exception:
                printer.warn(f'Yj监控房间内可能有恶意干扰{uid}: {ori}')
        return True




