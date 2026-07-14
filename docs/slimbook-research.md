# Slimbook EVO AMD 固件基准分析

更新时间：2026-07-14

## 结论摘要

Slimbook 的 EVO AMD 包比 XMG 包更适合作为 GX4HRXL 家族 EC 研究基准，因为它同时提供：

- BIOS capsule EFI
- 解压后的 32 MiB BIOS ROM
- 独立 256 KiB EC payload
- 独立 EC 刷写器 `ifux64.efi`

当前最有价值的包是：

```text
SLIMBOOK.Evo_AMD8845HS_BIOS_N.1.14GOS07_EC_2.12.00.zip
sha256: 0060f7d217a392c8ca6a81ef698cfad5766421ed231b50a7c507f443f44bba42
```

其中独立 EC 文件 `GXxHXxx_21.200` 是 EC `2.12`、project `0x00`，并且和机械革命 `MRO50` ROM 内嵌的 `207F94A8` EC payload 字节级完全一致：

```text
sha256: 34c050d30772da07ef262fc7016e0677b9b1b4cdcd90cf43d93f0f15bf6a38c2
```

因此，若当前机器 EC 已是 `2.12`，它很可能对应 project `0x00` 分支；Slimbook GOS07 可以作为 EC 2.12 payload 的公开、可复核来源。

## Slimbook 包结构

GOS07:

```text
BIOS/GXxHXxxN114GOS07.ROM        33,554,432 bytes
BIOS/GXxHXxxN114GOS07_CAP.efi     9,343,640 bytes
BIOS/F.nsh
BIOS/CHANGELOG_BIOS.txt
EC/GXxHXxx_21.200                   262,144 bytes
EC/ifux64.efi                        94,784 bytes
EC/F.nsh
EC/CHANGELOG_EC.txt
readme.txt
```

GOS05:

```text
BIOS/GXxHXxxN114GOS05.ROM        33,554,432 bytes
BIOS/GXxHXxxN114GOS05_CAP.efi     9,341,592 bytes
EC/GXxHXxx_21.000                   262,144 bytes
EC/ifux64.efi                        94,784 bytes
```

两版的 `ifux64.efi` 完全相同：

```text
b013ddd898061a96bd10c8faffeb0b54300e5be4dcd933728b8a927b759f362d
```

EC 更新脚本很直接：

```text
IFUX64.efi GXxHXxx_21.200 0 1
IFUX64.efi GXxHXxx_21.000 0 1
```

BIOS 更新脚本会刷整片 SPI：

```text
GXxHXxxN114GOS07_CAP.efi GXxHXxxN114GOS07.ROM /p /b /n /r /x /l /k /reboot
GXxHXxxN114GOS05_CAP.efi GXxHXxxN114GOS05.ROM /p /b /n /r /x /l /k /reboot
```

## BIOS capsule 解压

Slimbook capsule 仍是 AMI UAF 自包含 EFI 程序，`@ROM` 中的 EFI/Tiano 压缩流解压后与包内 `.ROM` 文件完全一致。

GOS07:

```text
wrapper sha256: 3f69fefe4e30cad588b469104827633f69f1452ce713fd7503310c76b95d3dda
@ROM compressed: 0x84c0a2
@ROM original:   0x02000000
ROM sha256:      26280fbb32b64b348e1d425133fa9af9325ac6cdad191179ae130d2e1c7a9e13
```

GOS05:

```text
wrapper sha256: 88deed047e1f808455e792d0b28e01c0b495b34ce09bc849fa4aa55b737f292a
@ROM compressed: 0x84b8a5
@ROM original:   0x02000000
ROM sha256:      8136d53d7770d809c9dfd516f1c24f78a6645d2719c837f3a6f2f391736811e9
```

解压产物：

```text
analysis/slimbook/GOS07/extracted/GOS07-32m.rom
analysis/slimbook/GOS05/extracted/GOS05-32m.rom
```

## EC payload 矩阵

ROM 中仍存在两个 ITE EC freeform raw payload：

- GUID `207F94A8-238E-11E8-B467-0ED5F89F718B`
- GUID `207F989A-238E-11E8-B467-0ED5F89F718B`

`ECVER` 编码仍是：

```text
major = version_byte >> 6
minor = version_byte & 0x3f
```

