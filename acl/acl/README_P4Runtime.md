# P4Runtime ACL Controller 使用说明

本文档说明如何使用P4Runtime动态控制面来替代静态JSON配置文件管理ACL规则。

## 文件说明

- `acl_controller.py`: 主要的P4Runtime控制器程序
- `run_acl_controller.py`: 简化的控制器运行脚本
- `s1-acl.json`: 原始的静态配置文件（用于对比）

## 使用方法

### 方法1: 使用静态JSON配置（原始方法）

1. 编译P4程序：
   ```bash
   make build
   ```

2. 运行带有静态配置的网络：
   ```bash
   make run
   ```

### 方法2: 使用P4Runtime动态控制面（新方法）

1. 编译P4程序：
   ```bash
   make build
   ```

2. 启动不带配置的mininet网络：
   ```bash
   # 修改Makefile或手动启动mininet，不加载s1-acl.json
   sudo python utils/run_exercise.py -t topology.json
   ```

3. 在另一个终端运行P4Runtime控制器：
   ```bash
   python3 acl_controller.py
   ```
   
   或者使用简化脚本：
   ```bash
   python3 run_acl_controller.py
   ```

## P4Runtime控制器功能

控制器会自动安装以下规则：

### IPv4转发规则
- 10.0.1.1 -> MAC 00:00:00:00:01:01, 端口 1
- 10.0.1.2 -> MAC 00:00:00:00:01:02, 端口 2  
- 10.0.1.3 -> MAC 00:00:00:00:01:03, 端口 3
- 10.0.1.4 -> MAC 00:00:00:00:01:04, 端口 4

### ACL规则
- 丢弃所有目标端口为80的UDP数据包
- 丢弃所有目标IP为10.0.1.4的数据包

## 测试验证

使用以下命令测试ACL功能：

1. 测试UDP端口80被阻止：
   ```bash
   # 在h1终端
   ./send.py 10.0.1.2 UDP 80 "This should be dropped"
   ```

2. 测试其他UDP端口正常：
   ```bash
   # 在h1终端  
   ./send.py 10.0.1.2 UDP 8080 "This should work"
   ```

3. 测试IP 10.0.1.4被阻止：
   ```bash
   # 在h1终端
   ./send.py 10.0.1.4 UDP 8080 "This should be dropped"
   ```

4. 测试其他IP正常：
   ```bash
   # 在h1终端
   ./send.py 10.0.1.3 UDP 8080 "This should work"
   ```

## P4Runtime vs 静态配置对比

| 特性 | 静态JSON配置 | P4Runtime动态控制 |
|------|-------------|------------------|
| 规则更新 | 需要重启交换机 | 实时动态更新 |
| 灵活性 | 低 | 高 |
| 调试能力 | 有限 | 强大（可读取表项、计数器等） |
| 复杂度 | 简单 | 中等 |
| 生产环境适用性 | 有限 | 高 |

## 注意事项

1. 确保P4程序已正确编译（存在build/acl.p4.p4info.txt和build/acl.json）
2. P4Runtime控制器需要在mininet启动后运行
3. 控制器会持续运行并监控网络状态，使用Ctrl+C退出
4. 如果遇到连接问题，检查mininet是否正确启动且P4Runtime端口（50051）可用

## 扩展功能

控制器支持以下扩展：
- 动态添加/删除ACL规则
- 读取和显示表项
- 监控计数器统计
- 实时网络状态查看