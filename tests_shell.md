# Préparation :
from django.utils import timezone as tz
import datetime as dt
from yourapp.models import Formation as F, Centre as C, TypeOffre as TO, Statut as S
c = C.objects.create(nom="Test"); to = TO.objects.create(nom="Test"); s = S.objects.create(nom="Test")
f = F(nom="Test", centre=c, type_offre=to, statut=s, start_date=tz.now().date(), end_date=tz.now().date()+dt.timedelta(days=1), prevus_crif=1); f.save()
print(f.places_disponibles)