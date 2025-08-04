#!/usr/bin/env python3
"""
街聲波影片縮圖生成器
自動為所有影片生成靜態縮圖 (JPG格式)
"""

import os
import sys
from pathlib import Path
import subprocess

def check_ffmpeg():
    """檢查是否安裝了 ffmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_ffmpeg_instructions():
    """顯示 ffmpeg 安裝說明"""
    print("🚨 需要安裝 ffmpeg 才能生成縮圖！")
    print("\n在 Mac 上安裝 ffmpeg：")
    print("brew install ffmpeg")
    print("\n安裝完成後重新執行此腳本")

def generate_thumbnail(video_path, output_path, timestamp="00:00:01"):
    """
    生成單個影片的縮圖
    
    Args:
        video_path: 影片檔案路徑
        output_path: 輸出縮圖路徑
        timestamp: 截取時間點 (預設第1秒)
    """
    try:
        # ffmpeg 指令：截取指定時間點的幀，調整為 IG 直式比例
        cmd = [
            'ffmpeg',
            '-i', str(video_path),           # 輸入影片
            '-ss', timestamp,                # 時間點
            '-vframes', '1',                 # 只要1幀
            '-vf', 'scale=270:480:force_original_aspect_ratio=decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2,setsar=1',  # IG 直式比例 9:16
            '-q:v', '2',                     # 高品質 (1-31, 越小越好)
            '-y',                            # 覆蓋已存在的檔案
            str(output_path)
        ]
        
        # 執行 ffmpeg
        result = subprocess.run(cmd, 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.PIPE, 
                              text=True)
        
        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr
            
    except Exception as e:
        return False, str(e)

def process_video_folder(video_folder, output_folder):
    """
    處理整個影片資料夾（支援多層結構）
    
    Args:
        video_folder: 街聲波影片資料夾路徑
        output_folder: 縮圖輸出資料夾路徑
    """
    video_folder = Path(video_folder)
    output_folder = Path(output_folder)
    
    # 建立輸出資料夾結構
    output_folder.mkdir(exist_ok=True)
    
    # 支援的影片格式
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.m4v'}
    
    # 統計
    total_videos = 0
    success_count = 0
    error_count = 0
    
    print("🎬 開始生成影片縮圖...")
    print(f"📁 影片資料夾: {video_folder}")
    print(f"📁 輸出資料夾: {output_folder}")
    print("-" * 50)
    
    def process_directory(current_dir, output_dir, level=0):
        """遞迴處理目錄"""
        nonlocal total_videos, success_count, error_count
        
        indent = "  " * level
        folder_name = current_dir.name
        print(f"{indent}📂 處理分類: {folder_name}")
        
        # 建立對應的輸出資料夾
        output_dir.mkdir(exist_ok=True)
        
        # 先處理當前目錄的影片檔案
        video_files = [f for f in current_dir.iterdir() 
                      if f.is_file() and f.suffix.lower() in video_extensions]
        
        for video_file in video_files:
            total_videos += 1
            
            # 生成縮圖檔案名 (影片名.jpg)
            thumbnail_name = video_file.stem + '.jpg'
            thumbnail_path = output_dir / thumbnail_name
            
            print(f"{indent}  🎯 {video_file.name} -> {thumbnail_name}")
            
            # 生成縮圖
            success, error = generate_thumbnail(video_file, thumbnail_path)
            
            if success:
                success_count += 1
                print(f"{indent}    ✅ 成功")
            else:
                error_count += 1
                print(f"{indent}    ❌ 失敗: {error[:100]}...")
        
        # 再處理子目錄
        sub_dirs = [d for d in current_dir.iterdir() if d.is_dir()]
        for sub_dir in sub_dirs:
            sub_output_dir = output_dir / sub_dir.name
            process_directory(sub_dir, sub_output_dir, level + 1)
    
    # 開始遞迴處理
    for category_folder in video_folder.iterdir():
        if not category_folder.is_dir():
            continue
            
        category_output = output_folder / category_folder.name
        process_directory(category_folder, category_output)
    
    # 顯示結果
    print("\n" + "=" * 50)
    print("🎉 縮圖生成完成！")
    print(f"📊 總計: {total_videos} 個影片")
    print(f"✅ 成功: {success_count} 個")
    print(f"❌ 失敗: {error_count} 個")
    print(f"📁 縮圖位置: {output_folder}")
    
    # 顯示資料夾結構
    print(f"\n📋 生成的縮圖結構:")
    for item in sorted(output_folder.rglob("*.jpg")):
        relative_path = item.relative_to(output_folder)
        print(f"  📸 {relative_path}")


def main():
    """主程式"""
    print("🎬 街聲波影片縮圖生成器")
    print("=" * 30)
    
    # 檢查 ffmpeg
    if not check_ffmpeg():
        install_ffmpeg_instructions()
        return
    
    # 設定路徑 (根據你的檔案結構調整)
    script_dir = Path(__file__).parent
    video_folder = script_dir / "街聲波影片"
    output_folder = script_dir / "thumbnails"
    
    # 檢查影片資料夾是否存在
    if not video_folder.exists():
        print(f"❌ 找不到影片資料夾: {video_folder}")
        print("請確認腳本在正確的位置，或修改 video_folder 路徑")
        return
    
    # 開始處理
    try:
        process_video_folder(video_folder, output_folder)
    except KeyboardInterrupt:
        print("\n⏹️  使用者中斷處理")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")

if __name__ == "__main__":
    main()
