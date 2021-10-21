import os
import winreg

def check_registry_entry_for_osu():
    reg_table = winreg.ConnectRegistry(None, winreg.HKEY_CLASSES_ROOT)

    try:
        with winreg.OpenKey(reg_table, r'osu!\shell\open\command', 0, winreg.KEY_READ) as handle:
            _, osu_exe_path, _ = winreg.EnumValue(handle, 0)

        osu_exe_path = osu_exe_path.split(" ")[0].strip('"')
        osu_path = os.path.split(osu_exe_path)[0]
    except:
        osu_path = None

    return osu_path