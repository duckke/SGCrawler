import sys
import re
import requests
from datetime import datetime, time, timedelta
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QDateTimeEdit, QPushButton, QGridLayout, QTimeEdit, QProgressBar, QLineEdit, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer  # QTimer 모듈 추가
from urllib3.exceptions import InsecureRequestWarning # to disable warnings
from urllib3 import disable_warnings 

class SearchApp(QMainWindow):
    
    now_date = None
    date_pattern = r'([1-9]|10|11|12)-([1-9]|[12][0-9]|3[01])' # M-D 의 패턴
    time_pattern = r'([01]\d|2[0-3]):([0-5]\d)' # hh-mm 의 패턴

    def __init__(self):
        super().__init__()
        self.setWindowTitle("동향 크롤링 툴 - 중국어 버전 (v2.0)")
        self.setGeometry(300, 300, 600, 400)  # 창의 너비와 높이를 조정
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        grid_layout = QGridLayout()
        layout.addLayout(grid_layout)

        # 검색 시작일 선택
        self.start_date_label = QLabel("검색 시작일:")
        self.start_date_label.setFixedWidth(80)  # 라벨 너비 조정
        grid_layout.addWidget(self.start_date_label, 0, 0)

        # 검색 시작일은 기본값으로 오늘 날짜로 설정
        today = datetime.today()
        self.start_date_edit = QDateTimeEdit(self)
        self.start_date_edit.setDateTime(today)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setCalendarPopup(True)  # 달력 표시
        grid_layout.addWidget(self.start_date_edit, 0, 1)

        # 시간 선택 (시) - 검색 시작일
        self.start_hour_edit = QTimeEdit(self)
        self.start_hour_edit.setDisplayFormat("HH")
        self.start_hour_edit.setFixedWidth(50)  # 너비 조정
        grid_layout.addWidget(self.start_hour_edit, 0, 2)

        # 시 라벨 - 검색 시작일
        self.start_hour_label = QLabel("시")
        self.start_hour_label.setFixedWidth(20)  # 라벨 너비 조정
        grid_layout.addWidget(self.start_hour_label, 0, 3)

        # 시간 선택 (분) - 검색 시작일
        self.start_minute_edit = QTimeEdit(self)
        self.start_minute_edit.setDisplayFormat("mm")
        self.start_minute_edit.setFixedWidth(50)  # 너비 조정
        grid_layout.addWidget(self.start_minute_edit, 0, 4)

        # 분 라벨 - 검색 시작일
        self.start_minute_label = QLabel("분")
        self.start_minute_label.setFixedWidth(20)  # 라벨 너비 조정
        grid_layout.addWidget(self.start_minute_label, 0, 5)

        # 검색 종료일 선택
        self.end_date_label = QLabel("검색 종료일:")
        self.end_date_label.setFixedWidth(80)  # 라벨 너비 조정
        grid_layout.addWidget(self.end_date_label, 1, 0)

        # 검색 종료일은 기본값으로 내일 날짜로 설정
        self.end_date_edit = QDateTimeEdit(self)
        self.end_date_edit.setDateTime(today)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setCalendarPopup(True)  # 달력 표시
        grid_layout.addWidget(self.end_date_edit, 1, 1)

        # 시간 선택 (시) - 검색 종료일
        self.end_hour_edit = QTimeEdit(self)
        self.end_hour_edit.setDisplayFormat("HH")
        self.end_hour_edit.setTime(time(23, 0))  # 시간 기본값 설정
        self.end_hour_edit.setFixedWidth(50)  # 너비 조정
        grid_layout.addWidget(self.end_hour_edit, 1, 2)

        # 시 라벨 - 검색 종료일
        self.end_hour_label = QLabel("시")
        self.end_hour_label.setFixedWidth(20)  # 라벨 너비 조정
        grid_layout.addWidget(self.end_hour_label, 1, 3)

        # 시간 선택 (분) - 검색 종료일
        self.end_minute_edit = QTimeEdit(self)
        self.end_minute_edit.setDisplayFormat("mm")
        self.end_minute_edit.setTime(time(0, 59))  # 분 기본값 설정
        self.end_minute_edit.setFixedWidth(50)  # 너비 조정
        grid_layout.addWidget(self.end_minute_edit, 1, 4)

        # 분 라벨 - 검색 종료일
        self.end_minute_label = QLabel("분")
        self.end_minute_label.setFixedWidth(20)  # 라벨 너비 조정
        grid_layout.addWidget(self.end_minute_label, 1, 5)

        # 검색 키워드 입력란 추가
        self.keyword_label = QLabel("검색 키워드:")
        self.keyword_label.setFixedWidth(80)
        grid_layout.addWidget(self.keyword_label, 2, 0)

        self.keyword_input = QLineEdit(self)
        grid_layout.addWidget(self.keyword_input, 2, 1)

        # 사이트 선택 드롭다운 메뉴 추가
        self.site_label = QLabel("사이트 선택:")
        self.site_label.setFixedWidth(80)
        grid_layout.addWidget(self.site_label, 3, 0)

        self.site_dropdown = QComboBox(self)
        self.site_dropdown.addItem("https://tieba.baidu.com/")  # 원하는 사이트 이름으로 변경
        self.site_dropdown.addItem("사이트 2")  # 원하는 사이트 이름으로 변경
        grid_layout.addWidget(self.site_dropdown, 3, 1)

        # 진행 상황 표시를 위한 Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # 작업 중인 내용을 표시할 QLabel
        self.status_label = QLabel(self)
        self.status_label.setStyleSheet("background-color: transparent;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(40)  # 최소 높이 설정        
        self.status_label.setText("1. 로우데이터 추출: 검색을 원하는 시간을 설정 후 검색버튼을 눌러주세요.\n \
2. 키워드데이터 추출: 추가로 키워드를 입력 후 검색버튼을 눌러주세요.")
        layout.addWidget(self.status_label)

        # 탑 키워드 결과를 표시할 QLabel 추가
        self.result_label = QLabel(self)
        self.result_label.setStyleSheet("background-color: white;"
                                        "border-style: solid;"
                                        "border-width: 1px;"
                                        "border-color: #FA8072;")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setMinimumHeight(40)
        layout.addWidget(self.result_label)

        # 검색 버튼
        self.search_button = QPushButton("검색", self)
        self.search_button.clicked.connect(self.search_clicked)
        self.search_button.setFixedHeight(40)  # 검색 버튼 높이 설정
        layout.addWidget(self.search_button)

    def search_clicked(self):
        start_datetime = self.start_date_edit.dateTime()
        start_datetime = start_datetime.addSecs(self.start_hour_edit.time().hour() * 3600 + self.start_minute_edit.time().minute() * 60)
        start_date = start_datetime.toString("yyyy-MM-dd HH:mm")

        end_datetime = self.end_date_edit.dateTime()
        end_datetime = end_datetime.addSecs(self.end_hour_edit.time().hour() * 3600 + self.end_minute_edit.time().minute() * 60 + 59)
        end_date = end_datetime.toString("yyyy-MM-dd HH:mm")
        #print(start_datetime, end_datetime)
        
        self.now_date = datetime.now()
        self.now_date = self.now_date.replace(second=0, microsecond=0)

        self.search_button.setText("작업중")  # 버튼 텍스트 변경
        self.search_button.setEnabled(False)  # 버튼 비활성화

        # 진행 상황 표시 (초기 0% 진행)
        self.update_progress(0)

        # 검색할 페이지 및 게시물 데이터 세팅
        self.status_label.setText("검색할 페이지 계산중")
        # search_url_list = self.get_search_url_list(start_date, end_date)        
        search_url_list = ['https://tieba.baidu.com/p/8589742214']


        # 찾을 url list가 있으면
        if (len(search_url_list) > 0):
            # 검색할 게시물 돌면서 results에 세팅
            # 검색 키워드 입력 시 키워드 검색 데이터 추출
            # 키워드 미 입력 시 일반 로우데이터 출력
            # 키워드는 A,B,C,D,... 식으로 ',' 콤마로 구분
            keywords = []
            if (self.keyword_input.text() is not None and self.keyword_input.text().strip() != ''):
                keywords = self.keyword_input.text().split(',')
            crawled_data = self.get_element_contents(search_url_list, start_date, end_date, keywords)
            df = pd.DataFrame(crawled_data)        
            start_datetime_str = start_datetime.toString("yyyyMMddHHmm")
            end_datetime_str = end_datetime.toString("yyyyMMddHHmm")
            df.to_excel(f'crawled_data ({start_datetime_str}-{end_datetime_str}).xlsx', index=False)
            self.status_label.setText(f"저장완료!")
        
        self.search_button.setText("검색")  # 버튼 텍스트 변경
        self.search_button.setEnabled(True)  # 버튼 활성화
        



    def update_progress(self, value):
        self.progress_bar.setValue(int(value * 100))



    # 시작시간과 끝시간을 인자로 받아 검색할 url list를 리턴
    # search_url_list = [url0, url1, url2, .....]
    def get_search_url_list(self, start_date_str, end_date_str):
        base_url = "https://tieba.baidu.com/f?kw=%E5%91%BD%E8%BF%90%E6%96%B9%E8%88%9F&ie=utf-8"
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")
        start_element_datetime = None
        search_url_list = set() # 순회할 url list(). set() : 중복되지않는 리스트 
        is_all_finded = False
        is_block = False # 캡챠 떳는지 여부
        cur_page = 0
        page_interval = 50

        # <=====================요부분은 필요없으면 지우세여
        #get 하는부분에서 일단 header뺴둠
        # headers = {
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.66 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        # }
        #
        # ca_cert_file = "path/to/ca_certificate.pem"  # 신뢰할 수 있는 CA 인증서 파일 경로


        # 1페이지 부터 돌면서 시작날짜의 이전날짜의 글을 발견할때까지 페이지를 열어본다
        while (not is_block and not is_all_finded) :
            url = f"{base_url}&pn={cur_page*page_interval}"            
            response = requests.get(url, verify=False) # verify=ca_cert_file
            if response.status_code == 200:
                if 'https://wappass.baidu.com/' in response.url:
                    self.status_label.setText(f"캡챠 뜸........ㅜㅜ")
                    print("캡챠 뜸........ㅜㅜ")
                    is_block = True
                    continue                          
                
                soup = BeautifulSoup(response.text, 'html.parser')
                # 게시판의 게시물들을 접근하기 위한 변수
                posts = soup.find_all('li', class_='j_thread_list clearfix thread_item_box')
                
                # 현재 페이지의 게시물들을 순회
                for post in posts:
                    each_url = ''                    
                    if post is not None and post.has_attr('data-tid'):
                        link = post['data-tid']

                        # 현재 게시물의 링크
                        each_url = f'https://tieba.baidu.com/p/{link}'

                        # 현재 게시물 시간을 가져옴 (하루 이내면 hh:mm, 그외는 M-D 의 포맷임)
                        element_date = post.find('span', class_='threadlist_reply_date pull_right j_reply_data')
                        element_date_str = element_date.contents[0].strip()

                        # 첫 게시물이면 게시물의 시간을 기억해둔다
                        if start_element_datetime is None:
                            start_element_datetime = self.get_datetime_by_string(element_date_str)

                        # 시작날짜~끝날짜의 기준에 맞는지 체크
                        if self.is_valid_date_format(element_date_str, start_date, end_date, start_element_datetime):
                            # 기준에 맞는 url 이 아니면 list 에 추가해준다
                            # 중복된 url은 패스
                            if each_url in search_url_list:
                                print('중복')
                            else:
                                search_url_list.add(each_url)
                        else:
                            is_all_finded = True

                cur_page += 1
        return search_url_list   


    # 검색할 url 목록을 돌면서 content 를 result에 담아서 리턴
    def get_element_contents(self, search_url_list, start_date_str, end_date_str, keywords) :
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M") # 수정
        results = []
        total_size = len(search_url_list)       
        idx = 0
        for url in search_url_list :
            idx += 1
            self.update_progress(idx/total_size)
            self.status_label.setText(f"게시물 가져오는중... ( {idx} / {total_size} )")

            each_response = requests.get(url)
            each_soup = BeautifulSoup(each_response.content, "html.parser")
            
            
            #
            #
            # 각 url을 읽으면서 제목,본문,등록일 을 가져온다
            #
            #

            # 제목
            title_to_string = each_soup.find('h1', class_='core_title_txt')

            # 내용
            content_to_string = each_soup.find('div', class_='d_post_content j_d_post_content clearfix')
            
            # 제목이나 본문에 내용없으면 pass
            if (title_to_string is None or content_to_string is None):
                continue

            title_to_string = title_to_string.text.strip()
            content_to_string = content_to_string.text.strip()

            # # 등록일
            date_str = None
            # date_str = each_soup.find('ul', class_='p_tail') # 안잡혀 ㅜ.ㅜ
            # date = self.now_date # date_str 을 datetime 으로 만들어줘야함. 임시로 현재시간
            
            # # 날짜 기준에 맞지 않으면 pass            
            # if start_date > date > end_date:
            #     continue

            # 조건에 부합하는 content인지?
            is_appendable = True

            # 키워드 검색목록이 있으면 해당 키워드가 제목이나 내용에 포함되어야한다          
            if (len(keywords) > 0):
                is_appendable = False # 키워드값이 포함되어 있으면 True로 해준다
                for keyword in keywords:
                    keyword = keyword.strip()
                    if (keyword is None or keyword == ''):
                        continue
                    if (keyword in title_to_string or keyword in content_to_string):
                        is_appendable = True
                        break
            
            # 조건에 부합하지 않기때문에 pass
            if (not is_appendable):
                continue
            
            # 엑셀 파일에 들어갈 제목과 내용 값 저장        
            results.append({'제목': title_to_string, '내용': content_to_string, '등록일' : date_str})

        return results


    # 시작시간과 끝시간 사이에 있는 시간인지 리턴
    def is_valid_date_format(self, date_string, start_date, end_date, first_element_date):
        date = self.get_datetime_by_string(date_string)

        # 검색을 시작한 첫번째 글의 date 이후의 글이고 (검색시작한 시간이후의 글을 발견했을때는 건너뛰도록 하기 위함)
        # 시작시간~끝시간 사이에 해당하는 값이면 true를 리턴
        first_element_date = first_element_date - timedelta(microseconds=first_element_date.microsecond)
        date = date - timedelta(microseconds=date.microsecond)
        if first_element_date >= date and start_date <= date <= end_date:
            return True
        else:
            return False


    # 날짜 or 시간의 string값으로 datetime을 return        
    def get_datetime_by_string(self, date_string):
        date = self.now_date

        # 날짜 패턴에 맞는 데이터는 해당날짜의 00:00 분으로 date에 넣어줌
        if re.match(self.date_pattern, date_string):
            date_obj = datetime.strptime(date_string, "%m-%d")
            date = datetime(date.year, date_obj.month, date_obj.day)
        # 시간 패턴에 맞는 데이터는 오늘날짜의 해당시간으로 date에 넣어줌
        elif re.match(self.time_pattern, date_string):            
            time_obj = datetime.strptime(date_string, "%H:%M")            
            date = datetime.combine(date.date(), time_obj.time())

        return date
            
        

if __name__ == "__main__":
    disable_warnings(InsecureRequestWarning)
    app = QApplication(sys.argv)
    search_app = SearchApp()
    search_app.show()
    sys.exit(app.exec_())
