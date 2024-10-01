from django.shortcuts import redirect
from functools import wraps

def user_type_required(*allowed_user_types):
    """
    カスタムデコレーター: 複数のユーザータイプに基づいてリダイレクトを行う
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # アプリ名に名前空間を設定する必要あり
            if request.user.is_authenticated:
                if request.resolver_match.namespace == "owner" and request.user.is_owner:
                    return view_func(request, *args, **kwargs)
                
                elif request.resolver_match.namespace == "teacher" and request.user.is_teacher:
                    return view_func(request, *args, **kwargs)
                
                elif request.resolver_match.namespace == "parent" and request.user.is_parent:
                    parent_model = request.user
                    student_id_from_url = kwargs.get('pk')
                    if parent_model.parent_profile.current_student.id == student_id_from_url:
                        return view_func(request, *args, **kwargs)
                    else:
                        return redirect('login')
                
            return redirect('login')

        return wrapped_view

    return decorator