# GX4HRXL / XMG EVO 固件 Capsule 逆向记录

更新时间：2026-07-14

## 结论摘要

XMG 的 `GXxHXxxN114A13_CAP.efi` 是 AMI UAF 自包含 EFI 刷写程序，不是裸 BIOS 或独立 EC 文件。其末尾 `@ROM` 记录包含 EFI/Tiano 压缩的完整 32 MiB SPI ROM。

从 ROM 中已经定位到两个 256 KiB 的 ITE EC 固件 Freeform 区域：

- GUID `207F94A8-238E-11E8-B467-0ED5F89F718B`
- GUID `207F989A-238E-11E8-B467-0ED5F89F718B`

两者均包含 8051 代码、`ITE EC-V14.6` 和 `ITE8850-PD` 字符串，说明 EC/PD 固件确实嵌在 BIOS ROM 中。两个镜像的 `ECVER` 目标版本字节都是 `0x81`，编码为 `2.01`；项目 ID 分别为 `0x00` 和 `0x0A`。

当前机器由 Linux/DMI 报告：

```text
Manufacturer: MECHREVO
Product: WUJIE 14 Series GX4HRXL
Board: GX4HRXL
BIOS: N.1.14A13
EC: 2.12
```

## 原始文件

```text
Firmware_XMG_EVO_AMD_M24_XEV14AM24_XEV15AM24_BIOS_N.1.14A13_EC_2.01.00(1).zip
sha256: ea6799b1f1d2e13f2d5463260d57c97e3d58220eeea77b7cadeff27944c4d8a4

GXxHXxxN114MRO50_CAP(1).EXE
sha256: 1c832aa5d3bfb0e06ea3a8b86c674f4329f978c884547408f186e973749487cc
```

XMG ZIP 内容只有一个 EFI 刷写程序和启动脚本：

```text
GXxHXxxN114A13_CAP.efi       9,410,280 bytes
EFI/BOOT/startup.nsh
f.nsh                         -> GXxHXxxN114A13_CAP.efi
```

XMG CHANGELOG 明确写有：BIOS `N.1.14A13` / EC `2.01.00`。

## 1. UAF 容器识别

EFI 文件是 PE32+ EFI application，PE 本体后面附加 AMI UAF 记录。关键记录：

```text
offset    tag   size       value/aux
0x09cbe0  @UAF  0x85c5b0   0x00109e3c
0x09cbf0  @UII  0x60       0xff006199
0x09cc50  @CMD  0x30       0x17a1
0x09cc80  @ROM  0x85c510   aux=0x1f7e
```

`@ROM` 后 8 字节是 EFI compression header：

```text
compressed size:   0x85c4f2
decompressed size: 0x02000000  (32 MiB)
```

XMG EFI 内置的默认命令字符串为：

```text
/p /b /n /x /r /capsule
```

AMI AFU 中还包含 `/E`、`/ECUF` 等通用选项，但本机实测 `/E` 报 `No EC blocks found in system ROM`，原因是 EC 不是普通 SPI ROM layout 中的 EC block。

## 2. ROM 解压过程

本机已有 `UEFIExtract NE alpha 75`，另外用 `uv` 临时加载 `uefi_firmware` 的 `EfiDecompress` 解压器。解压调用的逻辑是：

```python
stream = rom_record[offset + 16 : offset + 16 + 8 + compressed_size]
rom = EfiDecompress(stream, len(stream))
```

恢复结果：

```text
analysis/extracted/xmg.efi-compressed
size:   0x85c4fa (含 8 字节 EFI compression header)
sha256: aae1d8a5889a4566d400143f84c0577cbd2f0221df237bdf57f202e892950928

analysis/extracted/xmg-32m.rom
size:   0x02000000 (33,554,432 bytes)
sha256: 1086406573cf3e54d1a0b976ad66b61334be545ba3143693a972b4d4faa002e4
```

使用的本地脚本：

```text
tools/uaf_inspect.py
tests/test_uaf_inspect.py
```

脚本只做 UAF 记录扫描、边界检查和离线解压，不执行 EFI/BIOS/EC 程序。单元测试 3 项全部通过。

## 3. UEFIExtract 结果

```bash
uefiextract analysis/extracted/xmg-32m.rom
```

输出：

```text
analysis/extracted/xmg-32m.rom.report.txt
analysis/extracted/xmg-32m.rom.dump/
```

共展开约 7,768 个节点，dump 目录约 82 MiB。ROM 中发现两个明确的 Freeform Raw 文件：

```text
Base 0x133A900  size 0x4001C  GUID 207F94A8-238E-11E8-B467-0ED5F89F718B
Base 0x137A920  size 0x4001C  GUID 207F989A-238E-11E8-B467-0ED5F89F718B
```

两者 Raw body 均为 262,144 字节，且 FFS header/data checksum 均有效。提取副本：

```text
analysis/ec-payloads/207F94A8.bin
sha256: 6a60785d370403a7db6c4a8f21ab6f230d37dc72c2d2febd5726113eaca2db56

analysis/ec-payloads/207F989A.bin
sha256: 093bbcf49fe53344b46d2fce7163aad80536e594d85d95befb76aed511ef3bd5
```

## 4. ITE EC 固件特征

两个 256 KiB 镜像都具有 8051 风格复位/中断向量，并包含：

