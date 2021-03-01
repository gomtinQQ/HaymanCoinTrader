# MySQL Data Save
import configparser
import numpy as np
import pandas as pd
import pymysql
import random
import sys
import os

from datetime import datetime

# 코인 가격로그 저장
class CoinPriceLog():

    ## 초기화
    def __init__(self, broker_name, time_interval):

        ### 인풋 파라미터 설정
        self.broker_name = broker_name
        self.time_interval = time_interval
        
        ### import config file
        self.prev_path = os.path.dirname(os.path.dirname(__file__))
        self.config = configparser.ConfigParser()
        self.config.read(self.prev_path + '\config.cfg', encoding = 'utf-8')

        ### Read config about database
        self.db_ip = self.config.get('DATABASE', 'DB_IP')
        self.db_port = self.config.get('DATABASE', 'DB_PORT')
        self.db_id = self.config.get('DATABASE', 'DB_ID')
        self.db_pw = self.config.get('DATABASE', 'DB_PW')

        ### Database, table name 설정 (사용자 입력)
        self.db_name = 'coin_data'
        self.table_name = 'temp'
        
        ### 저장할 데이터베이스 호출(pymysql)
        self.db_conn = pymysql.connect(
            host = self.db_ip,
            user = self.db_id,
            password = self.db_pw,
            db = self.db_name,
            charset = 'utf8'
        )

    ## DB 생성
    def create_db(self):
        ### 구문작성
        sql_syntax = 'CREATE DATABASE %s' %self.db_name       
        
        ### 커밋후 저장, 종료
        cur = self.db_conn.cursor()
        cur.execute(sql_syntax)
        self.db_conn.commit()

    ##  가격데이터 저장 테이블 생성
    def create_price_table(self):
        # 구문 작성
        sql_syntax = """
            CREATE TABLE %s_%s
            ( Ticker varchar(16), Date int, Time int, Open float,
                High float, Low float, Close float, Volume float,
                quote_av float, trades int, tb_base_av float, tb_float_av float);
            """ %(self.broker_name, self.time_interval)

        ### 커밋후 저장, 종료
        cur = self.db_conn.cursor()
        cur.execute(sql_syntax)
        self.db_conn.commit()

    ## 가격데이터 - 업데이트 체크
    def search_last_update_data(self, ticker):
        sql_syntax = """
            SELECT * FROM %s.%s_%s WHERE Ticker = '%s' order by Date DESC, Time DESC Limit 3
        """ %(self.db_name, self.broker_name, self.time_interval, ticker)

        ### 쿼리 실행 
        cur = self.db_conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql_syntax)
        
        result = pd.DataFrame(cur.fetchall())

        return result

    ## 데이터 입력
    def insert_bulk_record(self, record):
        
        ### 입력할 데이터 입력
        record_data_list = str(tuple(record.apply(lambda x: tuple(x.tolist()), axis=1)))[1:-1]
        
        ### 맨끝 반점 삭제
        if record_data_list[-1] == ',':
            record_data_list = record_data_list[:-1]

        ### 구문생성
        sql_syntax = 'INSERT INTO %s.%s_%s values %s' %(
            self.db_name, self.broker_name, self.time_interval, record_data_list
        )

        ### 커밋후 저장, 종료
        cur = self.db_conn.cursor()
        cur.execute(sql_syntax)
        self.db_conn.commit()

        return True

    ## 총 데이터 입력
    def save(self, data):
        
        ### 테이블 미존재 시 테이블 생성
        print("[INFO] Target Input Data length is %s." %len(data.index))
    
        try:
            self.create_price_table()

        except:
            pass
        
        ### 1000행 넘어갈 경우 1000행씩 나눠서 인서트
        if len(data.index) > 1000:
            slice_unit = int(len(data.index)/1000)
            start = 0
            
            ### 0-999, 1000-1999, *** 순으로 입력
            for x in range(slice_unit):
                end = start + 999
                
                # 끝이 넘어가면 끝을 데이터 행갯수로 설정
                if end > len(data.index):
                    end = len(data.index)

                self.insert_bulk_record(data.iloc[start:end])
                start = end + 1

        ### 1000개 미만이면 그냥 삽입함
        else:
            self.insert_bulk_record(data)

        return True

# 코인 가격로그 검색
class SearchPriceLog():

    ## 초기화
    def __init__(self, broker_name, time_interval):

        ### 인풋 파라미터 설정
        self.broker_name = broker_name
        self.time_interval = time_interval
        
        ### import config file
        self.prev_path = os.path.dirname(os.path.dirname(__file__))
        self.config = configparser.ConfigParser()
        self.config.read(self.prev_path + '\config.cfg', encoding = 'utf-8')

        ### Read config about database
        self.db_ip = self.config.get('DATABASE', 'DB_IP')
        self.db_port = self.config.get('DATABASE', 'DB_PORT')
        self.db_id = self.config.get('DATABASE', 'DB_ID')
        self.db_pw = self.config.get('DATABASE', 'DB_PW')

        ### Database, table name 설정 (사용자 입력)
        self.db_name = 'coin_data'
        self.table_name = '%s_%s' %(self.broker_name, self.time_interval)
        
        ### 저장할 데이터베이스 호출(pymysql)
        self.db_conn = pymysql.connect(
            host = self.db_ip,
            user = self.db_id,
            password = self.db_pw,
            db = self.db_name,
            charset = 'utf8'
        )

    ## 가격 데이터 검색
    def price_data(self, ticker):
        sql_syntax = """
            SELECT * FROM %s.%s_%s WHERE Ticker = '%s' order by Date DESC, Time DESC
        """ %(self.db_name, self.broker_name, self.time_interval, ticker)

        ### 쿼리 실행 
        cur = self.db_conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql_syntax)
        
        result = pd.DataFrame(cur.fetchall())

        return result
    
