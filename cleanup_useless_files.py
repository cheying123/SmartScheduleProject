#!/usr/bin/env python3
"""
智能日程管理系统 - 清理无用文件脚本

此脚本用于删除项目中已识别的无用文件和目录。
注意：运行此脚本将永久删除以下文件：
1. test.py - 临时测试文件
2. fix_homeview.py - 一次性修复脚本
3. LocationList-master 目录 - 未使用的天气地点列表
4. LocationList-master.zip - 上述目录的压缩文件
"""

import os
import sys
import shutil
from pathlib import Path

def confirm_deletion():
    """确认是否要删除文件"""
    print("=" * 60)
    print("⚠️  警告：即将删除以下无用文件/目录:")
    print("=" * 60)
    print("1. test.py - 临时测试文件")
    print("2. fix_homeview.py - 一次性修复脚本")
    print("3. LocationList-master/ - 未使用的天气地点列表目录")
    print("4. LocationList-master.zip - 未使用的天气地点列表压缩文件")
    print("=" * 60)
    
    response = input("是否继续删除？(输入 'yes' 确认): ")
    return response.lower() == 'yes'

def delete_file(filepath):
    """安全删除文件"""
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"✅ 已删除文件: {filepath}")
            return True
        except Exception as e:
            print(f"❌ 删除文件失败 {filepath}: {e}")
            return False
    else:
        print(f"ℹ️  文件不存在，跳过: {filepath}")
        return True

def delete_directory(dirpath):
    """安全删除目录"""
    if os.path.exists(dirpath):
        try:
            shutil.rmtree(dirpath)
            print(f"✅ 已删除目录: {dirpath}")
            return True
        except Exception as e:
            print(f"❌ 删除目录失败 {dirpath}: {e}")
            return False
    else:
        print(f"ℹ️  目录不存在，跳过: {dirpath}")
        return True

def main():
    """主函数"""
    print("🧹 智能日程管理系统 - 无用文件清理工具")
    
    if not confirm_deletion():
        print("\n❌ 用户取消操作，未删除任何文件。")
        return
    
    # 定义要删除的文件和目录
    files_to_delete = [
        ("test.py", "file"),
        ("fix_homeview.py", "file"),
        ("LocationList-master", "directory"),
        ("LocationList-master.zip", "file")
    ]
    
    # 转换为绝对路径
    base_path = Path(__file__).parent
    deleted_items = []
    
    for item, item_type in files_to_delete:
        full_path = base_path / item
        
        if item_type == "file":
            success = delete_file(full_path)
        elif item_type == "directory":
            success = delete_directory(full_path)
        else:
            success = False
            
        if success:
            deleted_items.append(str(full_path))
    
    print("\n" + "=" * 60)
    if deleted_items:
        print(f"🎉 完成！已成功删除 {len(deleted_items)} 个项目:")
        for item in deleted_items:
            print(f"   • {item}")
    else:
        print("ℹ️  没有文件被删除。")
    print("=" * 60)

if __name__ == "__main__":
    main()