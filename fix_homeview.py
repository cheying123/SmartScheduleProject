with open(r'd:\SmartScheduleProject\frontend\src\views\HomeView.vue', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 删除第 50-55 行（索引 49-54）
del lines[49:55]

with open(r'd:\SmartScheduleProject\frontend\src\views\HomeView.vue', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('✅ 已删除第 50-55 行的重复代码')
print(f'文件总行数: {len(lines)}')
