import os
from typing import List, Optional, Tuple
from pathlib import Path
import accwidgets


def collect_paths():
    accwidgets_path = Path(accwidgets.__file__).parent.absolute()
    plugin_paths = list(map(str, accwidgets_path.glob("**/designer")))
    print(os.pathsep.join(plugin_paths))


def install_additional_templates():

    venv_config = _get_venv_config()
    if venv_config is None:
        print("This command is effective only inside a virtual environment.")
        return

    venv_activate, venv_cmd = venv_config

    from qtpy.QtCore import QSettings
    settings = QSettings(_SETTINGS_PROJECT_NAME, _SETTINGS_APP_NAME)
    existing_paths: List[str] = settings.value(_SETTINGS_TEMPLATE_PATH_KEY)
    existing_paths = existing_paths if isinstance(existing_paths, list) else []
    # Qt Designer displays the last 2 components of the path in the title. So we setup the last 2 to be nice
    # and readable "accwidgets/templates".
    if _TEMPLATES_LOCATION_STR not in existing_paths:
        existing_paths.append(_TEMPLATES_LOCATION_STR)
        settings.setValue(_SETTINGS_TEMPLATE_PATH_KEY, existing_paths)
        print("Your Qt Designer settings have been updated. Please restart Qt Designer to see changes.")
    else:
        print("Your Qt Designer settings are already correctly set up.")

    if venv_cmd not in venv_activate.read_text():
        with venv_activate.open("a") as f:
            f.write(venv_cmd)
            print("Your virtual environment has been modified for accwidgets. You can use "
                  "'accwidgets-cli uninstall-templates' to undo.")
            print(f"Please re-activate your virtual environment: deactivate && source {venv_activate}")


def uninstall_additional_templates():

    venv_config = _get_venv_config()
    if venv_config is None:
        print("This command is effective only inside a virtual environment.")
        return

    venv_activate, venv_cmd = venv_config

    from qtpy.QtCore import QSettings
    settings = QSettings(_SETTINGS_PROJECT_NAME, _SETTINGS_APP_NAME)
    existing_paths: List[str] = settings.value(_SETTINGS_TEMPLATE_PATH_KEY)
    existing_paths = existing_paths if isinstance(existing_paths, list) else []
    changes_made = False
    # Do not just remove locations, but also selected template name, if it corresponds to accwidgets' template
    selected_template = settings.value(_SETTINGS_TEMPLATE_KEY)
    if isinstance(selected_template, str) and selected_template:
        template_names = (p.stem for p in _TEMPLATES_LOCATION.glob("*.ui"))
        if selected_template in template_names:
            settings.remove(_SETTINGS_TEMPLATE_KEY)

    if _TEMPLATES_LOCATION_STR in existing_paths:
        existing_paths.remove(_TEMPLATES_LOCATION_STR)
        settings.setValue(_SETTINGS_TEMPLATE_PATH_KEY, existing_paths)
        changes_made = True
    if changes_made:
        print("Your Qt Designer settings have been updated. Please restart Qt Designer to see changes.")
    else:
        print("There was nothing to clean up.")

    orig_contents = venv_activate.read_text()
    if venv_cmd in orig_contents:
        new_contents = orig_contents.replace(venv_cmd, "")
        with venv_activate.open("w") as f:
            f.write(new_contents)
            print(f"Your virtual environment activation ({str(venv_activate)}) has been cleared of accwidgets "
                  f"Qt Designer modification.")
            print(f"Please re-activate your virtual environment: deactivate && source {venv_activate}")


_SETTINGS_TEMPLATE_PATH_KEY = "FormTemplatePaths"
_SETTINGS_TEMPLATE_KEY = "FormTemplate"
_SETTINGS_PROJECT_NAME = "QtProject"
_SETTINGS_APP_NAME = "Designer"
# Qt Designer displays the last 2 components of the path in the title. So we setup the last 2 to be nice
# and readable "accwidgets/templates".
_TEMPLATES_LOCATION = Path(__file__).parent.absolute() / "accwidgets" / "templates"
_TEMPLATES_LOCATION_STR = str(_TEMPLATES_LOCATION)


_VENV_CONFIG: Optional[Tuple[Path, str]] = -1  # type: ignore  # special case


def _get_venv_config() -> Optional[Tuple[Path, str]]:
    global _VENV_CONFIG
    if _VENV_CONFIG == -1:  # First time only. Should never be -1, only Path or None
        cli_path = os.popen("command -v accwidgets-cli").read()
        if cli_path:
            cli = Path(cli_path.strip())
            venv_activate = cli.parent / "activate"
            if not venv_activate.is_file():
                _VENV_CONFIG = None
            else:
                config_dir = cli.parent.parent / "etc" / "xdg"
                if not config_dir.exists():
                    config_dir.mkdir(parents=True)
                venv_cmd = f"alias designer='XDG_CONFIG_HOME={config_dir} PYQTDESIGNERPATH=$(accwidgets-cli designer-paths):$PYQTDESIGNERPATH designer'"
                os.environ["XDG_CONFIG_HOME"] = str(config_dir)  # For any QSettings that are called in this file
                _VENV_CONFIG = venv_activate, venv_cmd
        else:
            _VENV_CONFIG = None
    return _VENV_CONFIG
