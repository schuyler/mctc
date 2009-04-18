from apps.webui.shortcuts import messages

def general(request):
    result = {}
    # message parser so that we have messages
    if request.GET.has_key("msg"):
        msg = messages.get(request.GET["msg"], "")
        if msg:
            result["msg"] = msg
    return result