import os
import time


# Reset timezone to UTC for time-sensitive tests, e.g. those using freezegun.
# While setting freezegun to a date with explicit timezone may work, it also
# may fail on systems, where $TZ environment variable is undefined. Here, we
# define it explicitly to avoid those problems.
os.environ["TZ"] = "Etc/UTC"
time.tzset()
