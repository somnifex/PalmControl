#!/usr/bin/env python3
"""
平滑移动测试脚本
测试鼠标移动的流畅性和性能
"""

import time
import math
from input_controller import InputController

def test_smooth_movement():
    """测试平滑移动功能"""
    print("开始测试鼠标移动平滑性...")
    
    # 创建输入控制器实例
    controller = InputController(sensitivity=2.0)
    
    # 设置不同的平滑参数进行测试
    test_configs = [
        {"smoothing": 1.0, "fps": 60, "description": "无平滑"},
        {"smoothing": 0.5, "fps": 120, "description": "中等平滑"},
        {"smoothing": 0.3, "fps": 120, "description": "高平滑"},
        {"smoothing": 0.1, "fps": 120, "description": "最高平滑"}
    ]
    
    for config in test_configs:
        print(f"\n测试配置: {config['description']}")
        print(f"平滑因子: {config['smoothing']}, 最大FPS: {config['fps']}")
        
        # 应用配置
        controller.set_smoothing_factor(config['smoothing'])
        controller.set_max_fps(config['fps'])
        
        # 重置位置
        controller.reset_position()
        
        print("开始圆形轨迹测试 (5秒)...")
        start_time = time.time()
        
        # 执行圆形轨迹移动
        radius = 0.2  # 相对半径
        center_x, center_y = 0.5, 0.5  # 屏幕中心
        
        while time.time() - start_time < 5.0:
            t = (time.time() - start_time) * 2  # 2圈/秒
            x = center_x + radius * math.cos(t)
            y = center_y + radius * math.sin(t)
            
            # 确保坐标在有效范围内
            x = max(0.1, min(0.9, x))
            y = max(0.1, min(0.9, y))
            
            controller.move_mouse(x, y)
            time.sleep(0.016)  # ~60fps
        
        # 返回中心
        controller.move_mouse(0.5, 0.5)
        time.sleep(1)
    
    print("\n测试完成！")
    print("观察不同配置下鼠标移动的流畅性差异。")

def test_performance():
    """测试性能"""
    print("\n开始性能测试...")
    
    controller = InputController(sensitivity=2.0)
    controller.set_smoothing_factor(0.3)
    controller.set_max_fps(120)
    
    # 快速移动测试
    start_time = time.time()
    move_count = 0
    
    for i in range(1000):
        x = 0.3 + 0.4 * (i % 2)  # 在屏幕左右摆动
        y = 0.5
        controller.move_mouse(x, y)
        move_count += 1
        time.sleep(0.001)  # 1ms间隔
    
    elapsed = time.time() - start_time
    actual_fps = move_count / elapsed
    
    print(f"性能测试结果:")
    print(f"总移动次数: {move_count}")
    print(f"耗时: {elapsed:.2f}秒")
    print(f"实际FPS: {actual_fps:.1f}")
    
if __name__ == "__main__":
    print("PalmControl 鼠标移动平滑性测试")
    print("=" * 40)
    
    try:
        # 运行测试
        test_smooth_movement()
        test_performance()
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
