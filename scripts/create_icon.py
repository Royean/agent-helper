#!/usr/bin/env python3
"""
创建 AgentLinker 应用图标
生成多尺寸图标和 ICNS 文件
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    print("安装 Pillow: pip install Pillow")
    HAS_PIL = False

if HAS_PIL:
    import os
    
    # 图标尺寸
    SIZES = [16, 32, 64, 128, 256, 512, 1024]
    
    def create_icon(size):
        """创建单个尺寸的图标"""
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 渐变色
        start_color = (66, 135, 245)    # 蓝色
        end_color = (102, 126, 234)     # 浅蓝
        
        # 绘制圆角矩形背景
        margin = size // 8
        radius = size // 5
        
        # 背景渐变
        for y in range(margin, size - margin):
            progress = (y - margin) / (size - 2 * margin)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * progress)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * progress)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * progress)
            
            y_top = max(margin, y)
            y_bottom = min(size - margin, y + 1)
            
            draw.rounded_rectangle(
                [(margin, y_top), (size - margin, y_bottom)],
                radius=radius,
                fill=(r, g, b, 255)
            )
        
        # 绘制机器人图标（白色）
        center = size // 2
        head_radius = size // 5
        
        # 头部
        draw.ellipse(
            [(center - head_radius, center - head_radius - size//20),
             (center + head_radius, center + head_radius - size//20)],
            fill=(255, 255, 255, 255)
        )
        
        # 身体
        body_width = head_radius
        body_height = head_radius * 1.5
        draw.rounded_rectangle(
            [(center - body_width, center),
             (center + body_width, center + body_height)],
            radius=body_width // 2,
            fill=(255, 255, 255, 255)
        )
        
        # 眼睛
        eye_radius = head_radius // 4
        eye_offset = head_radius // 2
        eye_y = center - head_radius // 2
        
        # 左眼
        draw.ellipse(
            [(center - eye_offset - eye_radius, eye_y - eye_radius),
             (center - eye_offset + eye_radius, eye_y + eye_radius)],
            fill=(66, 135, 245, 255)
        )
        
        # 右眼
        draw.ellipse(
            [(center + eye_offset - eye_radius, eye_y - eye_radius),
             (center + eye_offset + eye_radius, eye_y + eye_radius)],
            fill=(66, 135, 245, 255)
        )
        
        # 天线
        antenna_height = size // 10
        draw.line(
            [(center, center - head_radius - size//20),
             (center, center - head_radius - size//20 - antenna_height)],
            fill=(255, 255, 255, 255),
            width=max(2, size // 50)
        )
        
        # 天线球
        ball_radius = size // 25
        draw.ellipse(
            [(center - ball_radius, center - head_radius - size//20 - antenna_height - ball_radius),
             (center + ball_radius, center - head_radius - size//20 - antenna_height + ball_radius)],
            fill=(255, 200, 50, 255)
        )
        
        return img
    
    # 创建图标目录
    os.makedirs('/tmp/agentlinker_icons', exist_ok=True)
    
    # 生成所有尺寸
    print("生成图标...")
    for size in SIZES:
        img = create_icon(size)
        filename = f'/tmp/agentlinker_icons/icon_{size}x{size}.png'
        img.save(filename)
        print(f"  ✓ {size}x{size}")
    
    # 创建 ICNS 文件（需要 iconutil）
    print("\n创建 ICNS 文件...")
    iconset_dir = '/tmp/agentlinker_icons/icon.iconset'
    os.makedirs(iconset_dir, exist_ok=True)
    
    # 复制为 iconset 格式
    import shutil
    for size in SIZES:
        src = f'/tmp/agentlinker_icons/icon_{size}x{size}.png'
        
        # icon_512x512.png
        if size == 512:
            shutil.copy(src, f'{iconset_dir}/icon_512x512.png')
            shutil.copy(src, f'{iconset_dir}/icon_256x256@2x.png')
        elif size == 256:
            shutil.copy(src, f'{iconset_dir}/icon_256x256.png')
            shutil.copy(src, f'{iconset_dir}/icon_128x128@2x.png')
        elif size == 128:
            shutil.copy(src, f'{iconset_dir}/icon_128x128.png')
            shutil.copy(src, f'{iconset_dir}/icon_64x64@2x.png')
        elif size == 64:
            shutil.copy(src, f'{iconset_dir}/icon_64x64.png')
            shutil.copy(src, f'{iconset_dir}/icon_32x32@2x.png')
        elif size == 32:
            shutil.copy(src, f'{iconset_dir}/icon_32x32.png')
            shutil.copy(src, f'{iconset_dir}/icon_16x16@2x.png')
        elif size == 16:
            shutil.copy(src, f'{iconset_dir}/icon_16x16.png')
    
    # 使用 iconutil 创建 icns
    import subprocess
    try:
        subprocess.run([
            'iconutil', '-c', 'icns', iconset_dir,
            '-o', '/tmp/agentlinker_icons/icon.icns'
        ], check=True)
        print("  ✓ ICNS 文件创建成功")
    except subprocess.CalledProcessError:
        print("  ⚠ iconutil 不可用，跳过 ICNS 创建")
    except FileNotFoundError:
        print("  ⚠ iconutil 未找到（仅 macOS 可用）")
    
    print("\n✅ 图标生成完成！")
    print("位置：/tmp/agentlinker_icons/")
    
    # 复制到项目目录
    project_icon_dir = '/tmp/AgentLinker/assets'
    os.makedirs(project_icon_dir, exist_ok=True)
    shutil.copy('/tmp/agentlinker_icons/icon_512x512.png', f'{project_icon_dir}/icon.png')
    if os.path.exists('/tmp/agentlinker_icons/icon.icns'):
        shutil.copy('/tmp/agentlinker_icons/icon.icns', f'{project_icon_dir}/icon.icns')
    
    print(f"\n已复制到：{project_icon_dir}/")
