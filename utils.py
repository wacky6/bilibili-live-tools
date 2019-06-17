from online_net import OnlineNet
import printer
import time
import datetime
from io import BytesIO
import webbrowser
import re
from operator import itemgetter
from configloader import ConfigLoader
from bilibili import bilibili


def adjust_for_chinese(str):
    SPACE = '\N{IDEOGRAPHIC SPACE}'
    EXCLA = '\N{FULLWIDTH EXCLAMATION MARK}'
    TILDE = '\N{FULLWIDTH TILDE}'

    # strings of ASCII and full-width characters (same order)
    west = ''.join(chr(i) for i in range(ord(' '), ord('~')))
    east = SPACE + ''.join(chr(i) for i in range(ord(EXCLA), ord(TILDE)))

    # build the translation table
    full = str.maketrans(west, east)
    str = str.translate(full).rstrip().split('\n')
    md = f'{str[0]:^10}'
    return md.translate(full)


def CurrentTime():
    currenttime = int(time.time())
    return str(currenttime)


def seconds_until_tomorrow():
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    tomorrow_start_time = int(time.mktime(time.strptime(str(tomorrow), '%Y-%m-%d')))
    current_time = int(time.mktime(datetime.datetime.now().timetuple()))
    return tomorrow_start_time - current_time

async def WearingMedalInfo():
    json_response = await OnlineNet().req('ReqWearingMedal')
    # print(json_response)
    if not json_response['code']:
        data = json_response['data']
        if data:
            # print(data['roominfo']['room_id'], data['today_feed'], data['day_limit'])
            return [(data['roominfo']['room_id'],  int(data['day_limit']) - int(data['today_feed']), data['medal_name']), ]
        else:
            # print('暂无佩戴任何勋章')
            return []

        # web api返回值信息少

async def TitleInfo():
    json_response = await OnlineNet().req('ReqTitleInfo')
    dic_title = ConfigLoader().dic_title
    # print(json_response)
    if not json_response['code']:
        data = json_response['data']
        for i in data['list']:
            if i['level']:
                max = i['level'][1]
            else:
                max = '-'
            print(dic_title[i['title_pic']['id']], i['activity'], i['score'], max)

async def fetch_medal(show=False):
    printlist = []
    list_medal = []
    json_response = await OnlineNet().req('request_fetchmedal')
    # print(json_response)
    if not json_response['code']:
        for i in json_response['data']['fansMedalList']:
            if 'roomid' in i:
                today_feed = i['today_feed'] if 'today_feed' in i else i['todayFeed']
                day_limit = i['day_limit'] if 'day_limit' in i else i['dayLimit']
                list_medal.append((
                    i['roomid'],   # apparent roomid, convert to canonical roomid first
                    int(day_limit - today_feed),    # today's remaining intimacy
                    i['medal_name']
                ))

    return list_medal

async def send_danmu_msg_web(msg, roomId):
    json_response = await OnlineNet().req('request_send_danmu_msg_web', msg, roomId)
    print(json_response)

async def find_live_user_roomid(wanted_name):
    print(wanted_name)

    def check_name_piece(json_rsp, wanted_name):
        results = json_rsp['result']
        if results is None:
            # print('屏蔽全名')
            return None
        for i in results:
            real_name = re.sub(r'<[^>]*>', '', i['uname'])
            # print('去除干扰', real_name)
            if real_name == wanted_name:
                print('找到结果', i)
                return i
        return None

    for i in range(len(wanted_name), 0, -1):
        name_piece = wanted_name[:i]
        json_rsp = await OnlineNet().req('request_search_biliuser', name_piece)
        answer = check_name_piece(json_rsp, wanted_name)
        if answer is not None:
            return answer['room_id']
        # print('结束一次')

    print('第2备份启用')
    for i in range(len(wanted_name)):
        name_piece = wanted_name[i:]
        json_rsp = await OnlineNet().req('request_search_biliuser', name_piece)
        answer = check_name_piece(json_rsp, wanted_name)
        if answer is not None:
            return answer['room_id']

    print('第3备份启用')
    for i in range(len(wanted_name), 0, -1):
        name_piece = wanted_name[:i]
        json_rsp = await OnlineNet().req('request_search_liveuser', name_piece)
        answer = check_name_piece(json_rsp, wanted_name)
        if answer is not None:
            return answer['roomid']

    print('第4备份启用')
    for i in range(len(wanted_name)):
        name_piece = wanted_name[i:]
        json_rsp = await OnlineNet().req('request_search_liveuser', name_piece)
        answer = check_name_piece(json_rsp, wanted_name)
        if answer is not None:
            return answer['roomid']


