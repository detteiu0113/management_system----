from django.utils.decorators import method_decorator
from accounts.decorators import user_type_required
from django.shortcuts import render
from .models import Room, Message
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings

def websocket_chat(request, room_name):
    return render(request, 'owner/room.html', {
        'room_name': room_name
    })

def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        # ファイルを保存する
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(uploaded_file.name, uploaded_file)

        # 保存されたファイルのパスを取得する
        saved_file_path = fs.url(filename)

        # 必要に応じてファイルの保存パスやその他の処理を返す
        return JsonResponse({'message': 'File uploaded successfully', 'file_path': saved_file_path})
    else:
        return JsonResponse({'error': 'File not found or invalid request'})

def rooms(request):
    # allにすることでownerは全てのroomにアクセス可能に
    rooms = Room.objects.all()
    for room in rooms:
        last_message = Message.objects.filter(room=room).order_by('-date_added').first()
        room.last_message = last_message

        # 未読メッセージ数を計算し、ルームオブジェクトに追加する
        room.unread_count = Message.objects.filter(room=room, is_read=False).exclude(user=request.user).count()
    return render(request, 'owner/rooms.html', {'rooms': rooms})

@user_type_required('owner')
def room(request, slug):
    room = Room.objects.get(slug=slug)
    unread_messages = Message.objects.filter(room=room, is_read=False).exclude(user=request.user)

    # 未読メッセージを既読に更新する
    for message in unread_messages:  # 送信者がログインしているユーザーでない場合のみ
        message.is_read = True
        message.save()

    # 未読メッセージを含まないメッセージも取得する
    messages = Message.objects.filter(room=room)

    return render(request, 'owner/room.html', {'room': room, 'messages': messages})

@user_type_required('teacher')
def teacher_rooms(request):
    rooms = Room.objects.filter(users=request.user)
    for room in rooms:
        last_message = Message.objects.filter(room=room).order_by('-date_added').first()
        room.last_message = last_message

    return render(request, 'teacher/rooms.html', {'rooms': rooms })


@user_type_required('teacher')
def teacher_room(request, slug):
    room = Room.objects.get(slug=slug)
    messages = Message.objects.filter(room=room)

        # 既読フラグを更新する
    for message in messages:
        if message.user != request.user:  # 送信者がログインしているユーザーでない場合のみ
            if not message.is_read:
                message.is_read = True
                message.save()

    return render(request, 'teacher/room.html', {'room': room, 'messages': messages})

def parent_rooms(request, pk):
    rooms = Room.objects.filter(users=request.user)
    for room in rooms:
        last_message = Message.objects.filter(room=room).order_by('-date_added').first()
        room.last_message = last_message
    return render(request, 'parent/rooms.html', {'rooms': rooms})

def parent_room(request, pk, slug):
    room = Room.objects.get(slug=slug)
    messages = Message.objects.filter(room=room)[0:25]

    return render(request, 'parent/room.html', {'room': room, 'messages': messages})