```text
ITE EC-V14.6
ECVER
ITE8850-PD
UsbPdVer:01.00
```

其中 `ITE8850-PD` 更像 ITE8850 USB-PD 子固件/功能块；仅凭这些字符串不能把主 EC 芯片型号直接确定为 IT8850。主 EC 仍需芯片丝印或工程资料确认。

两份镜像的目标版本字段：

```text
ECVER 81 00 ...   # 项目 ID 0x00
ECVER 81 0A ...   # 项目 ID 0x0A
```

版本字节编码由 ReFlash 代码确认：

```text
major = version_byte >> 6
minor = version_byte & 0x3f
```

所以：

```text
0x81 = 2.01
0x8c = 2.12
```

## 5. ReFlash 版本比较逻辑

UEFI 模块路径：

```text
.../104 ReFlash/1 PE32 image section/body.bin
sha256: 6ba741a7e8e7019e4ba3f1bd4494c02bbf6e9cf984f557dc44e9cffb82967805
```

其中有与屏幕输出完全一致的字符串：

```text
EC F/W: %01d.%02d. It's the latest version
```

反汇编可还原出以下流程：

1. 通过 EC 命令 `0x54` 读取当前版本字节。
2. 通过 EC 命令 `0x55` 读取项目/机型 ID。
3. 在选定的 256 KiB EC raw image 中扫描 `ECVER`。
4. 读取 `ECVER + 5` 作为目标版本字节。
5. 读取 `ECVER + 6` 作为目标项目 ID，并与 EC 命令 `0x55` 返回值匹配。
6. 若当前版本 `<=` 目标版本，进入擦除、编程、校验；若当前版本 `>` 目标版本，跳到 “latest version” 分支。

关键分支位于 ReFlash PE 映像 RVA 约 `0x90CF`：

```asm
cmp  byte ptr [rbp+0x38], cl   ; 当前版本 vs capsule 目标版本
jbe  0x9047                    ; 当前 <= 目标，继续刷写
                                 ; 否则跳过并显示 latest version
```

这解释了用户看到的行为：`/EC` 路径正确进入 capsule，BIOS 更新完成后 ReFlash 读取到当前 EC `2.12`，发现 capsule 目标是 `2.01`，于是主动跳过 EC。

## 6. 当前未做的事情

没有执行以下操作：

- 没有运行任何刷写程序。
- 没有修改原始 EFI、EXE、ROM 或 EC payload。
- 没有向 EC 端口 `0x62/0x66` 发送写命令。
- 没有尝试 `/ALL`、`/RECOVERY` 或 FFS/ROM 重打包刷写。

## 7. 风险与可行性评估

理论上有两个离线修改方向：

### 方向 A：改 EC 目标版本字段

将对应镜像的 `ECVER` 目标字节从 `0x81` 改成大于当前版本的值，例如 `0x8D`，版本比较即可通过。但这可能破坏 EC 固件内部 checksum/签名，且修改后 EC 可能把自身报告为伪造的 `2.13`。

### 方向 B：改 ReFlash 的比较分支

将 `jbe` 改成无条件跳转，使其忽略版本比较。这样不修改 EC payload，但需要重打包 ReFlash 所在 FFS/ROM，并且可能触发 AMI Secure Flash、BIOS Guard 或平台签名校验。

目前没有证据表明公开 capsule 接受这两种修改后的完整 ROM。因此不能把修改后的 ROM 直接交给 `/EC` 或 `/CAPSULE` 刷写。

## 8. 最安全的下一步

优先级从高到低：

1. 取得厂商工程版 EC downgrade capsule 或 ITE ISP 工具。
2. 确认主板上 ITE 芯片的完整丝印，以便选择正确的 ITE 工具和容量配置。
3. 在离线副本上验证 EC payload 内部 checksum、FFS checksum、UAF 压缩/记录校验和 Secure Flash 签名覆盖范围。
4. 只有在有原始 EC 备份和外部编程恢复手段时，才考虑任何强制降级实验。

## 9. Slimbook 基准补充

已补充 Slimbook EVO AMD 固件分析。Slimbook GOS07 包提供独立 EC payload `GXxHXxx_21.200` 和独立刷写器 `ifux64.efi`，其中 project `0x00` 的 EC `2.12` payload 与机械革命 MRO50 ROM 内嵌 payload 字节级完全一致。后续 EC 2.12 研究应优先以 Slimbook GOS07 / Mechrevo MRO50 的 project `0x00` payload 作为基准，而不是 XMG A13 的 EC 2.01 payload。

## 相关分析文件

- [tools/uaf_inspect.py](../tools/uaf_inspect.py)
- [tests/test_uaf_inspect.py](../tests/test_uaf_inspect.py)
- [docs/slimbook-research.md](slimbook-research.md)
- [analysis/extracted/xmg-32m.rom](../analysis/extracted/xmg-32m.rom)
- [analysis/extracted/xmg.efi-compressed](../analysis/extracted/xmg.efi-compressed)
- [analysis/ec-payloads/207F94A8.bin](../analysis/ec-payloads/207F94A8.bin)
- [analysis/ec-payloads/207F989A.bin](../analysis/ec-payloads/207F989A.bin)
- [analysis/extracted/xmg-32m.rom.report.txt](../analysis/extracted/xmg-32m.rom.report.txt)
