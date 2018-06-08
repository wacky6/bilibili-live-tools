from bilibili import bilibili
import datetime
import time
import asyncio
from configloader import ConfigLoader
import utils
from printer import Printer
from bilitimer import BiliTimer
import random
import sys
import re
import json

# 获取每日包裹奖励
async def Daily_bag():
    json_response = await bilibili.get_dailybag()
    # no done code
    # print('Daily_bag', json_response)
    for i in json_response['data']['bag_list']:
        Printer().print_words(["# 获得-" + i['bag_name'] + "-成功"])
    await BiliTimer.append2list_jobs(Daily_bag, 21600)

def CurrentTime():
    currenttime = str(int(time.mktime(datetime.datetime.now().timetuple())))
    return currenttime

# 签到功能
async def DoSign():
    # -500 done
    temp = await bilibili.get_dosign()
    # print('DoSign', temp)
    Printer().print_words([f'# 签到状态: {temp["msg"]}'])
    if temp['code'] == -500 and '已' in temp['msg']:
        sleeptime = (utils.seconds_until_tomorrow() + 300)
        await BiliTimer.append2list_jobs(DoSign, sleeptime)
    else:
        await BiliTimer.append2list_jobs(DoSign, 350)

# 领取每日任务奖励
async def Daily_Task():
    # -400 done/not yet
    json_response2 = await bilibili.get_dailytask()
    Printer().print_words([f'# 双端观看直播:  {json_response2["msg"]}'])
    # print('Daily_Task', json_response2)
    if json_response2['code'] == -400 and '已' in json_response2['msg']:
        sleeptime = (utils.seconds_until_tomorrow() + 300)
        await BiliTimer.append2list_jobs(Daily_Task, sleeptime)
    else:
        await BiliTimer.append2list_jobs(Daily_Task, 350)

async def Sign1Group(i1, i2):
    json_response = await bilibili.assign_group(i1, i2)
    if not json_response['code']:
        if (json_response['data']['status']) == 1:
            Printer().print_words(["# 应援团 %s 已应援过" % (i1)])
        if (json_response['data']['status']) == 0:
            Printer().print_words(["# 应援团 %s 应援成功,获得 %s 点亲密度" % (i1, json_response['data']['add_num'])])
    else:
        Printer().print_words(["# 应援团 %s 应援失败" % (i1)])

# 应援团签到
async def link_sign():
    json_rsp = await bilibili.get_grouplist()
    list_check = json_rsp['data']['list']
    id_list = ((i['group_id'], i['owner_uid']) for i in list_check)
    if list_check:
        tasklist = []
        for (i1, i2) in id_list:
            task = asyncio.ensure_future(Sign1Group(i1, i2))
            tasklist.append(task)
        results = await asyncio.gather(*tasklist)
    await BiliTimer.append2list_jobs(link_sign, 21600)

async def send_gift():
    if ConfigLoader().dic_user['task_control']['clean-expiring-gift']:
        argvs = await utils.fetch_bag_list(printer=False)
        # print(argvs)
        sent = False
        roomID = ConfigLoader().dic_user['task_control']['clean-expiring-gift2room']
        time_set = ConfigLoader().dic_user['task_control']['set-expiring-time']
        for i in argvs:
            left_time = i[3]
            if left_time is not None and 0 < int(left_time) < time_set:  # 剩余时间少于半天时自动送礼
                sent = True
                giftID = i[0]
                giftNum = i[1]
                bagID = i[2]
                await utils.send_gift_web(roomID, giftNum, bagID, giftID)
        if not sent:
            Printer().print_words(["# 没有将要过期的礼物~"])
    await BiliTimer.append2list_jobs(send_gift, 21600)

async def auto_send_gift():
    if ConfigLoader().dic_user['task_control']['send2wearing-medal']:
        a = await utils.WearingMedalInfo()
        if a is None:
            print('暂未佩戴任何勋章')
            await BiliTimer.append2list_jobs(auto_send_gift, 21600)
            return
        json_res = await bilibili.gift_list()
        temp_dic = {j['id']: (j['price'] / 100) for j in json_res['data']}
        temp = await utils.fetch_bag_list(printer=False)
        roomid = a[0]
        today_feed = a[1]
        day_limit = a[2]
        left_score = int(day_limit) - int(today_feed)
        calculate = 0
        # print(temp)
        for i in temp:
            gift_id = int(i[0])
            gift_num = int(i[1])
            bag_id = int(i[2])
            left_time = i[3]
            if (gift_id not in [4, 3, 9, 10]) and left_time is not None:
                # print(gift_id, bag_id)
                if (gift_num * temp_dic[gift_id] <= left_score):
                    pass
                elif left_score - temp_dic[gift_id] >= 0:
                    gift_num = int((left_score) / (temp_dic[gift_id]))
                else:
                    continue
                score = temp_dic[gift_id] * gift_num
                await utils.send_gift_web(roomid, gift_num, bag_id, gift_id)
                calculate = calculate + score
                left_score = left_score - score
        Printer().print_words(["# 自动送礼共送出亲密度为%s的礼物" % int(calculate)])
    await BiliTimer.append2list_jobs(auto_send_gift, 21600)

async def doublegain_coin2silver():
    if ConfigLoader().dic_user['task_control']['doublegain_coin2silver']:
        json_response0 = await bilibili.request_doublegain_coin2silver()
        json_response1 = await bilibili.request_doublegain_coin2silver()
        print(json_response0['msg'], json_response1['msg'])
    await BiliTimer.append2list_jobs(doublegain_coin2silver, 21600)

