#!/usr/bin/env python3
"""
街聲波影片數據自動更新器
掃描影片檔案，自動更新現有 HTML 中的 videoData 部分
保持原有設計，只更新數據
"""

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime

class VideoDataUpdater:
    def __init__(self, base_dir=None):
        """初始化影片數據更新器"""
        self.base_dir = Path(base_dir) if base_dir else Path(".")
        self.video_dir = self.base_dir / "街聲波影片"
        self.thumbnail_dir = self.base_dir / "thumbnails"
        self.html_file = self.base_dir / "index.html"
        
        # 支援的影片格式
        self.video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.m4v'}
        
        # 影片數據
        self.video_data = {
            'neutral': [],
            'realistic': [], 
            'sky': [],
            'mountain': [],
            'forest': [],
            'ocean': [],
            'funny': []
        }
        
    def scan_videos(self):
        """掃描影片資料夾，更新數據結構"""
        print("🎬 掃描影片檔案...")
        
        if not self.video_dir.exists():
            print(f"❌ 找不到影片資料夾: {self.video_dir}")
            return False
        
        # 掃描各分類
        categories = {
            'neutral': '中性素材（15）',
            'realistic': '寫實人物（15）',
            'funny': '搞怪素材（11）'
        }
        
        # 山海大地自然的子分類
        nature_subcategories = {
            'sky': '天空系列（8）',
            'mountain': '山脈系列（7）',
            'forest': '森林系列（7）',
            'ocean': '海洋系列（8）'
        }
        
        total_videos = 0
        
        # 處理一級分類
        for key, folder_name in categories.items():
            folder_path = self.video_dir / folder_name
            if folder_path.exists():
                videos = self.scan_folder(folder_path, key)
                self.video_data[key] = videos
                total_videos += len(videos)
                print(f"  📂 {folder_name}: {len(videos)} 個影片")
        
        # 處理山海大地自然子分類
        nature_base = self.video_dir / "山海大地自然（30）"
        if nature_base.exists():
            for key, folder_name in nature_subcategories.items():
                folder_path = nature_base / folder_name
                if folder_path.exists():
                    videos = self.scan_folder(folder_path, key, is_nature_sub=True)
                    self.video_data[key] = videos
                    total_videos += len(videos)
                    print(f"  📂 {folder_name}: {len(videos)} 個影片")
        
        print(f"✅ 總計掃描到 {total_videos} 個影片")
        return True
    
    def scan_folder(self, folder_path, category_key, is_nature_sub=False):
        """掃描單個資料夾"""
        videos = []
        
        for file_path in folder_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.video_extensions:
                # 生成相對路徑
                if is_nature_sub:
                    relative_path = f"街聲波影片/山海大地自然（30）/{folder_path.name}/{file_path.name}"
                else:
                    relative_path = f"街聲波影片/{folder_path.name}/{file_path.name}"
                
                video_info = {
                    'name': file_path.name,
                    'title': self.generate_title(file_path.stem),
                    'duration': self.estimate_duration(file_path),
                    'path': relative_path,
                    'trending': self.is_trending(file_path.name)
                }
                
                videos.append(video_info)
        
        return sorted(videos, key=lambda x: x['name'])
    
    def generate_title(self, filename):
        """根據檔案名生成友善的標題"""
        # 移除 .mp4 後綴（如果有雙重後綴）
        title = filename.replace('.mp4', '')
        
        # 替換底線為破折號
        title = title.replace('_', ' - ')
        
        # 處理常見模式
        replacements = {
            '幾何圖形 - ': '幾何圖形 - ',
            '抽象圖案 - ': '抽象圖案 - ',
            '簡約背景 - ': '簡約背景 - ',
            '音波視覺化 - ': '音波視覺化 - '
        }
        
        for old, new in replacements.items():
            title = title.replace(old, new)
        
        return title.strip(' -')
    
    def estimate_duration(self, video_path):
        """估算影片時長"""
        try:
            # 可以用 ffprobe 獲取真實時長，這裡用簡化版本
            size_mb = video_path.stat().st_size / (1024 * 1024)
            
            if size_mb < 3:
                return f"0:{20 + int(size_mb * 10):02d}"
            elif size_mb < 10:
                return f"0:{40 + int(size_mb * 5):02d}"
            elif size_mb < 30:
                return f"1:{int(size_mb * 2):02d}"
            else:
                return f"2:{int(size_mb // 10):02d}"
        except:
            return "1:30"
    
    def is_trending(self, filename):
        """判斷是否為熱門影片"""
        trending_keywords = [
            '極光', '台北', '粒子', '彩色波', '聽團仔', '80 年代', 
            '可愛', '日落', '陽光', '波光', '人潮', '三角形'
        ]
        return any(keyword in filename for keyword in trending_keywords)
    
    def generate_thumbnails(self):
        """生成缺失的縮圖"""
        print("📸 檢查並生成縮圖...")
        
        # 檢查 ffmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except:
            print("⚠️  未安裝 ffmpeg，跳過縮圖生成")
            return
        
        generated_count = 0
        
        for category_videos in self.video_data.values():
            for video in category_videos:
                if self.generate_single_thumbnail(video):
                    generated_count += 1
        
        if generated_count > 0:
            print(f"✅ 生成了 {generated_count} 個新縮圖")
        else:
            print("✅ 所有縮圖都已存在")
    
    def generate_single_thumbnail(self, video_info):
        """生成單個縮圖"""
        video_path = self.base_dir / video_info['path']
        
        # 計算縮圖路徑
        thumbnail_path = self.thumbnail_dir / video_info['path'].replace('街聲波影片/', '').replace('.mp4', '.jpg')
        
        # 如果縮圖已存在，跳過
        if thumbnail_path.exists():
            return False
        
        # 創建目錄
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            cmd = [
                'ffmpeg', '-i', str(video_path), '-ss', '00:00:01',
                '-vframes', '1', '-vf', 
                'scale=270:480:force_original_aspect_ratio=decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2',
                '-q:v', '2', '-y', str(thumbnail_path)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"  📸 生成縮圖: {thumbnail_path.name}")
            return True
        except:
            print(f"  ❌ 縮圖生成失敗: {video_path.name}")
            return False
    
    def update_html(self):
        """更新 HTML 檔案中的 videoData"""
        print("🌐 更新 HTML 檔案...")
        
        if not self.html_file.exists():
            print(f"❌ 找不到 HTML 檔案: {self.html_file}")
            return False
        
        # 讀取現有 HTML
        with open(self.html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 準備新的數據
        new_data = self.prepare_video_data_js()
        
        # 使用正則表達式找到並替換 videoData 部分
        pattern = r'(const videoData = \{)(.*?)(\};)'
        
        def replace_video_data(match):
            return f"{match.group(1)}{new_data}{match.group(3)}"
        
        # 替換數據
        new_html_content = re.sub(pattern, replace_video_data, html_content, flags=re.DOTALL)
        
        # 檢查是否成功替換
        if new_html_content == html_content:
            print("⚠️  未找到 videoData 區塊，可能需要手動更新")
            return False
        
        # 寫回檔案
        with open(self.html_file, 'w', encoding='utf-8') as f:
            f.write(new_html_content)
        
        print("✅ HTML 檔案更新成功")
        return True
    
    def prepare_video_data_js(self):
        """準備 JavaScript 格式的影片數據"""
        # 計算合併的數據
        all_videos = []
        nature_videos = []
        
        for key, videos in self.video_data.items():
            all_videos.extend(videos)
            if key in ['sky', 'mountain', 'forest', 'ocean']:
                nature_videos.extend(videos)
        
        # 生成 JavaScript 對象字符串
        js_data = {
            'all': all_videos,
            **self.video_data,
            'nature': nature_videos
        }
        
        # 轉換為 JavaScript 格式
        def format_video_data(data):
            lines = []
            lines.append("            all: [],")
            
            for key in ['neutral', 'realistic', 'sky', 'mountain', 'forest', 'ocean', 'funny']:
                if key in data and data[key]:
                    lines.append(f"            {key}: [")
                    for video in data[key]:
                        trending = ', trending: true' if video.get('trending') else ''
                        lines.append(f"                {{ name: '{video['name']}', title: '{video['title']}', duration: '{video['duration']}', path: '{video['path']}'{trending} }},")
                    lines.append("            ],")
            
            return '\\n'.join(lines)
        
        result = format_video_data(js_data)
        
        # 添加合併邏輯
        result += """
        
        // 合併所有影片到 all 分類
        videoData.all = [
            ...videoData.neutral,
            ...videoData.realistic,
            ...videoData.sky,
            ...videoData.mountain,
            ...videoData.forest,
            ...videoData.ocean,
            ...videoData.funny
        ];

        // 合併自然分類的子系列
        videoData.nature = [
            ...videoData.sky,
            ...videoData.mountain,
            ...videoData.forest,
            ...videoData.ocean
        ];"""
        
        return result
    
    def run(self):
        """執行完整流程"""
        print("🚀 街聲波影片數據自動更新器")
        print("=" * 40)
        
        # 1. 掃描影片
        if not self.scan_videos():
            return False
        
        # 2. 生成縮圖
        self.generate_thumbnails()
        
        # 3. 更新 HTML
        if not self.update_html():
            return False
        
        # 4. 統計信息
        total_videos = sum(len(videos) for videos in self.video_data.values())
        
        print("=" * 40)
        print("🎉 更新完成！")
        print(f"🎬 總影片數: {total_videos}")
        print(f"📂 分類明細:")
        for key, videos in self.video_data.items():
            if videos:
                print(f"   {key}: {len(videos)} 個")
        
        return True

def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description="街聲波影片數據自動更新器")
    parser.add_argument("--dir", "-d", help="專案目錄路徑", default=".")
    
    args = parser.parse_args()
    
    # 執行更新
    updater = VideoDataUpdater(args.dir)
    success = updater.run()
    
    if success:
        print("\\n✅ 可以執行以下指令部署:")
        print("git add . && git commit -m '自動更新影片數據' && git push")
    else:
        print("\\n❌ 更新失敗")

if __name__ == "__main__":
    main()
