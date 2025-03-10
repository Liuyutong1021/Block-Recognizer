import winreg

def get_scaling_factor():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics") as key:
        value = winreg.QueryValueEx(key, "AppliedDPI")[0]
        return value / 96