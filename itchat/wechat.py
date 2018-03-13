import itchat
import dandan

logger = dandan.logger.getLogger(name="wechat")

itchat.auto_login(hotReload=True)

friends = itchat.get_friends()


contacts = dandan.value.get_json("info.json") or dandan.value.AttrDict()

if not contacts:
    for friend in friends:
        friend = dandan.value.AttrDict(friend)

        contact = dandan.value.AttrDict()

        contact.NickName = friend.NickName
        contact.RemarkName = friend.RemarkName
        contact.name = friend.RemarkName or friend.NickName
        contact.nick = ""
        contacts[contact.NickName] = contact

    dandan.value.put_json(contacts, "info.json")

    exit()


 # msg = message.format(name=name)
 #        print(msg)
 #        print(itchat.send_msg(msg, friend.UserName))