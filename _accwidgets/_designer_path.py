import os
from pathlib import Path
import accwidgets


def run():
    accwidgets_path = Path(accwidgets.__file__).parent.absolute()
    plugin_paths = list(map(str, accwidgets_path.glob("**/designer")))
    print(os.pathsep.join(plugin_paths))
