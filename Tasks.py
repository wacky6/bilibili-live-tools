from bilibili import bilibili
import datetime
import time
import asyncio
from configloader import ConfigLoader
import utils
from printer import Printer
from bilitimer import BiliTimer
import aiohttp

    
# 获取每日包裹奖励
async def Daily_bag():
    json_response = await bilibili().get_dailybag()
    # no done code
    # print('Daily_bag', json_response)
    for i in range(0, len(json_response['data']['bag_list'])):
        Printer().printlist_append(['join_lottery', '', 'user', "# 获得-" + json_response['data']['bag_list'][i]['bag_name'] + "-成功"])
    BiliTimer().append2list_jobs([Daily_bag, [], int(CurrentTime()), 21600])


def CurrentTime():
    currenttime = str(int(time.mktime(datetime.datetime.now().timetuple())))
    return currenttime

# 签到功能
async def DoSign():
    temp = await bilibili().get_dosign()
    # -500 done
    # print('DoSign', temp)
    Printer().printlist_append(['join_lottery', '', 'user', "# 签到状态:",temp['msg']])
    BiliTimer().append2list_jobs([DoSign, [], int(CurrentTime()), 21600])

# 领取每日任务奖励
async def Daily_Task():
    json_response2 = await bilibili().get_dailytask()
    Printer().printlist_append(['join_lottery', '', 'user', "# 双端观看直播:", json_response2["msg"]])
    #-400 done
    # print('Daily_Task', json_response2)
    BiliTimer().append2list_jobs([Daily_Task, [], int(CurrentTime()), 21600])


async def Sign1Group(session, i1, i2):
    json_response = await bilibili().assign_group(session, i1, i2)
    if json_response['code'] == 0:
        if (json_response['data']['status']) == 1:
            Printer().printlist_append(['join_lottery', '', 'user', "# 应援团 %s 已应援过" % (i1)])
        if (json_response['data']['status']) == 0:
            Printer().printlist_append(['join_lottery', '', 'user', "# 应援团 %s 应援成功,获得 %s 点亲密度" % (i1, json_response['data']['add_num'])])
    else:
        Printer().printlist_append(['join_lottery', '', 'user', "# 应援团 %s 应援失败" % (i1)])

# 应援团签到
async def link_sign():
    response = bilibili().get_grouplist()
    check = len(response.json()['data']['list'])
    group_id_list = []
    owner_uid_list = []
    for i in range(0, check):
        group_id = response.json()['data']['list'][i]['group_id']
        owner_uid = response.json()['data']['list'][i]['owner_uid']
        group_id_list.append(group_id)
        owner_uid_list.append(owner_uid)
    tasklist = []
    if group_id_list:
        async with aiohttp.ClientSession() as session:
            for (i1, i2) in zip(group_id_list, owner_uid_list):
                task = asyncio.ensure_future(Sign1Group(session, i1, i2))
                tasklist.append(task)
            results = await asyncio.gather(*tasklist)
    BiliTimer().append2list_jobs([link_sign, [], int(CurrentTime()), 21600])
        

async def send_gift():
    if ConfigLoader().dic_user['task_control']['clean-expiring-gift']:
        argvs, x = await utils.fetch_bag_list(printer=False)
        for i in range(0, len(argvs)):
            giftID = argvs[i][0]
            giftNum = argvs[i][1]
            bagID = argvs[i][2]
            roomID = ConfigLoader().dic_user['task_control']['clean-expiring-gift2room']
            await utils.send_gift_web(roomID, giftID, giftNum, bagID)
        if not argvs:
            Printer().printlist_append(['join_lottery', '', 'user', "# 没有将要过期的礼物~"])
    BiliTimer().append2list_jobs([send_gift, [], int(CurrentTime()), 21600])

async def auto_send_gift():
    if ConfigLoader().dic_user['task_control']['send2wearing-medal']:
        a = await utils.WearingMedalInfo()
        if a is None:
            print('暂未佩戴任何勋章')
            return 
        json_res = await bilibili().gift_list()
        temp_dic = {}
        for j in range(0, len(json_res['data'])):
            price = json_res['data'][j]['price']
            id = json_res['data'][j]['id']
            temp_dic[id] = price
        x, temp = await utils.fetch_bag_list(printer=False)
        roomid = a[0]
        today_feed = a[1]
        day_limit = a[2]
        left_num = int(day_limit) - int(today_feed)
        calculate = 0
        for i in range(0, len(temp)):
            gift_id = int(temp[i][0])
            gift_num = int(temp[i][1])
            bag_id = int(temp[i][2])
            if (gift_id not in [4, 3, 9, 10]):
                if (gift_num * (temp_dic[gift_id] / 100) < left_num):
                    calculate = calculate + temp_dic[gift_id] / 100 * gift_num
                    # tmp = calculate / (temp_dic[gift_id] / 100)
                    tmp2 = temp_dic[gift_id] / 100 * gift_num
                    await utils.send_gift_web(roomid, gift_id, gift_num, bag_id)
                    left_num = left_num-tmp2
                elif left_num - temp_dic[gift_id] / 100 >= 0:
                    tmp = (left_num) / (temp_dic[gift_id] / 100)
                    tmp1 = (temp_dic[gift_id] / 100) * int(tmp)
                    calculate = calculate + tmp1
                    await utils.send_gift_web(roomid, gift_id, tmp, bag_id)
                    left_num = left_num - tmp1
        Printer().printlist_append(['join_lottery', '', 'user', "# 自动送礼共送出亲密度为%s的礼物" % int(calculate)])
    BiliTimer().append2list_jobs([auto_send_gift, [], int(CurrentTime()), 21600])
        
async def doublegain_coin2silver():
    if ConfigLoader().dic_user['task_control']['doublegain_coin2silver']:
        json_response0 = await bilibili().request_doublegain_coin2silver()
        json_response1 = await bilibili().request_doublegain_coin2silver()
        print(json_response0['msg'], json_response1['msg'])
    BiliTimer().append2list_jobs([doublegain_coin2silver, [], int(CurrentTime()), 21600])

async def sliver2coin():
    if ConfigLoader().dic_user['task_control']['silver2coin']:
        json_response = await bilibili().silver2coin_web()
        json_response1 = await bilibili().silver2coin_app()
        Printer().printlist_append(['join_lottery', '', 'user',"# ", json_response['msg']])
        Printer().printlist_append(['join_lottery', '', 'user', "# ", json_response1['msg']])
    BiliTimer().append2list_jobs([sliver2coin, [], int(CurrentTime()), 21600])


def init():
    BiliTimer().append2list_jobs([sliver2coin, [], 0, 0])
    BiliTimer().append2list_jobs([doublegain_coin2silver, [], 0, 0])
    BiliTimer().append2list_jobs([DoSign, [], 0, 0])
    BiliTimer().append2list_jobs([Daily_bag, [], 0, 0])
    BiliTimer().append2list_jobs([Daily_Task, [], 0, 0])
    BiliTimer().append2list_jobs([link_sign, [], 0, 0])
    BiliTimer().append2list_jobs([send_gift, [], 0, 0])
    BiliTimer().append2list_jobs([auto_send_gift, [], 0, 0])