# 백테스트 결과 DB 컨트롤
class BackTestResult():
    
    ## 초기화
    def __init__(self, strategy_name):
        
        ### import input parameter
        self.strategy_name = strategy_name
        
        ### 백테스트 결과 저장
        now = datetime.now()

        ### import config file
        self.prev_path = os.path.dirname(os.path.dirname(__file__))
        self.config = configparser.ConfigParser()
        self.config.read(self.prev_path + '\config.cfg', encoding = 'utf-8')

        ### Read config about database
        self.db_ip = self.config.get('DATABASE', 'DB_IP')
        self.db_port = self.config.get('DATABASE', 'DB_PORT')
        self.db_id = self.config.get('DATABASE', 'DB_ID')
        self.db_pw = self.config.get('DATABASE', 'DB_PW')

        ### Database, table name 설정 (사용자 입력)
        self.db_name = 'coin_backtest'
        self.table_name = 'temp'
        
        ### 저장할 데이터베이스 호출(pymysql)
        self.db_conn = pymysql.connect(
            host = self.db_ip,
            user = self.db_id,
            password = self.db_pw,
            db = self.db_name,
            charset = 'utf8'
        )

    ## DB 생성
    def create_db(self):
        ### 구문작성
        sql_syntax = 'CREATE DATABASE %s' %self.db_name       
        
        ### 커밋후 저장, 종료
        cur = self.db_conn.cursor()
        cur.execute(sql_syntax)
        self.db_conn.commit()
        
    ## 전체 백테스트 결과 저장용
    ## name, date, result, cagr, mdd, p/f ratio
    def create_backtest_result_table(self):
        
        ### 구문 작성
        sql_syntax = """
            CREATE TABLE backtest_result
            (
                date int, time int, strategy varchar(255), start_amount float,
                end_amount float, total_trade_year int, total_profit float, mdd float
            );
            """

        ### 커밋후 저장, 종료
        cur = self.db_conn.cursor()
        cur.execute(sql_syntax)
        self.db_conn.commit()

    ### 백테스트 히스토리 결과 저장용
    ### Date, time, position, balance, profit_percent, mdd
    def create_history_result_table(self, date, time):

        ### 구문 작성
        sql_syntax = """
            CREATE TABLE history_%s_%s_%s
            (
                date int, time int, open float, high float,
                low float, close float, volume float, position varchar(16),
                profit float
            );
            """ %(self.strategy_name, date, time)

        ### 커밋후 저장, 종료
        cur = self.db_conn.cursor()
        cur.execute(sql_syntax)
        self.db_conn.commit()
    
    ## 백테스트 결과 요약 데이터 입력
    def insert_describe_data(self, record):
        ### 구문생성
        sql_syntax = 'INSERT INTO %s.backtest_result values %s' %(
            self.db_name, tuple(record)
        )

        ### 커밋후 저장, 종료
        cur = self.db_conn.cursor()
        cur.execute(sql_syntax)
        self.db_conn.commit()
        
    ## 데이터 입력
    def insert_bulk_record(self, record, date, time):
        
        ### 입력할 데이터 입력
        record_data_list = str(tuple(record.apply(lambda x: tuple(x.tolist()), axis=1)))[1:-1]
        
        ### 맨끝 반점 삭제
        if record_data_list[-1] == ',':
            record_data_list = record_data_list[:-1]

        ### 구문생성
        sql_syntax = 'INSERT INTO %s.history_%s_%s_%s values %s' %(
            self.db_name, self.strategy_name, date, time, record_data_list
        )

        ### 커밋후 저장, 종료
        cur = self.db_conn.cursor()
        cur.execute(sql_syntax)
        self.db_conn.commit()

        return True

    ## 저장 루틴
    def save(self, data, mode, date, time):
        
        if mode == 'history':
            try:
                self.create_history_result_table(date, time)

            except:
                pass
            
            ### 1000행 넘어갈 경우 1000행씩 나눠서 인서트
            if len(data.index) > 1000:
                slice_unit = int(len(data.index)/1000)
                start = 0
                
                ### 0-999, 1000-1999, *** 순으로 입력
                for x in range(slice_unit):
                    end = start + 999
                    
                    # 끝이 넘어가면 끝을 데이터 행갯수로 설정
                    if end > len(data.index):
                        end = len(data.index)

                    self.insert_bulk_record(data.iloc[start:end], date, time)
                    start = end + 1

            ### 1000개 미만이면 그냥 삽입함
            else:
                self.insert_bulk_record(data, date, time)

        elif mode == 'describe':
            try:
                self.create_backtest_result_table()

            except:
                pass

            self.insert_describe_data(data)

        ### 모드 파라미터를 잘못 넣었을 경우
        else:
            raise ValueError

        return True
