try : 
    from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QToolButton
    from PySide2.QtWidgets import QVBoxLayout, QLabel, QLineEdit
    from PySide2.QtWidgets import QHBoxLayout, QPushButton, QFileDialog
    from PySide2.QtWidgets import QMessageBox, QPlainTextEdit
    from PySide2.QtWidgets import QComboBox
    from PySide2 import QtCore
except Exception :
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QToolButton
    from PySide6.QtWidgets import QVBoxLayout, QLabel, QLineEdit
    from PySide6.QtWidgets import QHBoxLayout, QPushButton, QFileDialog
    from PySide6.QtWidgets import QMessageBox, QPlainTextEdit
    from PySide6.QtWidgets import QComboBox
    from PySide6 import QtCore

import sys, os, re
import maya.cmds as cmds

from publisher.core.play_blast import PlayblastManager
from publisher.event.event_handler import *
from loader.core.video_player import VideoPlayer
from publisher.core.publish import PublishManager

class PublisherDialog(QMainWindow):
    def __init__(self, video_path, ct):
        super().__init__()
        self.ct = ct
        print(f"여긴 Publisher Dialog : {self.ct}")
        self.setWindowTitle("Publish")
        self.setGeometry(100, 100, 650, 1000)
        print(f"** 퍼블리시에 드디어 clickedtask가 들어오다 {ct}")
        print(f"task id : {ct.id}")

        self.dept = ct.step
        self.work_path = ct.set_deep_path("work")
        self.pub_path = ct.set_deep_path("pub")
        ct.set_deep_path("pub", "data")
        self.root_path = ct.root_path
        self.project_name = ct.project_name #entityname shotname assetname, #entity parent seq asset type
        self.entity_name = ct.entity_name
        self.entity_parent = ct.entity_parent
        self.dept = ct.step
        self.center_window()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        full_path = cmds.file(q=True, sceneName=True)
        self.file_name, ext = os.path.basename(full_path).split('.')
        self.file_path = cmds.file(q=True, sceneName=True)
        # print(folder_path, file_name_with_ext)
        # work -> pub으로 경로변경

        # 파일명 Label + LineEdit
        filename_container = QHBoxLayout()
        filename_label = QLabel("File name:")
        self.filename_input = QLineEdit(self.file_name)
        self.filename_input.setDisabled(True)
        self.version_btn = QToolButton()
        self.version_btn.setCheckable(True)
        self.version_btn.setText("version up")
        self.version_btn.setFixedSize(100, 30)

        # 파일 경로 Label + LineEdit
        filepath_container = QHBoxLayout()
        filepath_label = QLabel("File path:")
        self.filepath_input = QLineEdit(self.pub_path)
        self.filepath_input.setDisabled(True)
        #self.filepath_input = QLineEdit("/nas/eval/show")

        # 파일 타입 
        filetype_container = QHBoxLayout()
        filetype_label = QLabel("File of type:")
        self.format_combo = QComboBox()
        self.format_combo.addItems([".mb", ".ma"])  # 옵션 추가
        self.format_combo.setCurrentText(".mb")  # 기본값 설정
        self.usd_format_combo = QComboBox()
        self.usd_format_combo.addItems([".usda"])

        # Comment
        comment_container = QVBoxLayout()   
        comment_label = QLabel("Comment")
        self.plain_text_edit = QPlainTextEdit()
        self.plain_text_edit.setPlaceholderText("Write your comment here ......")

        # Preview
        preview_container = QVBoxLayout()
        preview_h_container = QHBoxLayout()
        self.preview_label = QLabel("Preview")
        self.preview_frame = VideoPlayer(video_path)

        # pub or not
        button_container = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        publish_btn = QPushButton("Publish")

        # Style Sheet
        filepath_label.setFixedWidth(80)
        filename_label.setFixedWidth(80)
        filetype_label.setFixedWidth(80)
        comment_label.setFixedHeight(30)
        self.plain_text_edit.setFixedHeight(250)
        self.preview_label.setFixedHeight(30)
        self.preview_frame.setFixedHeight(350)
        self.preview_frame.setStyleSheet("border:1px solid black;")
        cancel_btn.setFixedHeight(30)
        publish_btn.setFixedHeight(30)

        style = """
            color: white;  /* 글씨를 검정색으로 유지 */
            background-color:rgb(93, 93, 93);  /* 배경색 변경 (비활성화된 느낌 최소화) */
        """
        self.filename_input.setStyleSheet(style)
        self.filepath_input.setStyleSheet(style)

        # Event Handle
        cancel_btn.clicked.connect(self.close)
        self.version_btn.clicked.connect(lambda: on_version_click(self, self.file_name))
        publish_btn.clicked.connect(self.publish_final_output)

        # layout
        filepath_container.addWidget(filepath_label)
        filepath_container.addWidget(self.filepath_input)

        filename_container.addWidget(filename_label)
        filename_container.addWidget(self.filename_input)
        filename_container.addWidget(self.version_btn)

        filetype_container.addWidget(filetype_label)
        filetype_container.addWidget(self.format_combo)
        filetype_container.addWidget(self.usd_format_combo)

        comment_container.addWidget(comment_label)
        comment_container.addWidget(self.plain_text_edit)

        preview_h_container.addWidget(self.preview_label)
        preview_container.addLayout(preview_h_container)
        preview_container.addWidget(self.preview_frame)

        button_container.addWidget(cancel_btn)
        button_container.addWidget(publish_btn)

        layout.addLayout(filepath_container)
        layout.addLayout(filename_container)
        layout.addLayout(filetype_container)
        layout.addLayout(comment_container)
        layout.addLayout(preview_container)
        layout.addLayout(button_container)
        central_widget.setLayout(layout)

    def version_name(self):
        file_name = self.filename_input.text()
        version_match = re.search(r'v\d+', file_name)
        
        if version_match:
            return version_match.group()  # "v005" 반환
        else:
            return None

    def cleanup_video_player(self):
        """ 비디오 플레이어 종료 및 리소스 정리 """
        if hasattr(self, "preview_frame") and self.preview_frame:
            print("비디오 플레이어 종료 중...")

            if hasattr(self.preview_frame, "video_thread") and self.preview_frame.video_thread:
                print("비디오 스레드 종료 중...")
                self.preview_frame.video_thread.stop()
                self.preview_frame.video_thread.quit()
                self.preview_frame.video_thread.wait()
                print("백그라운드 비디오 스레드 종료 완료")

            if hasattr(self.preview_frame, "video_thread") and self.preview_frame.video_thread.cap:
                print("OpenCV 비디오 파일 닫기...")
                self.preview_frame.video_thread.cap.release()
                print("OpenCV 비디오 파일 닫힘")

            self.preview_frame.setParent(None)
            self.preview_frame.deleteLater()
            self.preview_frame = None
            print("비디오 플레이어 객체 제거 완료")

    def convert_to_save_path(file_path):
        """새로 저장할 경로"""
        directory_path = os.path.dirname(file_path)
        path_parts = directory_path.strip("/").split("/")

        if "work" in path_parts:
            work_index = path_parts.index("work")
            path_parts[work_index] = "pub"

        new_path = "/" + "/".join(path_parts)
        return new_path

    def close_event(self, event=None):
        """ UI 창이 닫힐 때 비디오 플레이어 종료 및 정리 """
        # 비디오 플레이어 종료 함수 호출
        self.cleanup_video_player()
        print("퍼블리셔 UI 종료 요청됨")
        # UI 닫기 실행
        if event:
            event.accept()  # X 버튼을 눌렀을 때 호출되는 경우
        else:
            self.close()  # "Cancel" 버튼을 눌렀을 때 호출되는 경우

    def publish_final_output(self):
        """ 
        1. 파일 저장 (save_file_as)
        2. 슬레이트 mov 2개 저장 (save_playblast_files)
        3. 비디오 플레이어 종료
        4. 원본 Playblast 삭제
        5. UI 닫기
        """
        version = self.version_name()
        print(f"publish 버튼 눌렷음! {version}")

        publish(self, self.work_path, self.pub_path, self.project_name, self.entity_parent, self.entity_name, self.dept)
        print ("저장 완료!")

        # 슬레이트 mov 3개 저장
        PlayblastManager(self.file_path, self.file_name).save_playblast_files(version)

        # 비디오 플레이어 종료 (중복 코드 제거하고 함수 호출)
        self.cleanup_video_player()

        # # 원본 Playblast .mov 삭제
        playblast_path = f"{self.filepath_input.text()}/playblast.mov"

        if os.path.exists(playblast_path):
            try:
                os.remove(playblast_path)
                print(f"원본 Playblast 파일 삭제 완료: {playblast_path}")
            except PermissionError:
                print("파일이 아직 사용 중이라 삭제할 수 없습니다.")
                return
        else:
            print("원본 Playblast 파일이 이미 삭제되었거나 존재하지 않습니다.")
        # UI 닫기
        self.close_event()
        print("퍼블리셔 UI 종료")

        clicked_task = self.ct
        publish_manager = PublishManager(clicked_task)
        
        file_name_text = self.filename_input.text().strip()
        local_path_text = self.filepath_input.text().strip()
        description_text = self.plain_text_edit.toPlainText().strip()
        usd_file_path = self.ct.set_shallow_path()
        usd_file_path = os.path.abspath(os.path.join(usd_file_path, "pub/usd"))
        usd_file_path = usd_file_path.split("/show")[-1]
        usd_file_path = f"/show{usd_file_path}"
        #mb_file_path = f"{local_path_text}/{file_name_text}"
        clean_name = re.sub(r"_v\d{3}$", "", file_name_text)
        usd_file_name = f"{clean_name}.usda"

        # print(f"line edit 에서 가져온 file name{file_name_text}")
        # print(f"line edit 에서 가져온 local path{local_path_text}")
        # print(f"line edit 에서 가져온 description{description_text}")
        print(f"usd 파일이 있는 경로 : {usd_file_path}")
        # print(f"mb file path : {mb_file_path}")
        print(f"usda 파일 이름 : {usd_file_name}")

        mov_name = f"{file_name_text}.mov"
        local_path = self.ct.set_deep_path("pub", "maya", "data")
        mov_path = os.path.abspath(os.path.join(local_path, mov_name))
        print(mov_path)

        jpg_name = f"{file_name_text}.jpg"
        jpg_path = os.path.abspath(os.path.join(local_path, jpg_name))
        print(jpg_path)

        publish_manager.set_file_path(usd_file_path)
        publish_manager.set_file_name(usd_file_name)
        publish_manager.set_description(description_text)
        publish_manager.set_thumbnail_path(jpg_path)
        publish_manager.set_mov_path(mov_path)
        # print(publish_manager)


        created_version = publish_manager.create_versions()
        published_file = publish_manager.create_published_file()
        publish_manager.link_version_to_published_file(published_file["id"], created_version["id"])
        # UI 닫기
        self.close_event()

        print("퍼블리셔 UI 종료")

    def center_window(self):
        screen_geometry = self.screen().geometry()  # 현재 창이 표시되는 화면의 전체 크기
        window_geometry = self.frameGeometry()  # 현재 창의 크기 정보

        # 화면 중앙 좌표 계산
        center_x = screen_geometry.width() // 2 - window_geometry.width() // 2
        center_y = screen_geometry.height() // 2 - window_geometry.height() // 2
        print(center_x, center_y)
        # 창 이동
        self.setGeometry(center_x, center_y, window_geometry.width(), window_geometry.height())        
        self.move(center_x, center_y)