| 来源 | GUID | body offset | sha256 | EC version | project |
| --- | --- | ---: | --- | --- | --- |
| Slimbook GOS07 | `207F94A8` | `0x133a274` | `34c050d30772da07ef262fc7016e0677b9b1b4cdcd90cf43d93f0f15bf6a38c2` | `2.12` | `0x00` |
| Slimbook GOS07 | `207F989A` | `0x137a294` | `8091c5d628edf740235965d0ba25448270c9e389096c8c921ae9156fc52f498c` | `2.04` | `0x0a` |
| Slimbook GOS05 | `207F94A8` | `0x133a22c` | `f1f589565c1f62130354ff697757c02fa92115914e2b9f8a79f757d2c367014c` | `2.10` | `0x00` |
| Slimbook GOS05 | `207F989A` | `0x137a24c` | `8091c5d628edf740235965d0ba25448270c9e389096c8c921ae9156fc52f498c` | `2.04` | `0x0a` |
| XMG A13 | `207F94A8` | `0x133a91c` | `6a60785d370403a7db6c4a8f21ab6f230d37dc72c2d2febd5726113eaca2db56` | `2.01` | `0x00` |
| XMG A13 | `207F989A` | `0x137a93c` | `093bbcf49fe53344b46d2fce7163aad80536e594d85d95befb76aed511ef3bd5` | `2.01` | `0x0a` |
| Mechrevo MRO50 | `207F94A8` | `0x133953c` | `34c050d30772da07ef262fc7016e0677b9b1b4cdcd90cf43d93f0f15bf6a38c2` | `2.12` | `0x00` |
| Mechrevo MRO50 | `207F989A` | `0x137955c` | `093bbcf49fe53344b46d2fce7163aad80536e594d85d95befb76aed511ef3bd5` | `2.01` | `0x0a` |
| Mechrevo MRO17 | `207F94A8` | `0x133a094` | `8536e5a5ac5a32609e4d76cbca80ef4a0523fc4c3838b1d4b5c5988435771152` | `2.04` | `0x00` |
| Mechrevo MRO17 | `207F989A` | `0x137a0b4` | `093bbcf49fe53344b46d2fce7163aad80536e594d85d95befb76aed511ef3bd5` | `2.01` | `0x0a` |

提取副本：

```text
analysis/slimbook/ec-payloads/GOS07-207F94A8.bin
analysis/slimbook/ec-payloads/GOS07-207F989A.bin
analysis/slimbook/ec-payloads/GOS05-207F94A8.bin
analysis/slimbook/ec-payloads/GOS05-207F989A.bin
analysis/mechrevo/ec-payloads/MRO50-207F94A8.bin
analysis/mechrevo/ec-payloads/MRO50-207F989A.bin
analysis/mechrevo/ec-payloads/MRO17-207F94A8.bin
analysis/mechrevo/ec-payloads/MRO17-207F989A.bin
```

## 机械革命 EXE 封装差异

机械革命 Windows EXE 也是 AMI UAF，但尾部压缩流长度与文件剩余长度有轻微差异：

```text
MRO50 missing tail bytes: 3
MRO17 missing tail bytes: 2
```

在内存中补 0 后，EFI/Tiano 解压成功：

```text
analysis/mechrevo/MRO50-32m.rom
sha256: 0017fc530d2b8e5c35cd77bc4e817c009910dafa92750171ec5d220ddb72724b

analysis/mechrevo/MRO17-32m.rom
sha256: 0851cea275db89ca9f6b88741a3d74e739d37b42d1c2e6678722e45edcdbed7b
```

这说明现有 `tools/uaf_inspect.py` 对 Windows EXE 的严格边界检查会误拒这类尾部 padding 缺失样本。后续可以给工具增加一个显式 `--pad-truncated-stream` 选项，但不应默认静默补齐。

## 对后续研究的影响

1. Slimbook GOS07 是 EC `2.12` / project `0x00` 的首选公开基准。
2. 机械革命 MRO50 的 project `0x00` EC 与 Slimbook GOS07 完全一致，可作为交叉验证。
3. XMG A13 的两个 EC payload 都是 `2.01`，因此对 EC `2.12` 当前机器会触发 ReFlash 的 downgrade 跳过逻辑。
4. Slimbook 独立 EC 刷写链路值得继续逆向：`ifux64.efi` + 256 KiB payload 比 BIOS capsule 内的 ReFlash 路径更窄，变量更少。
5. 仍不建议直接运行 Slimbook 或机械革命刷写脚本；本分析只做离线提取、哈希和静态字段确认。

