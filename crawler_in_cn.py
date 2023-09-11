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
2. 키워드데이터 추출: 추가로 키워드를 입력 후 검색버튼을 눌러주세요.\n \
미구현 - 3. 탑 키워드 확인: 가장 많이 언급된 단어 5개를 하단의 창에서 확인해주세요.")
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
        #start_datetime = start_datetime.addSecs(self.start_hour_edit.time().hour() * 3600 + self.start_minute_edit.time().minute() * 60)
        start_date = start_datetime.toString("yyyy-MM-dd HH:mm")

        end_datetime = self.end_date_edit.dateTime()
        #end_datetime = end_datetime.addSecs(self.end_hour_edit.time().hour() * 3600 + self.end_minute_edit.time().minute() * 60 + 59)
        end_date = end_datetime.toString("yyyy-MM-dd HH:mm")
        #print(start_datetime, end_datetime)
        
        self.search_button.setText("작업중")  # 버튼 텍스트 변경
        self.search_button.setEnabled(False)  # 버튼 비활성화

        # 진행 상황 표시 (초기 0% 진행)
        self.update_progress(0)

        # 검색할 페이지 및 게시물 데이터 세팅
        self.status_label.setText("검색할 페이지 계산중")
        search_page = self.get_search_page(start_date, end_date)

        # 검색할 게시물 돌면서 results에 세팅
        # 검색 키워드 입력 시 키워드 검색 데이터 추출
        keyword = self.keyword_input.text().strip()
        if keyword:
            keyword_data = self.find_keyword_contents(search_page, start_date, end_date, keyword)
            df = pd.DataFrame(keyword_data)        
            start_datetime_str = start_datetime.toString("yyyyMMddHHmm")
            end_datetime_str = end_datetime.toString("yyyyMMddHHmm")
            df.to_excel(f'keyword_data ({start_datetime_str}-{end_datetime_str}).xlsx', index=False)

        # 키워드 미 입력 시 일반 로우데이터 출력
        else:
            crawled_data = self.get_element_contents(search_page, start_date, end_date)

            df = pd.DataFrame(crawled_data)        
            start_datetime_str = start_datetime.toString("yyyyMMddHHmm")
            end_datetime_str = end_datetime.toString("yyyyMMddHHmm")
            df.to_excel(f'crawled_data ({start_datetime_str}-{end_datetime_str}).xlsx', index=False)

        self.status_label.setText(f"저장완료!")

        """# 5초 후에 "저장완료!" 메시지를 지움
        QTimer.singleShot(5000, self.show_results)"""
        
        self.search_button.setText("검색")  # 버튼 텍스트 변경
        self.search_button.setEnabled(True)  # 버튼 활성화

        # 결과를 표시하는 QLabel 업데이트
        top_keywords = self.get_top_keywords()  # 가장 많이 언급된 상위 5개 키워드를 가져오는 함수를 호출하도록 수정하세요.
        top_keywords_text = "상위 5개 키워드:\n" + "\n".join(top_keywords)
        self.result_label.setText(top_keywords_text)
        

    def show_results(self):
        """
        # "저장완료!" 메시지 지우기
        self.status_label.clear()
        """

        # 결과를 표시하는 QLabel 업데이트
        top_keywords = self.get_top_keywords()  # 가장 많이 언급된 상위 5개 키워드를 가져오는 함수를 호출하도록 수정하세요.
        top_keywords_text = "상위 5개 키워드:\n" + "\n".join(top_keywords)
        self.result_label.setText(top_keywords_text)
        

    def update_progress(self, value):
        self.progress_bar.setValue(int(value * 100))

    # 가장 많이 언급된 상위 5개 키워드를 가져오는 함수를 구현
    def get_top_keywords(self, title, content):
        # 여기에 적절한 로직을 추가하여 상위 5개 키워드를 가져오세요.
        # 이 함수는 결과 데이터를 분석하여 가장 많이 언급된 키워드를 찾는 로직을 포함해야 합니다.
        # 예를 들어 Counter 클래스를 사용하여 키워드 빈도를 계산할 수 있습니다.
        # 결과는 리스트 형태로 반환하세요.
        
        keywords_list = []
        # keywords_list = ['밸런스', 'pvp', '클래스', '직업', '건슬', '슬레', '슬레이어', '건슬링어', '소서', '캐릭터', '캐릭', '컨텐츠', '필드보스',\
        #                 '쿠크세이튼','퀘스트','접속','서버','장애', '피로도','보상','버그','','골드','도화가', ,'데헌','바드','카멘', \
        #                 '아이템', '보석','크리스탈','크리스털','먹통', '패스','남캐','여캐', '편린','카던', '어비스','군단장','무기', \
        #                 '아바타','탈것', '스탯','이벤트','레이드','던전','업데이트','가토','버프','버그']

        #word_list = ""
        #keyword_list = word_list.split()
        #colletions.Counter(keyword_list)
    
        #keywords_count = collections.Counter(keywords_list)
        
        
        for title_element in title:
            keyword_list.append(title_element.get_text().strip())

        for content_element in content:         
            keyword_list.append(content_element.get_text().strip())

        # 제목과 내용을 하나의 텍스트로 합치기
        combined_text = ' '.join(keyword_list)

        # 공백과 특수문자 제거하여 단어 리스트로 변환
        words = combined_text.lower().split()

        # 가장 많이 언급된 키워드 5개 추출
        most_common_keywords = Counter(words).most_common(5)

        # 결과 출력
        print("가장 많이 언급된 키워드 5개:")
        for keyword, count in most_common_keywords:
            print(f"{keyword}: {count}번 언급")
        
        return most_common_keywords  # ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]
        
    # 시작시간과 끝시간을 인자로 받아 검색할 페이지 데이터를 리턴
    # search_page = key:page_num, value:url_list
    def get_search_page(self, start_date_str, end_date_str):
        base_url = "https://tieba.baidu.com/f?kw=%E5%91%BD%E8%BF%90%E6%96%B9%E8%88%9F&ie=utf-8"
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")
        now_date = datetime.now()
        cur_page = 0
        page_interval = 50
        tmp_url = '' # 위와같은 상황에서 이전페이지부터 시작페이지로 할 경우 바로리스트에 추가해 줄 용도 임시변수
        tmp_url_list = []
        search_start_page = search_end_page = -1 # 페이지 검색 후 검색할 페이지 넘버가 정해지면 그때 page_num 을 넣어줌
        search_page_dic = {}
        is_all_find = False
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        # ca_cert_file = "path/to/ca_certificate.pem"  # 신뢰할 수 있는 CA 인증서 파일 경로

        # 1페이지 부터 돌면서 페이지의 첫번째 글의 날짜만 보고 검색해야 할 페이지인지 확인
        # 만약 2번째 페이지의 첫째글의 시간이 검색범위에 있는 시간일경우 cur_page - 1 해서 1페이지 부터가 검색범위임
        while (not is_all_find) :
            url = f"{base_url}&pn={cur_page}"
            
            response = requests.get(url, headers=headers, verify=False) # verify=ca_cert_file

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                print(soup)
                # 게시판의 게시물들을 접근하기 위한 변수
                posts = soup.find_all("ul", id_="thread_list") #class_="threadlist_bright j_threadlist_bright"

                # 게시물들의 각 링크를 돌아가며
                # ahref 값을 찾아 링크 안의 제목과 내용을 긁어온다
                for post in posts:
                    for li in post.find_all("li"): # 각 페이지의 게시물 접근 
                        print(li.text)
                        idx = 0
                        # 첫째 ul의 공지쪽은 건너뜀
                        if (li.has_attr("class") and len(li["class"]) > 0 and li["class"][0] == 'thread_top_list_folder'):
                            continue
                        else:
                            # 두번째부터의 li만 봄
                            link_element = li.find("a")
                            tmp_url == ''
                            each_url = ''
                            if link_element and link_element.has_attr("href"):
                                link = link_element["href"]
                                each_url = f"https://tieba.baidu.com{link}"

                            if idx == 0 :
                                element_date = li.find('span', class_='pull-right is_show_create_time')
                                
                                # 페이지 첫글의 시간을 가져옴 (하루 이내면 n시간전, 그외는 yyyy.mm.dd의 포맷임)
                                # --> 수정: (하루 이내면 HH:MM 포맷, 그 외는 MM-DD 포맷)
                                
                                element_date_str = element_date[0].contents[0]

                                # 시작날짜~끝날짜의 기준에 맞으면 search_page_dic에 추가해준다
                                # --> 수정: HH:MM 포맷이면 당일 동향이므로 search_page_dic에 추가해준다
                                if self.is_valid_date_format(element_date_str, start_date, end_date, now_date):
                                    if search_start_page == -1:
                                        # 현재 검색중인페이지가 2페이지 이상이고 시작 페이지가 세팅이 안되어있으면 이전 페이지가 시작페이지임
                                        if cur_page > 0 :
                                            search_start_page = cur_page - page_interval
                                            pre_page_url_list = tmp_url_list[-page_interval:]
                                            tmp_url_list.clear()
                                            search_page_dic[search_start_page] = pre_page_url_list
                                            if search_page_dic.get(cur_page) is None:
                                                search_page_dic[cur_page] = []
                                            search_page_dic[cur_page].append(each_url)
                                        # 걍 첫페이지임
                                        else :                                        
                                            search_start_page = cur_page
                                            if search_page_dic.get(cur_page) is None:
                                                search_page_dic[cur_page] = []
                                            search_page_dic[cur_page].append(each_url)
                                    else :
                                        if search_page_dic.get(cur_page) is None:
                                            search_page_dic[cur_page] = []
                                        search_page_dic[cur_page].append(each_url)

                                    search_end_page = cur_page
                                else:
                                    # 날짜가 넘어간 페이지이면 마지막 페이지
                                    # 검색할 페이지와 url정보를 이제 다 들고 있으니 bool 체크하고 while 아웃
                                    if search_end_page != -1:
                                        if search_page_dic.get(cur_page) is None:
                                            search_page_dic[cur_page] = []
                                        search_page_dic[cur_page].append(each_url)
                                        is_all_find = True
                            
                            # 첫페이지를 못찾은 상태면 tmp_url_list 에 캐싱
                            if search_start_page == -1:
                                tmp_url_list.append(each_url)
                            elif idx != 0 :
                                search_page_dic[cur_page].append(each_url)

                        idx += 1
            cur_page += page_interval
        return search_page_dic   

    # 검색할 url 목록을 돌면서 content 를 result에 담아서 리턴
    def get_element_contents(self, search_page, start_date_str, end_date_str) :
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M") # 수정
        results = []
        total_size = 0        
        for page in search_page :
            for url in search_page.get(page) :
                total_size += 1

        idx = 1
        for page in search_page :
            for url in search_page.get(page) :
                self.update_progress(idx/total_size)
                self.status_label.setText(f"게시물 가져오는중... ( {idx} / {total_size} )")

                each_response = requests.get(url)
                each_soup = BeautifulSoup(each_response.content, "html.parser")
                
                # 등록일 찾기
                to_find_date = each_soup.find_all("ul", class_="p_tail")

                for li in to_find_date.find("span", class_=""):
                    if (li.has_attr("class") and len(li["class"]) > 0 and li["class"][0] == 'thread_top_list_folder'):
                        break
                    # 두번째 li만 봄
                    else:
                        date_element = li.find("span")
                
                if date_element:
                    date_str = date_element.text.strip()

                    uploaded_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")

                    # 게시물의 등록일이 기준에 맞으면: 
                    if start_date <= uploaded_date <= end_date:
                        
                        # 제목과 내용을 각각 변수에 저장
                        title = each_soup.find("a", class_="j_th_tit")
                        contents = each_soup.find("div", class_='fr-view')
                        content_element = contents.find_all("p")

                        # 탑 키워드 함수 호출
                        # keyword_result = get_top_keywords(self, title, content_element)
                        
                        # 제목을 스트링으로 변환
                        title_to_string = title.string                    

                        # 내용을 스트링으로 변환
                        content_to_string = ''
                        
                        for i in content_element:
                            if (i.string is not None):
                                i.string.replace(" © Smilegate RPG All rights reserved. ","")
                                content_to_string += i.string
                            content_to_string += '\n'
                            

                        # 예외처리                     
                        if (title_to_string is not None and content_to_string is not None):
                                    
                            ## 그 게시물의 제목이나 내용에 키워드가 있을 경우    
                            #if (keyword in title_to_string or keyword in content_to_string):
                                        
                            # 엑셀 파일에 들어갈 제목과 내용 값 저장        
                            results.append({'제목': title_to_string, '내용': content_to_string, '등록일' : date_str})

                        else:
                            continue                
                idx += 1
        return results

    # 키워드 입력 시 키워드가 있는 데이터 추출 함
    def find_keyword_contents(self, search_page, start_date_str, end_date_str, keyword):
        print("호출")
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")
        results = []
        total_size = 0        
        for page in search_page :
            for url in search_page.get(page) :
                total_size += 1

        idx = 1
        for page in search_page :
            for url in search_page.get(page) :
                self.update_progress(idx/total_size)
                self.status_label.setText(f"게시물 가져오는중... ( {idx} / {total_size} )")

                each_response = requests.get(url)
                each_soup = BeautifulSoup(each_response.content, "html.parser")

                # 등록일 찾기
                to_find_date = each_soup.find_all("ul", class_="p_tail")

                for li in to_find_date.find("span", class_=""):
                    if (li.has_attr("class") and len(li["class"]) > 0 and li["class"][0] == 'thread_top_list_folder'):
                        break
                    # 두번째 li만 봄
                    else:
                        date_element = li.find("span")
                
                if date_element:
                    date_str = date_element.text.strip()

                    uploaded_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")

                    # 게시물의 등록일이 기준에 맞으면: 
                    if start_date <= uploaded_date <= end_date:
                        # 제목과 내용을 각각 변수에 저장
                        title = each_soup.find("a", class_="j_th_tit")
                        
                        # 제목을 스트링으로 변환
                        title_to_string = title.string

                        # 게시물의 제목에 키워드가 있을 경우, 내용을 저장    
                        if (keyword in title_to_string):
                            contents = each_soup.find("div", class_='fr-view')
                            content_element = contents.find_all("p")          

                            # 내용을 스트링으로 변환
                            content_to_string = ''
                            
                            for i in content_element:
                                if (i.string is not None):
                                    i.string.replace(" © Smilegate RPG All rights reserved. ","")
                                    content_to_string += i.string
                                content_to_string += '\n'

                            # 예외처리                     
                            if (title_to_string is not None and content_to_string is not None):
                                            
                                    # 엑셀 파일에 들어갈 제목과 내용 값 저장        
                                    results.append({'제목': title_to_string, '내용': content_to_string, '등록일' : date_str})

                            else:
                                continue
                            
                        # 게시물의 제목에 키워드가 없을 경우,
                        elif (keyword not in title_to_string):
                            contents = each_soup.find("div", class_='fr-view')
                            content_element = contents.find_all("p")          

                            # 내용을 스트링으로 변환
                            content_to_string = ''
                            
                            for i in content_element:
                                if (i.string is not None):
                                    i.string.replace(" © Smilegate RPG All rights reserved. ","")
                                    content_to_string += i.string
                                content_to_string += '\n'
                            
                            # 내용에 키워드가 있을 경우
                            if (keyword in content_to_string):
                                
                                # 예외처리                     
                                if (title_to_string is not None and content_to_string is not None):
                                            
                                    # 엑셀 파일에 들어갈 제목과 내용 값 저장        
                                    results.append({'제목': title_to_string, '내용': content_to_string, '등록일' : date_str})

                                else:
                                    continue      
                idx += 1
        return results
                   

    # 시작시간과 끝시간 사이에 있는 시간인지 리턴
    def is_valid_date_format(self, date_string, start_date, end_date, now_date):
        date_pattern = r'(\d{4})-(\d{2})-(\d{2})'  # yyyy-mm-dd 형식의 정규 표현식   

        if re.match(date_pattern, date_string):
            date = datetime.strptime(date_string, "%Y-%m-%d")
            if start_date <= date <= end_date:
                return True
            else:
                return False
        # 끝나는날짜가 오늘이고 xxx 전 이면 True
        # 수정 --> HH:MM 형태일 경우, True
        elif end_date.day >= now_date.day and ":" in date_string:
            return True
        else:
            return False
        

if __name__ == "__main__":
    disable_warnings(InsecureRequestWarning)
    app = QApplication(sys.argv)
    search_app = SearchApp()
    search_app.show()
    sys.exit(app.exec_())
