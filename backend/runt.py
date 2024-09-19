from django.db.models import Sum
from users.models import User, Follow
from api.serializers import UserRecipeSerializer



user = User.objects.get(id=2)

print(user)
following = Follow.objects.filter(user=user).values_list('following', flat=True)
print(following)
f = Follow.objects.filter(user=user).values('following_id')
print(f)
exit()
