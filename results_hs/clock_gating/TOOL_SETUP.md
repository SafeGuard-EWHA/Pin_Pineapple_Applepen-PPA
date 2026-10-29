# 실행 환경 설치 기록

## 사용 환경

- Windows의 WSL2, Ubuntu 24.04.5 LTS.
- Yosys 0.58: 공식 `v0.58` 태그 및 고정된 ABC 하위 모듈에서 빌드하였다.
- OpenROAD `26Q2-1164-g08f67ee5ec`: 공식 문서가 안내하는 VaultLink의 Ubuntu 24.04 deb를 사용하였다.
- ORFS 커밋 `7bf5a814e47c54ec6c64692b464d398184d99891`.
- Icarus Verilog 12.0 stable, KLayout 0.28.16(Ubuntu 패키지).
- OpenROAD의 대응 OpenSTA 하위 모듈은 `76c4d6df3537ccce331b5caa812196c3330ba7c4`이다. 해당 소스의 `Power::findActivity`에서 클럭 핀에도 알려진 활동도가 우선 적용됨을 확인하고, 작은 ICG 회로의 VCD 실험으로 별도 검증하였다.

최종 실행 버전·파일 해시는 `environment.json`을 기준으로 한다. 과거 팀 환경과 도구 버전이 같다고 주장하지 않으며, 게이팅 전후 설계를 위 환경에서 함께 재합성한다.

## 설치 명령

Ubuntu에서 필요한 권한으로 실행한다. 다음은 설치 흐름이며, 저장소 원본 RTL이나 보고서를 수정하지 않는다.

```sh
apt-get update
apt-get install -y build-essential clang bison flex libreadline-dev gawk tcl-dev \
  libffi-dev git pkg-config python3 python3-pip python3-venv zlib1g-dev \
  cmake ninja-build iverilog klayout wget curl
git clone --depth 1 --branch v0.58 https://github.com/YosysHQ/yosys.git yosys
git -C yosys submodule update --init --depth 1
cd yosys
make config-clang
make -j8
make install
```

OpenROAD 다운로드 URL:

`https://vaultlink.precisioninno.com/api/releases/26Q2-1164-g08f67ee5ec/openroad_26Q2-1164-g08f67ee5ec_amd64-ubuntu-24.04.deb/download`

다운로드 파일 SHA-256:

`f3f1eeaa18f327503f72cc45dcef5b1514ec2e89726ec53b4553bf4f951168a3`

확인 후 `apt-get install ./openroad_ubuntu24.deb`로 설치하였다.

ORFS는 다른 공정의 대용량 파일을 제외한 sparse checkout을 사용하였다. 재현 시 위에 적은 커밋으로 고정하고, 최소한 `flow/scripts`, `flow/util`, `flow/platforms/asap7`, **`flow/platforms/common`** 및 flow의 최상위 파일이 있어야 한다. 최초 시도에서 common 디렉터리가 빠져 `lcu_kogge_stone.v` 오류가 발생했으며 이를 추가하여 해결하였다.

## 메모리 부족 및 복구

초기 WSL 환경은 RAM 약 7.6 GiB, swap 2 GiB였다. 첫 본격 ABC 매핑 중 WSL 응답 지연이 발생하였다. 커널 로그에는 2026-10-30 05:57 KST에 `yosys-abc`가 메모리 부족으로 종료되었다는 기록이 남았다. 해당 프로세스의 당시 anon-rss는 6,855,888 KiB였으며, 부모 Yosys의 메모리도 별도로 필요하였다.

작업용 WSL을 종료하고 사용자 `.wslconfig`에 다음 설정을 적용하였다. Windows 자체를 추가 재부팅하지 않았다.

```ini
[wsl2]
memory=10GB
swap=8GB
```

재시작 후 Linux에서 RAM 약 9.7 GiB와 swap 8 GiB를 확인하였다. 합성은 설계별로 순차 실행한다. 메모리 부족 시 결과가 생성되지 않은 실행을 성공으로 처리하지 않는다.

## 분석 도구 검증

`power_engine_probe.py`는 ICG 1개와 FF 1개를 구성하고, 동일 클럭에서 enable을 계속 켠 경우와 초기 2회 이후 끈 경우의 VCD를 각각 분석한다. 두 경우 모두 11개 핀에 VCD 활동이 적용되고 미주석 핀은 0개였다. 이는 분석 도구 확인이며 NPU의 전력 감소율이 아니다.

생성 클럭의 파형이 해석되기 전에 VCD를 읽으면 SDC 주기가 0으로 표시될 수 있어, 타이밍 해석 후 VCD를 읽도록 순서를 정하였다. 클럭 게이팅으로 펄스가 줄어든 경우의 평균 VCD 주기와 SDC 기준 주기 차이는 별도로 기록한다.

공식 자료: [WSL 설치](https://learn.microsoft.com/en-us/windows/wsl/install), [ORFS pre-built 안내](https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildWithPrebuilt.html), [사용 버전의 OpenSTA 전력 코드](https://github.com/The-OpenROAD-Project/OpenSTA/blob/76c4d6df3537ccce331b5caa812196c3330ba7c4/power/Power.cc).
