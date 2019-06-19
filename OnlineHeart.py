from online_net import OnlineNet
import time
import asyncio
import printer
from bilibili import bilibili
import utils
import traceback

had_gotted_guard = []
last_guard_room = 0

def CurrentTime():
    currenttime = int(time.time())
    return currenttime


async def heartbeat():
    printer.info(["心跳"], True)
    json_response = await OnlineNet().req('apppost_heartbeat')
    json_response = await OnlineNet().req('pcpost_heartbeat')
    json_response = await OnlineNet().req('heart_gift')
    # print('pcpost_heartbeat', json_response)

async def guard_lottery():
    global had_gotted_guard
    global last_guard_room

    guards = await bilibili().guard_list()

    for guard in guards:
        if not guard['Status']:
            continue

        GuardId = guard['GuardId']
        if GuardId not in had_gotted_guard and GuardId != 0:
            had_gotted_guard.append(GuardId)
            OriginRoomId = guard['OriginRoomId']

            if not OriginRoomId == last_guard_room:
                result = await utils.check_room_true(OriginRoomId)
                if True in result:
                    printer.info([f"检测到房间 {OriginRoomId} 的钓鱼操作"])
                    continue
                await bilibili().post_watching_history(OriginRoomId)
                last_guard_room = OriginRoomId

            response2 = await bilibili().get_gift_of_captain(OriginRoomId, GuardId)
            json_response2 = await response2.json(content_type=None)
            if json_response2['code'] == 0:
                printer.info([f"获取到房间 {OriginRoomId} 编号 {GuardId} 的上船亲密度: {json_response2['data']['message']}"])
            elif json_response2['code'] == 400 and json_response2['msg'] == "你已经领取过啦":
                printer.info([f"房间 {OriginRoomId} 编号 {GuardId} 的上船亲密度已领过"])
            elif json_response2['code'] == 400 and json_response2['msg'] == "访问被拒绝":
                printer.info([f"获取房间 {OriginRoomId} 编号 {GuardId} 的上船亲密度: {json_response2['message']}"])
                print(json_response2)
            else:
                printer.info([f"房间 {OriginRoomId} 编号 {GuardId}  的上船亲密度领取出错: {json_response2}"])
        else:
            pass

# 因为休眠时间差不多,所以放到这里,此为实验性功能
async def draw_lottery():
    blacklist = ['test', 'TEST', '测试', '加密']
    max = 10000
    min = 50
    while max > min:
        # print(min, max)
        middle = int((min + max + 1) / 2)
        code_middle = (await OnlineNet().req('get_lotterylist', middle))["code"]
        if code_middle:
            code_middle1 = (await OnlineNet().req('get_lotterylist', middle + 1))['code']
            code_middle2 = (await OnlineNet().req('get_lotterylist', middle + 2))['code']
            if code_middle1 and code_middle2:
                max = middle - 1
            else:
                min = middle + 1
        else:
            min = middle
    print('最新实物抽奖id为', min, max)
    for i in range(max - 30, max + 1):
        json_response = await OnlineNet().req('get_lotterylist', i)
        print('id对应code数值为', json_response['code'], i)
        # -400 不存在
        if not json_response['code']:
            temp = json_response['data']['title']
            if any(word in temp for word in blacklist):
                print("检测到疑似钓鱼类测试抽奖，默认不参与，请自行判断抽奖可参与性")
                # print(temp)
            else:
                check = json_response['data']['typeB']
                for g, value in enumerate(check):
                    join_end_time = value['join_end_time']
                    join_start_time = value['join_start_time']
                    ts = CurrentTime()
                    if int(join_end_time) > int(ts) > int(join_start_time):
                        json_response1 = await OnlineNet().req('get_gift_of_lottery', i, g)
                        printer.info([f'参与实物抽奖回显：{json_response1}'], True)


async def run():
    while 1:
        # login.HandleExpire()
        await heartbeat()
        # await draw_lottery()

        try:
            await guard_lottery()
        except:
            traceback.print_exc()

        await asyncio.sleep(300)