async def fetch_capsule_info():
    json_response = await OnlineNet().req('request_fetch_capsule')
    # print(json_response)
    if not json_response['code']:
        data = json_response['data']
        if data['colorful']['status']:
            print(f'梦幻扭蛋币: {data["colorful"]["coin"]}个')
        else:
            print('梦幻扭蛋币暂不可用')

        data = json_response['data']
        if data['normal']['status']:
            print(f'普通扭蛋币: {data["normal"]["coin"]}个')
        else:
            print('普通扭蛋币暂不可用')

async def open_capsule(count):
    json_response = await OnlineNet().req('request_open_capsule', count)
    # print(json_response)
    if not json_response['code']:
        # print(json_response['data']['text'])
        for i in json_response['data']['text']:
            print(i)

async def watch_living_video(cid):
    import sound
    sound.set_honors_silent_switch(False)
    sound.set_volume(1)
    sound.play_effect('piano:D3')
    json_response = await OnlineNet().req('request_playurl', cid)
    print(json_response)
    if not json_response['code']:
        data = json_response['data']
        print(data)
        webbrowser.open(data)

async def fetch_user_info():
    json_response = await OnlineNet().req('request_fetch_user_info')
    json_response_ios = await OnlineNet().req('request_fetch_user_infor_ios')
    print('[{}] 查询用户信息'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
    if not json_response_ios['code']:
        gold_ios = json_response_ios['data']['gold']
    # print(json_response_ios)
    if not json_response['code']:
        data = json_response['data']
        # print(data)
        userInfo = data['userInfo']
        userCoinIfo = data['userCoinIfo']
        uname = userInfo['uname']
        achieve = data['achieves']
        user_level = userCoinIfo['user_level']
        silver = userCoinIfo['silver']
        gold = userCoinIfo['gold']
        identification = bool(userInfo['identification'])
        mobile_verify = bool(userInfo['mobile_verify'])
        user_next_level = userCoinIfo['user_next_level']
        user_intimacy = userCoinIfo['user_intimacy']
        user_next_intimacy = userCoinIfo['user_next_intimacy']
        user_level_rank = userCoinIfo['user_level_rank']
        billCoin = userCoinIfo['coins']
        bili_coins = userCoinIfo['bili_coins']
        print('# 用户名', uname)
        size = 100, 100

        print(f'# 手机认证状况 {mobile_verify} | 实名认证状况 {identification}')
        print('# 银瓜子', silver)
        print('# 通用金瓜子', gold)
        print('# ios可用金瓜子', gold_ios)
        print('# 硬币数', billCoin)
        print('# b币数', bili_coins)
        print('# 成就值', achieve)
        print('# 等级值', user_level, '———>', user_next_level)
        print('# 经验值', user_intimacy)
        print('# 剩余值', user_next_intimacy - user_intimacy)
        arrow = int(user_intimacy * 30 / user_next_intimacy)
        line = 30 - arrow
        percent = user_intimacy / user_next_intimacy * 100.0
        process_bar = '# [' + '>' * arrow + '-' * line + ']' + '%.2f' % percent + '%'
        print(process_bar)
        print('# 等级榜', user_level_rank)

async def fetch_bag_list(verbose=False, bagid=None, show=True):
    json_response = await OnlineNet().req('request_fetch_bag_list')
    gift_list = []
    # print(json_response)
    if show:
        print('[{}] 查询可用礼物'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
    for i in json_response['data']['list']:
        bag_id = i['bag_id']
        gift_id = i['gift_id']
        gift_num = i['gift_num']
        gift_name = i['gift_name']
        expireat = i['expire_at']
        left_time = (expireat - json_response['data']['time'])
        if not expireat:
            left_days = '+∞'.center(6)
            left_time = None
        else:
            left_days = round(left_time / 86400, 1)
        if bagid is not None:
            if bag_id == int(bagid):
                return gift_id, gift_num
        else:
            if verbose:
                print(f'# 编号为{bag_id}的{gift_name:^3}X{gift_num:^4} (在{left_days:^6}天后过期)')
            elif show:
                print(f'# {gift_name:^3}X{gift_num:^4} (在{left_days:^6}天后过期)')

        gift_list.append([gift_id, gift_num, bag_id, left_time])
    # print(gift_list)
    return gift_list

async def check_taskinfo():
    json_response = await OnlineNet().req('request_check_taskinfo')
    # print(json_response)
    if not json_response['code']:
        data = json_response['data']
        double_watch_info = data['double_watch_info']
        box_info = data['box_info']
        sign_info = data['sign_info']
        live_time_info = data['live_time_info']
        print('双端观看直播：')
        if double_watch_info['status'] == 1:
            print('# 该任务已完成，但未领取奖励')
        elif double_watch_info['status'] == 2:
            print('# 该任务已完成，已经领取奖励')
        else:
            print('# 该任务未完成')
            if double_watch_info['web_watch'] == 1:
                print('## 网页端观看任务已完成')
            else:
                print('## 网页端观看任务未完成')

            if double_watch_info['mobile_watch'] == 1:
                print('## 移动端观看任务已完成')
            else:
                print('## 移动端观看任务未完成')

        print('直播在线宝箱：')
        if box_info['status'] == 1:
            print('# 该任务已完成')
        else:
            print('# 该任务未完成')
            print(f'## 一共{box_info["max_times"]}次重置次数，当前为第{box_info["freeSilverTimes"]}次第{box_info["type"]}个礼包(每次3个礼包)')

        print('每日签到：')
        if sign_info['status'] == 1:
            print('# 该任务已完成')
        else:
            print('# 该任务未完成')

        if sign_info['signDaysList'] == list(range(1, sign_info['curDay'] + 1)):
            print('# 当前全勤')
        else:
            print('# 出现断签')

        print('直播奖励：')
        if live_time_info['status'] == 1:
            print('# 已完成')
        else:
            print('# 未完成(目前本项目未实现自动完成直播任务)')

async def check_room(roomid):
    json_response = await OnlineNet().req('request_check_room', roomid)
    if not json_response['code']:
        # print(json_response)
        print('查询结果:')
        data = json_response['data']

        if not data['short_id']:
            print('# 此房间无短房号')
        else:
            print(f'# 短号为:{data["short_id"]}')
        print(f'# 真实房间号为:{data["room_id"]}')
        return data['room_id']
    # 房间不存在
    elif json_response['code'] == 60004:
        print(json_response['msg'])

async def send_gift_web(roomid, num_wanted, bagid, giftid=None):
    if giftid is None:
        giftid, num_owned = await fetch_bag_list(False, bagid)
        num_wanted = min(num_owned, num_wanted)
    if not num_wanted:
        return
    json_response = await OnlineNet().req('request_check_room', roomid)
    ruid = json_response['data']['uid']
    biz_id = json_response['data']['room_id']
    # 200027 不足数目
    json_response1 = await OnlineNet().req('request_send_gift_web', giftid, num_wanted, bagid, ruid, biz_id)
    if not json_response1['code']:
        # print(json_response1['data'])
        print(f'# 送出礼物: {json_response1["data"]["gift_name"]}X{json_response1["data"]["gift_num"]}')
    else:
        print("# 错误", json_response1['msg'], roomid, num_wanted, bagid, giftid)

async def fetch_liveuser_info(real_roomid):
    json_response = await OnlineNet().req('request_fetch_liveuser_info', real_roomid)
    if not json_response['code']:
        data = json_response['data']
        # print(data)
        print(f'# 主播姓名 {data["info"]["uname"]}')

        uid = data['level']['uid']  # str
        json_response_fan = await OnlineNet().req('request_fetch_fan', real_roomid, uid)
        # print(json_response_fan)
        data_fan = json_response_fan['data']
        if not json_response_fan['code'] and data_fan['medal']['status'] == 2:
            print(f'# 勋章名字: {data_fan["list"][0]["medal_name"]}')
        else:
            print('# 该主播暂时没有开通勋章')  # print(json_response_fan)

        size = 100, 100

async def enter_room(roomid):
    if not roomid:
        return True

    json_response = await OnlineNet().req('request_check_room', roomid)

    if not json_response['code']:
        data = json_response['data']
        param1 = data['is_hidden']
        param2 = data['is_locked']
        param3 = data['encrypted']
        if any((param1, param2, param3)):
            printer.info([f'抽奖脚本检测到房间{roomid:^9}为异常房间'], True)
            printer.warn(f'抽奖脚本检测到房间{roomid:^9}为异常房间')
            return False
        else:
            await OnlineNet().req('post_watching_history', roomid)
            return True

async def GiveCoin2Av(video_id, num):
    if num not in (1, 2):
        return False
    # 10004 稿件已经被删除
    # 34005 超过，满了
    # -104 不足硬币
    json_rsp = await OnlineNet().req('ReqGiveCoin2Av', video_id, num)
    code = json_rsp['code']
    if not code:
        print(f'给视频av{video_id}投{num}枚硬币成功')
        return True
    else:
        print('投币失败', json_rsp['message'])
        if code == -104:
            return None
        return False

async def GetTopVideoList():
    text_rsp = await OnlineNet().req('req_fetch_av')
    list_av = re.findall(r'(?<=www.bilibili.com/video/av)\d+(?=/)', text_rsp)
    list_av = list(set(list_av))
    return list_av

async def fetch_uper_video(list_mid):
    list_av = []
    for mid in list_mid:
        json_rsp = await OnlineNet().req('req_fetch_uper_video', mid, 1)
        # print(json_rsp)
        data = json_rsp['data']
        pages = data['pages']
        if data['vlist']:
            list_av += [av['aid'] for av in data['vlist']]
        for page in range(2, pages + 1):
            json_rsp = await OnlineNet().req('req_fetch_uper_video', mid, page)
            # print(json_rsp)
            data = json_rsp['data']
            list_av += [av['aid'] for av in data['vlist']]
    # print(len(list_av), list_av)
    return list_av

async def GetVideoCid(video_aid):
    json_rsp = await OnlineNet().req('ReqVideoCid', video_aid)
    # print(json_rsp[0]['cid'])
    return (json_rsp[0]['cid'])

async def GetRewardInfo(show=True):
    json_rsp = await OnlineNet().req('ReqMasterInfo')
    data = json_rsp['data']
    login = data['login']
    watch_av = data['watch_av']
    coins_av = data['coins_av']
    share_av = data['share_av']
    level_info = data["level_info"]
    current_exp = level_info['current_exp']
    next_exp = level_info['next_exp']
    if next_exp == -1:
        next_exp = current_exp
    print(f'# 主站等级值 {level_info["current_level"]}')
    print(f'# 主站经验值 {level_info["current_exp"]}')
    print(f'# 主站剩余值 {- current_exp + next_exp}')
    arrow = int(current_exp * 30 / next_exp)
    line = 30 - arrow
    percent = current_exp / next_exp * 100.0
    process_bar = '# [' + '>' * arrow + '-' * line + ']' + '%.2f' % percent + '%'
    print(process_bar)
    if show:
        print(f'每日登陆：{login} 每日观看：{watch_av} 每日投币经验：{coins_av}/50 每日分享：{share_av}')
    return login, watch_av, coins_av, share_av


async def FetchRoomArea(roomid):
    json_response = await OnlineNet().req('ReqRoomInfo', roomid)

    if not json_response['code']:
        # print(json_response)
        # print(json_response['data']['parent_area_id'])
        return json_response['data']['parent_area_id']


async def check_room_for_danmu(room_id, area_id):
    json_response = await OnlineNet().req('request_check_room', room_id)
    data = json_response['data']
    is_hidden = data['is_hidden']
    is_locked = data['is_locked']
    is_encrypted = data['encrypted']
    if any((is_hidden, is_locked, is_encrypted)):
        is_normal = False
    else:
        is_normal = True

    json_response = await OnlineNet().req('ReqRoomInfo', room_id)
    data = json_response['data']
    is_open = True if data['live_status'] == 1 else False
    current_area_id = data['parent_area_id']
    # print(is_hidden, is_locked, is_encrypted, is_open, current_area_id)
    is_ok = (area_id == current_area_id) and is_normal and is_open
    return is_ok


async def check_room_true(roomid):
    json_response = await bilibili().request_check_room(roomid)

    if json_response['code'] == 0:
        data = json_response['data']
        param1 = data['is_hidden']
        param2 = data['is_locked']
        param3 = data['encrypted']
        return param1, param2, param3
    else:
        Printer().printer(f"获取房间信息出错: {json_response}", "Error", "red")
        return [None]
