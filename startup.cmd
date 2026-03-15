@echo off
echo 카카오톡 설치 시작...
start /wait C:\Users\WDAGUtilityAccount\Desktop\PlaybotMacro\KakaoTalk_Setup.exe

echo 매크로 실행...
start "" C:\Users\WDAGUtilityAccount\Desktop\PlaybotMacro\playbot_sword_upgrade.exe

echo 매크로 창 왼쪽 절반 배치...
timeout /t 2 /nobreak >nul
powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $p=Get-Process playbot_sword_upgrade -ErrorAction SilentlyContinue|Select-Object -First 1; if($p -and $p.MainWindowHandle -ne 0){Add-Type 'using System;using System.Runtime.InteropServices;public class W{[DllImport(\"user32.dll\")]public static extern bool MoveWindow(IntPtr h,int x,int y,int w,int h2,bool r);}'; $s=[System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea; [W]::MoveWindow($p.MainWindowHandle,0,0,[int]($s.Width/2),$s.Height,$true)}"
