#!/bin/zsh
# tools/dev-env/scripts/android-emulator.sh
# headless 에뮬레이터를 띄우고, 부팅이 끝나면 실행 중인 dev 서버 포트에 adb reverse를 건다.
# devctl의 android-emulator 작업이 launchd 아래에서 실행한다. ANDROID_AVD, EMULATOR_PORT, DEVCTL은 plist가 주입한다.
set -euo pipefail

serial="emulator-${EMULATOR_PORT}"

emulator -avd "$ANDROID_AVD" -port "$EMULATOR_PORT" -no-window -no-audio -no-boot-anim &
emu_pid=$!
trap 'adb -s "$serial" emu kill >/dev/null 2>&1 || kill "$emu_pid" 2>/dev/null' TERM INT

adb -s "$serial" wait-for-device
until [[ "$(adb -s "$serial" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]]; do
  sleep 2
done
echo "[android-emulator] $serial 부팅 완료"

"$DEVCTL" reverse || echo "[android-emulator] adb reverse 생략 (실행 중인 서버 없음)"

wait "$emu_pid"
