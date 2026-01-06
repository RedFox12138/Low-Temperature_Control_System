# -*- coding: utf-8 -*-
"""
调试脚本 - Multifields Scanning Stage 设备诊断
用于排查设备通道无法打开和启动无响应的问题

使用方法:
1. 修改 DEVICE_PORT 为实际的设备端口
2. 运行脚本: python debug_multifields.py
"""

import pyvisa
import time
import sys

# ==================== 配置区 ====================
DEVICE_PORT = 'COM3'  # 修改为实际设备端口
TIMEOUT_MS = 5000     # 超时时间(毫秒)
# ===============================================


class MultifieldsDebugger:
    """Multifields 设备调试工具"""
    
    def __init__(self):
        self.rm = None
        self.device = None
        self.port = DEVICE_PORT
        
    def step1_list_devices(self):
        """步骤1: 列出所有可用设备"""
        print("\n" + "="*60)
        print("步骤1: 检测可用设备")
        print("="*60)
        
        try:
            self.rm = pyvisa.ResourceManager()
            resources = self.rm.list_resources()
            
            if len(resources) == 0:
                print("❌ 未检测到任何设备!")
                print("   请检查:")
                print("   - 设备是否已连接")
                print("   - USB驱动是否已安装")
                print("   - 设备是否已开机")
                return False
            else:
                print(f"✓ 检测到 {len(resources)} 个设备:")
                for i, res in enumerate(resources, 1):
                    print(f"   {i}. {res}")
                return True
                
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def step2_open_device(self):
        """步骤2: 尝试打开设备"""
        print("\n" + "="*60)
        print(f"步骤2: 打开设备 {self.port}")
        print("="*60)
        
        try:
            self.device = self.rm.open_resource(self.port)
            self.device.timeout = TIMEOUT_MS
            
            # 获取设备信息
            print(f"✓ 设备已打开")
            print(f"   端口: {self.port}")
            print(f"   超时: {TIMEOUT_MS} ms")
            
            # 尝试获取设备属性
            try:
                print(f"   波特率: {self.device.baud_rate}")
                print(f"   数据位: {self.device.data_bits}")
                print(f"   停止位: {self.device.stop_bits}")
                print(f"   校验位: {self.device.parity}")
            except:
                print("   (无法读取串口参数)")
            
            return True
            
        except Exception as e:
            print(f"❌ 无法打开设备: {e}")
            print(f"   请确认端口 '{self.port}' 是否正确")
            return False
    
    def step3_test_basic_communication(self):
        """步骤3: 测试基本通信"""
        print("\n" + "="*60)
        print("步骤3: 测试基本通信")
        print("="*60)
        
        test_commands = [
            ('[v?]', '查询电压'),
            ('[read:pulse?]', '查询脉冲'),
        ]
        
        results = []
        for cmd, desc in test_commands:
            print(f"\n测试命令: {cmd} ({desc})")
            try:
                response = self.device.query(cmd)
                print(f"✓ 响应: {response.strip()}")
                results.append(True)
            except pyvisa.errors.VisaIOError as e:
                print(f"❌ 超时或无响应: {e}")
                results.append(False)
            except Exception as e:
                print(f"❌ 错误: {e}")
                results.append(False)
            
            time.sleep(0.2)
        
        return any(results)
    
    def step4_test_channel_operations(self):
        """步骤4: 测试通道操作"""
        print("\n" + "="*60)
        print("步骤4: 测试通道操作")
        print("="*60)
        
        test_channels = [1, 2, 3]
        
        for ch in test_channels:
            print(f"\n测试通道 {ch}:")
            
            # 测试 numb 命令
            try:
                cmd = f'[numb:{ch}:4096]'
                print(f"  发送: {cmd}")
                self.device.write(cmd)
                time.sleep(0.1)
                print(f"  ✓ numb 命令已发送")
            except Exception as e:
                print(f"  ❌ numb 命令失败: {e}")
                continue
            
            # 测试 nch 命令
            try:
                cmd = f'[nch:{ch}]'
                print(f"  发送: {cmd}")
                self.device.write(cmd)
                time.sleep(0.1)
                print(f"  ✓ nch 命令已发送")
            except Exception as e:
                print(f"  ❌ nch 命令失败: {e}")
                continue
            
            # 测试 set_target 命令
            try:
                cmd = f'[target:ch{ch}:50.000000]'
                print(f"  发送: {cmd}")
                self.device.write(cmd)
                time.sleep(0.1)
                print(f"  ✓ set_target 命令已发送")
            except Exception as e:
                print(f"  ❌ set_target 命令失败: {e}")
                continue
            
            # 读取状态
            try:
                response = self.device.query('[v?]')
                print(f"  ✓ 当前状态: {response.strip()}")
            except Exception as e:
                print(f"  ❌ 无法读取状态: {e}")
    
    def step5_test_movement_commands(self):
        """步骤5: 测试移动命令"""
        print("\n" + "="*60)
        print("步骤5: 测试移动命令")
        print("="*60)
        
        test_commands = [
            ('[cap:100nF]', 'cap', '设置电容'),
            ('[volt:+100V]', 'volt', '设置电压'),
            ('[+:100]', 'pulse', '正向脉冲'),
            ('[-:100]', 'back', '反向脉冲'),
            ('[stop]', 'reset', '停止'),
        ]
        
        for cmd, name, desc in test_commands:
            print(f"\n测试 {name} ({desc}):")
            print(f"  命令: {cmd}")
            
            try:
                self.device.write(cmd)
                time.sleep(0.2)
                print(f"  ✓ 命令已发送")
                
                # 尝试读取响应
                try:
                    self.device.read_termination = '\n'
                    response = self.device.read()
                    print(f"  响应: {response.strip()}")
                except pyvisa.errors.VisaIOError:
                    print(f"  (无响应数据)")
                    
            except Exception as e:
                print(f"  ❌ 错误: {e}")
    
    def step6_interactive_test(self):
        """步骤6: 交互式测试"""
        print("\n" + "="*60)
        print("步骤6: 交互式测试模式")
        print("="*60)
        print("输入命令直接发送给设备 (输入 'quit' 退出)")
        print("示例命令:")
        print("  [v?]")
        print("  [nch:1]")
        print("  [cap:100nF]")
        print("-"*60)
        
        while True:
            try:
                cmd = input("\n命令 > ").strip()
                
                if cmd.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not cmd:
                    continue
                
                # 判断是查询还是写入
                if '?' in cmd:
                    response = self.device.query(cmd)
                    print(f"响应: {response.strip()}")
                else:
                    self.device.write(cmd)
                    print(f"✓ 已发送")
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                print("\n中断")
                break
            except Exception as e:
                print(f"错误: {e}")
    
    def close(self):
        """关闭设备连接"""
        if self.device:
            try:
                self.device.close()
                print("\n✓ 设备连接已关闭")
            except:
                pass
    
    def run_full_diagnostic(self):
        """运行完整诊断流程"""
        print("\n" + "="*60)
        print("Multifields Scanning Stage 设备诊断工具")
        print("="*60)
        
        # 步骤1: 列出设备
        if not self.step1_list_devices():
            print("\n诊断终止: 无法检测到设备")
            return
        
        # 步骤2: 打开设备
        if not self.step2_open_device():
            print("\n诊断终止: 无法打开设备")
            return
        
        # 步骤3: 测试基本通信
        if not self.step3_test_basic_communication():
            print("\n⚠ 警告: 基本通信测试失败")
            print("可能的原因:")
            print("  - 设备未正确初始化")
            print("  - 波特率不匹配")
            print("  - 命令格式不正确")
        
        # 步骤4: 测试通道操作
        self.step4_test_channel_operations()
        
        # 步骤5: 测试移动命令
        self.step5_test_movement_commands()
        
        # 步骤6: 交互式测试
        print("\n" + "="*60)
        choice = input("是否进入交互式测试模式? (y/n): ").strip().lower()
        if choice == 'y':
            self.step6_interactive_test()
        
        # 总结
        print("\n" + "="*60)
        print("诊断完成")
        print("="*60)
        print("\n建议:")
        print("1. 检查上述测试中失败的步骤")
        print("2. 确认设备固件版本和命令协议")
        print("3. 查看设备手册确认命令格式")
        print("4. 如果所有命令都无响应,检查设备波特率设置")


def main():
    """主函数"""
    debugger = MultifieldsDebugger()
    
    try:
        debugger.run_full_diagnostic()
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n严重错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        debugger.close()


if __name__ == "__main__":
    main()
