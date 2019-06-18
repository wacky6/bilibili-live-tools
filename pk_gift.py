from online_net import OnlineNet
import asyncio
from bilitimer import BiliTimer

# real_roomid -> remaining trials
active_rooms = dict()

async def get_pk_winner_gift(real_roomid, raffle_id):
    resp = await OnlineNet().req('join_room_pk_gift', real_roomid, raffle_id)
    return resp

async def monitor_pk_result(real_roomid):
    check_interval = 75
    init_trials = 11    # ceil(max duration of pk / check_interval) + 1 + tolerance

    if real_roomid in active_rooms:
        active_rooms[real_roomid] = init_trials
        return
    else:
        active_rooms[real_roomid] = init_trials

    while True:
        resp = await OnlineNet().req('check_room_pk_gift', real_roomid)
        list_raffles = resp['data']

        print(f'check room pk gift {real_roomid}, trial {init_trials - active_rooms[real_roomid]}, raffles = ', list_raffles)

        # no conclusion, keep checking
        if not list_raffles:
            active_rooms[real_roomid] -= 1
            if active_rooms[real_roomid] > 0:
                await asyncio.sleep(check_interval)
                continue
            else:
                del active_rooms[real_roomid]
                print(f'PK at {real_roomid} expires without gift')
                return

        # concluded, grab gifts
        for raffle in list_raffles:
            raffle_id = raffle['id']
            print(f'PK at {real_roomid} concludes with raffle: {raffle_id}, will join')
            resp = await get_pk_winner_gift(real_roomid, raffle_id)
            if resp['code'] == 0 and resp['data'] and resp['data']['award_text']:
                gift_text = resp['data']['award_text']
                print(f'PK at {real_roomid} raffle: {raffle_id}, received: {gift_text}')
            else:
                print(f'PK at {real_roomid} raffle: {raffle_id}, returns: ', resp)

        del active_rooms[real_roomid]
        return    # done
