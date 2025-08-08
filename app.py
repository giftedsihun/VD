import streamlit as st
import yt_dlp
import os
import tempfile
import shutil
from pathlib import Path
import time
import threading
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="비디오 다운로더",
    page_icon="📹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'download_progress' not in st.session_state:
    st.session_state.download_progress = {}
if 'download_status' not in st.session_state:
    st.session_state.download_status = {}

class DownloadProgress:
    def __init__(self, url):
        self.url = url
        self.progress = 0
        self.status = "준비 중..."
        self.filename = ""
        self.error = None
        
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                self.progress = int((d['downloaded_bytes'] / d['total_bytes']) * 100)
            elif 'total_bytes_estimate' in d:
                self.progress = int((d['downloaded_bytes'] / d['total_bytes_estimate']) * 100)
            self.status = f"다운로드 중... {self.progress}%"
            self.filename = d.get('filename', '')
        elif d['status'] == 'finished':
            self.progress = 100
            self.status = "다운로드 완료!"
            self.filename = d.get('filename', '')

def get_video_info(url):
    """비디오 정보 추출"""
    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'N/A'),
                'uploader': info.get('uploader', 'N/A'),
                'duration': info.get('duration_string', 'N/A'),
                'view_count': info.get('view_count', 'N/A'),
                'upload_date': info.get('upload_date', 'N/A'),
                'description': info.get('description', 'N/A')[:200] + '...' if info.get('description') else 'N/A',
                'thumbnail': info.get('thumbnail', None)
            }
    except Exception as e:
        return {'error': str(e)}

def download_video(url, output_path, quality='best', download_type='video', progress_callback=None):
    """비디오 다운로드"""
    try:
        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_callback.progress_hook] if progress_callback else [],
        }

        if download_type == 'video':
            ydl_opts["format"] = quality
        elif download_type == 'audio':            ydl_opts["format"] = "bestaudio/best"
            ydl_opts[\'postprocessors\'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        if progress_callback:
            progress_callback.error = str(e)
            progress_callback.status = f\"오류: {str(e)}\"
        return False

def main():디오 다운로더")
    st.markdown("YouTube, Instagram, X.com 등 다양한 플랫폼에서 비디오를 다운로드하세요!")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 다운로드 타입 선택
        download_type = st.radio(
            "다운로드 타입 선택",
            ("비디오 (Video)", "오디오 (Audio)"),
            index=0
        )

        # 품질 선택
        quality_options = {
            'best': '최고 품질',
            'worst': '최저 품질',
            'bestvideo[height<=720]+bestaudio/best[height<=720]': '720p',
            'bestvideo[height<=480]+bestaudio/best[height<=480]': '480p',
            'bestvideo[height<=360]+bestaudio/best[height<=360]': '360p'
        }
        selected_quality = st.selectbox(
            "비디오 품질 선택",
            options=list(quality_options.keys()),
            format_func=lambda x: quality_options[x],
            index=0
        )
        
        # 다운로드 폴더 설정
        download_folder = st.text_input(
            "다운로드 폴더",
            value="./downloads",
            help="비디오가 저장될 폴더 경로"
        )
        
        # 지원 플랫폼 정보
        st.header("📱 지원 플랫폼")
        st.markdown("""
        - YouTube
        - Instagram
        - X.com (Twitter)
        - TikTok
        - Facebook
        - Vimeo
        - 기타 500+ 사이트
        """)
    
    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔗 URL 입력")
        url = st.text_input(
            "비디오 URL을 입력하세요:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="YouTube, Instagram, X.com 등의 비디오 URL을 입력하세요"
        )
        
        # URL 검증 및 정보 표시
        if url:
            if st.button("📋 비디오 정보 확인", type="secondary"):
                with st.spinner("비디오 정보를 가져오는 중..."):
                    info = get_video_info(url)
                    
                if 'error' in info:
                    st.error(f"오류: {info['error']}")
                else:
                    st.success("비디오 정보를 성공적으로 가져왔습니다!")
                    
                    # 비디오 정보 표시
                    st.subheader("📺 비디오 정보")
                    
                    info_col1, info_col2 = st.columns([2, 1])
                    
                    with info_col1:
                        st.write(f"**제목:** {info['title']}")
                        st.write(f"**업로더:** {info['uploader']}")
                        st.write(f"**재생 시간:** {info['duration']}")
                        st.write(f"**조회수:** {info['view_count']:,}" if isinstance(info['view_count'], int) else f"**조회수:** {info['view_count']}")
                        st.write(f"**업로드 날짜:** {info['upload_date']}")
                        st.write(f"**설명:** {info['description']}")
                    
                    with info_col2:
                        if info['thumbnail']:
                            st.image(info['thumbnail'], caption="썸네일", use_column_width=True)
        
        # 다운로드 버튼
        if url and st.button("⬇️ 다운로드 시작", type="primary"):
            # 다운로드 폴더 생성
            os.makedirs(download_folder, exist_ok=True)
            
            # 진행 상황 추적 객체 생성
            progress_tracker = DownloadProgress(url)
            st.session_state.download_progress[url] = progress_tracker
            
            # 다운로드 시작
            with st.spinner("다운로드를 시작하는 중..."):
                def download_thread():
                    success = download_video(url, download_folder, selected_quality, download_type, progress_tracker)                    if success:
                        progress_tracker.status = "다운로드 완료!"
                    else:
                        progress_tracker.status = f"다운로드 실패: {progress_tracker.error}"
                
                # 백그라운드에서 다운로드 실행
                thread = threading.Thread(target=download_thread)
                thread.start()
                
                st.success("다운로드가 시작되었습니다! 아래에서 진행 상황을 확인하세요.")
    
    with col2:
        st.header("📊 다운로드 현황")
        
        if st.session_state.download_progress:
            for url, progress in st.session_state.download_progress.items():
                with st.container():
                    st.write(f"**URL:** {url[:50]}...")
                    st.write(f"**상태:** {progress.status}")
                    
                    if progress.progress > 0:
                        st.progress(progress.progress / 100)
                        st.write(f"진행률: {progress.progress}%")
                    
                    if progress.filename:
                        st.write(f"**파일:** {os.path.basename(progress.filename)}")
                    
                    st.divider()
        else:
            st.info("아직 다운로드 중인 항목이 없습니다.")
    
    # 다운로드된 파일 목록
    st.header("📁 다운로드된 파일")
    
    if os.path.exists(download_folder):
        files = [f for f in os.listdir(download_folder) if os.path.isfile(os.path.join(download_folder, f))]
        
        if files:
            for file in files:
                file_path = os.path.join(download_folder, file)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    file_size_mb = file_size / (1024 * 1024)
                else:
                    file_size_mb = 0.0 # 파일이 없으면 0으로 설정하거나 다른 처리를 할 수 있습니다.
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"📄 {file}")
                
                with col2:
                    st.write(f"{file_size_mb:.1f} MB")
                
                with col3:
                    # 파일 다운로드 버튼
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="다운로드",
                            data=f.read(),
                            file_name=file,
                            mime="video/mp4"
                        )
        else:
            st.info("다운로드된 파일이 없습니다.")
    
    # 자동 새로고침 (진행 상황 업데이트용)
    if st.session_state.download_progress:
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()






