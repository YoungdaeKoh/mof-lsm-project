python3 -c "
from datetime import datetime, timedelta
base = datetime(1900,1,1)
for t in [693030, 693036]:
    dt = base + timedelta(hours=t)
    print(t, '->', dt)
"