async def sliver2coin():
    if ConfigLoader().dic_user['task_control']['silver2coin']:
        # 403 done
        json_response1 = await bilibili.silver2coin_app()
        # -403 done
        json_response = await bilibili.silver2coin_web()
        Printer().print_words([f'#  {json_response["msg"]}'])
        Printer().print_words([f'#  {json_response1["msg"]}'])
        if json_response['code'] == -403 and '只' in json_response['msg']:
            finish_web = True
        else:
            finish_web = False

        if json_response1['code'] == 403 and '最多' in json_response1['msg']:
            finish_app = True
        else:
            finish_app = False
        if finish_app and finish_web:
            sleeptime = (utils.seconds_until_tomorrow() + 300)
            await BiliTimer.append2list_jobs(sliver2coin, sleeptime)
            return
        else:
            await BiliTimer.append2list_jobs(sliver2coin, 350)
            return

    await BiliTimer.append2list_jobs(sliver2coin, 21600)

async def GetVideoExp(list_topvideo):
    print('开始获取视频观看经验')
    aid = list_topvideo[random.randint(0, 19)]
    cid = await utils.GetVideoCid(aid)
    await bilibili().Heartbeat(aid, cid)

async def GiveCoinTask(coin_remain, list_topvideo):
    while coin_remain > 0:
        aid = list_topvideo[random.randint(0, 50)]
        rsp = await utils.GiveCoin2Av(aid, 1)
        if rsp is None:
            break
        elif rsp:
            coin_remain -= 1

async def GetVideoShareExp(list_topvideo):
    print('开始获取视频分享经验')
    aid = list_topvideo[random.randint(0, 19)]
    await bilibili().DailyVideoShare(aid)

async def BiliMainTask():
    try:
        login, watch_av, num, share_av= await utils.GetRewardInfo()
    except :
        # print('当前网络不好，正在重试，请反馈开发者!!!!')
        print(sys.exc_info()[0], sys.exc_info()[1])
        return 
    list_topvideo = await utils.GetTopVideoList()
    if (not login) or not watch_av:
        await GetVideoExp(list_topvideo)
    coin_sent = (num) / 10
    coin_set = min((ConfigLoader().dic_user['task_control']['givecoin']), 5)
    coin_remain = coin_set - coin_sent
    await GiveCoinTask(coin_remain, list_topvideo)
    if not share_av:
        await GetVideoShareExp(list_topvideo)
    # b站傻逼有记录延迟，3点左右成功率高一点
    await BiliTimer.append2list_jobs(BiliMainTask, utils.seconds_until_tomorrow() + 10800)

    
async def fetch_case():
    temp = await bilibili().req_fetch_case()
    if not temp['code']:
        id = temp['data']['id']
        return id
    # 25008 真给力 , 移交众裁的举报案件已经被处理完
    # 25014 有时有时……
    if temp['code'] == 25014 or 25008:
        return


async def check(id):
    # 3放弃
    # 2 否 voterule
    # 4 删除 votedelete
    # 1 封杀 votebreak
    text_rsp = await bilibili().req_check_voted(id)
    # print(response.text)
        
    pattern = re.compile(r'\((.+)\)')
    match = pattern.findall(text_rsp)
    if match:
        # 使用Match获得分组信息
        # print(match[0])
        temp = match[0]
    temp = json.loads(temp)
    print(temp)
    # print(temp['data']['originUrl'])
    data = temp['data']
    print(data['originContent'])
    votebreak = data['voteBreak']
    voteDelete = data['voteDelete']
    voteRule = data['voteRule']
    voted = votebreak+voteDelete+voteRule
    if voted:
        percent = voteRule / voted
    else:
        percent = 0
    print('目前已投票', voted)
    print('认为不违反规定的比例', percent)
    vote = 3
    if voted >= 400: 
        if percent >= 0.8:
            vote = 2
        elif percent <= 0.2:
            vote = 4
    elif voted >= 150: 
        if percent >= 0.9:
            vote = 2
        elif percent <= 0.1:
            vote = 4
    elif voted >= 50: 
        if percent >= 0.97:
            vote = 2
        elif percent <= 0.03:
            vote = 4
    return vote
    
                
async def vote_case(id, vote):
    json_rsp = await bilibili().req_vote_case(id, vote)
    print(json_rsp)
    return True
 
               
async def judge():
    list_result = []
    while True:
        id = await fetch_case()
        if id is None:
            print('本次未获取到案件')
            # await asyncio.sleep(1)
            break
        vote = await check(id)
        await vote_case(id, vote)    
        print('投票结果', id, vote)
        list_result.append((id, vote))
        
        print('______________________________')
        # await asyncio.sleep(1)
    print(list_result, f'共{len(list_result)}案例')
    await BiliTimer.append2list_jobs(judge, 3600)
        

async def init():
    await BiliTimer.append2list_jobs(sliver2coin, 0)
    await BiliTimer.append2list_jobs(doublegain_coin2silver, 0)
    await BiliTimer.append2list_jobs(DoSign, 0)
    await BiliTimer.append2list_jobs(Daily_bag, 0)
    await BiliTimer.append2list_jobs(Daily_Task, 0)
    await BiliTimer.append2list_jobs(link_sign, 0)
    await BiliTimer.append2list_jobs(send_gift, 0)
    await BiliTimer.append2list_jobs(auto_send_gift, 0)
    await BiliTimer.append2list_jobs(BiliMainTask, 0)
    await BiliTimer.append2list_jobs(judge, 0)
    
